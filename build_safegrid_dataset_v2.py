"""
SafeGrid — Dataset Builder v2
Team Code Coven | Infinity Hacks 2026

Changes from v1:
  1. risk_score / risk_band are ground truth ONLY -> shipped in a separate
     labels file, never inside the feature table.
  2. Added time_bucket (morning/afternoon/evening/night) -> long-format table,
     one row per (segment, time_bucket). Crowd density and how much lighting
     matters both vary by bucket.
  3. unsafe_reports_30d is no longer a single count column -> exploded into
     individual report rows with jittered lat/lon, a timestamp, and a
     simulated hashed device signature (with a small % of repeat devices
     across segments -> fuel for the predator-pattern stretch feature).
  4. Risk bands rebalanced via quantile cuts (30/35/35) instead of fixed
     0-33-66-100 cutoffs, which had buried "high" at ~9% of rows.
  5. Densified underrepresented zones (it_park, market_commercial,
     public_venue) with extra real anchors + finer local sub-grids so the
     model sees more than "residential_mixed" everywhere.

DATA PROVENANCE — unchanged from v1, see DATA_DICTIONARY.md for full detail.
Real: grid geography, anchor landmarks. Real (aggregate): NCRB/NCW calibration
constants. Simulated: lighting, crowd, incidents, reports — rule-based, no
bulk street-level public dataset exists for Bhubaneswar.

Outputs:
  safegrid_features.csv       <- TRAIN ON THIS (no risk_score/risk_band)
  safegrid_labels.csv         <- ground truth only, joins on segment_id+time_bucket
  safegrid_unsafe_reports.csv <- individual crowdsourced reports w/ device hashes
  safegrid_reference_full.csv <- convenience join of all three, for EDA only
"""

import numpy as np
import pandas as pd
import math
import hashlib
import datetime as dt

rng = np.random.default_rng(42)

# ---------------------------------------------------------------------------
# 1. GRID THE CITY (real Bhubaneswar bounding box) — base coarse grid
# ---------------------------------------------------------------------------
LAT_MIN, LAT_MAX = 20.220, 20.400
LON_MIN, LON_MAX = 85.740, 85.900
CELL_DEG = 0.0045  # ~500m

lat_steps = np.arange(LAT_MIN, LAT_MAX, CELL_DEG)
lon_steps = np.arange(LON_MIN, LON_MAX, CELL_DEG)

base_rows = []
for lat in lat_steps:
    for lon in lon_steps:
        base_rows.append({"lat_center": lat + CELL_DEG / 2, "lon_center": lon + CELL_DEG / 2})
base_grid = pd.DataFrame(base_rows)

# ---------------------------------------------------------------------------
# 2. REAL ANCHOR LANDMARKS — expanded roster, extra anchors added specifically
#    for previously-underrepresented zone types (it_park, market_commercial,
#    public_venue) so those categories get real, distinct locations instead
#    of just denser sampling around a single point.
# ---------------------------------------------------------------------------
ANCHORS = [
    ("Bhubaneswar Railway Station", 20.2679, 85.8398, "transit_hub"),
    ("Baramunda Bus Stand",         20.2955, 85.7929, "transit_hub"),
    ("Biju Patnaik Airport",        20.2530, 85.8180, "transit_hub"),

    ("Master Canteen Square",       20.2700, 85.8410, "market_commercial"),
    ("Rajmahal Square",             20.2700, 85.8330, "market_commercial"),
    ("Jaydev Vihar",                20.2960, 85.8180, "market_commercial"),
    ("Unit-1 Market Building",      20.2650, 85.8360, "market_commercial"),
    ("Unit-4 Market",               20.2760, 85.8420, "market_commercial"),
    ("Rasulgarh Market",            20.2960, 85.8560, "market_commercial"),
    ("Saheed Nagar Market",         20.2940, 85.8420, "market_commercial"),
    ("Bapuji Nagar Market",         20.2610, 85.8310, "market_commercial"),

    ("Patia / Infocity-1",          20.3520, 85.8200, "it_park"),
    ("Infocity-2, Patia",           20.3480, 85.8260, "it_park"),
    ("STPI Bhubaneswar",            20.3430, 85.8230, "it_park"),
    ("Chandaka Industrial Estate",  20.3600, 85.7950, "it_park"),

    ("Chandrasekharpur",            20.3450, 85.8100, "residential_dense"),
    ("Vani Vihar (Utkal Univ.)",    20.2950, 85.8390, "university_campus"),
    ("KIIT Campus, Patia",          20.3560, 85.8190, "university_campus"),

    ("Kalinga Stadium",             20.2870, 85.8250, "public_venue"),
    ("Esplanade Mall",              20.2990, 85.8420, "public_venue"),
    ("DN Regal / DN Mall area",     20.2690, 85.8440, "public_venue"),
    ("Regional Science Centre",     20.2920, 85.8330, "public_venue"),
    ("IG Park",                     20.2660, 85.8390, "public_venue"),

    ("Old Town / Lingaraj Temple",  20.2380, 85.8340, "heritage_dense"),
    ("Nandankanan Road (outskirts)",20.3940, 85.8180, "outskirts"),
    ("Khandagiri (outskirts)",      20.2610, 85.7780, "outskirts"),
]
anchors_df = pd.DataFrame(ANCHORS, columns=["name", "lat", "lon", "zone_type"])

def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))

def nearest_anchor(lat, lon):
    dists = anchors_df.apply(lambda r: haversine_km(lat, lon, r.lat, r.lon), axis=1)
    idx = dists.idxmin()
    return anchors_df.loc[idx, "zone_type"], anchors_df.loc[idx, "name"], dists[idx]

zone_types, nearest_names, dist_km = [], [], []
for _, r in base_grid.iterrows():
    zt, nm, d = nearest_anchor(r.lat_center, r.lon_center)
    if d > 2.2:
        zt, nm = "residential_mixed", "Unnamed residential/mixed segment"
    zone_types.append(zt); nearest_names.append(nm); dist_km.append(round(d, 3))

base_grid["zone_type"] = zone_types
base_grid["nearest_landmark"] = nearest_names
base_grid["dist_to_anchor_km"] = dist_km

# ---------------------------------------------------------------------------
# 2b. DENSE LOCAL SUB-GRIDS around it_park / market_commercial / public_venue
#     anchors -> directly tagged, no nearest-anchor fallback needed. This is
#     the fix for "model just learns residential_mixed".
# ---------------------------------------------------------------------------
def dense_subgrid(anchor_name, anchor_lat, anchor_lon, zone_type, radius_km=0.55, spacing_km=0.14):
    pts = []
    # degrees-per-km approx at this latitude
    dlat_per_km = 1 / 110.574
    dlon_per_km = 1 / (111.320 * math.cos(math.radians(anchor_lat)))
    steps = np.arange(-radius_km, radius_km + 1e-9, spacing_km)
    for dlat_km in steps:
        for dlon_km in steps:
            d = math.hypot(dlat_km, dlon_km)
            if d > radius_km:
                continue
            lat = anchor_lat + dlat_km * dlat_per_km
            lon = anchor_lon + dlon_km * dlon_per_km
            pts.append({
                "lat_center": lat, "lon_center": lon,
                "zone_type": zone_type, "nearest_landmark": anchor_name,
                "dist_to_anchor_km": round(d, 3),
            })
    return pd.DataFrame(pts)

DENSIFY_TYPES = {"it_park", "market_commercial", "public_venue"}
dense_frames = []
for _, a in anchors_df[anchors_df.zone_type.isin(DENSIFY_TYPES)].iterrows():
    dense_frames.append(dense_subgrid(a["name"], a.lat, a.lon, a.zone_type))
dense_grid = pd.concat(dense_frames, ignore_index=True)

df = pd.concat([base_grid, dense_grid], ignore_index=True)
df.insert(0, "segment_id", [f"BBS-{i+1:04d}" for i in range(len(df))])
df["lat_center"] = df["lat_center"].round(6)
df["lon_center"] = df["lon_center"].round(6)

CENTER = (20.2961, 85.8245)
df["dist_from_center_km"] = df.apply(
    lambda r: round(haversine_km(r.lat_center, r.lon_center, *CENTER), 3), axis=1
)

# ---------------------------------------------------------------------------
# 3. STATIC (non-time-varying) SEGMENT ATTRIBUTES: lighting, historical incidents
# ---------------------------------------------------------------------------
ZONE_PROFILE = {
    # lighting_base, incident_weight
    "transit_hub":        (0.75, 1.35),
    "market_commercial":  (0.70, 1.20),
    "it_park":            (0.80, 0.70),
    "residential_dense":  (0.55, 1.00),
    "university_campus":  (0.70, 0.85),
    "public_venue":       (0.75, 0.75),
    "heritage_dense":     (0.45, 1.10),
    "outskirts":          (0.25, 1.15),
    "residential_mixed":  (0.45, 1.00),
}

def sim_static(r):
    lighting_b, inc_w = ZONE_PROFILE[r.zone_type]
    decay = max(0.0, 1 - r.dist_to_anchor_km / 3.0)
    lighting = np.clip(lighting_b * (0.6 + 0.4 * decay) + rng.normal(0, 0.06), 0.03, 0.98)
    streetlight_pct = np.clip(lighting * 100 + rng.normal(0, 4), 5, 100)
    # baseline night crowd proxy just for incident simulation (not exported directly)
    night_crowd_proxy = ZONE_PROFILE[r.zone_type][0] * 0.4
    incident_lambda = inc_w * (1.6 * (1 - lighting) + 1.1 * (1 - night_crowd_proxy))
    historical_incidents = rng.poisson(max(incident_lambda, 0.05))
    return pd.Series({
        "lighting_score": round(lighting, 3),
        "streetlight_operational_pct": round(streetlight_pct, 1),
        "historical_incidents_annual": int(historical_incidents),
    })

df = pd.concat([df, df.apply(sim_static, axis=1)], axis=1)

# ---------------------------------------------------------------------------
# 4. TIME-VARYING LAYER: explode each segment into 4 time_buckets with its
#    own crowd_density, then compute per-bucket unsafe report counts from the
#    individual reports table generated below.
# ---------------------------------------------------------------------------
TIME_BUCKETS = ["morning", "afternoon", "evening", "night"]  # 05-11 / 11-17 / 17-21 / 21-05
LIGHTING_RELEVANCE = {"morning": 0.10, "afternoon": 0.05, "evening": 0.60, "night": 1.00}

# crowd_density_base[zone_type][time_bucket]
CROWD_BASE = {
    "transit_hub":       {"morning": 0.85, "afternoon": 0.50, "evening": 0.90, "night": 0.30},
    "market_commercial": {"morning": 0.40, "afternoon": 0.70, "evening": 0.85, "night": 0.15},
    "it_park":           {"morning": 0.50, "afternoon": 0.80, "evening": 0.40, "night": 0.05},
    "residential_dense": {"morning": 0.50, "afternoon": 0.35, "evening": 0.60, "night": 0.25},
    "university_campus": {"morning": 0.60, "afternoon": 0.75, "evening": 0.45, "night": 0.15},
    "public_venue":      {"morning": 0.20, "afternoon": 0.35, "evening": 0.70, "night": 0.20},
    "heritage_dense":    {"morning": 0.50, "afternoon": 0.45, "evening": 0.55, "night": 0.15},
    "outskirts":         {"morning": 0.15, "afternoon": 0.15, "evening": 0.12, "night": 0.04},
    "residential_mixed": {"morning": 0.35, "afternoon": 0.30, "evening": 0.45, "night": 0.15},
}

long_rows = []
for _, r in df.iterrows():
    for tb in TIME_BUCKETS:
        base = CROWD_BASE[r.zone_type][tb]
        decay = max(0.0, 1 - r.dist_to_anchor_km / 3.0)
        crowd = np.clip(base * (0.7 + 0.3 * decay) + rng.normal(0, 0.06), 0.01, 0.98)
        long_rows.append({
            "segment_id": r.segment_id, "time_bucket": tb,
            "crowd_density": round(crowd, 3),
        })
crowd_long = pd.DataFrame(long_rows)

features = crowd_long.merge(
    df[["segment_id", "lat_center", "lon_center", "zone_type", "nearest_landmark",
        "dist_to_anchor_km", "dist_from_center_km", "lighting_score",
        "streetlight_operational_pct", "historical_incidents_annual"]],
    on="segment_id", how="left",
)

# ---------------------------------------------------------------------------
# 5. INDIVIDUAL UNSAFE REPORTS (lat, lon, timestamp, device_hash_sim)
#    -> replaces the old flat unsafe_reports_30d count column.
#    A small pool of "repeat devices" is seeded across multiple segments/times
#    to simulate stalking proximity patterns for the predator-pattern stretch.
# ---------------------------------------------------------------------------
NOW = dt.datetime(2026, 8, 15, 12, 0, 0)
WINDOW_DAYS = 30

def time_bucket_from_hour(h):
    if 5 <= h < 11: return "morning"
    if 11 <= h < 17: return "afternoon"
    if 17 <= h < 21: return "evening"
    return "night"

def sim_hash(seed_str):
    return "dev_" + hashlib.sha1(seed_str.encode()).hexdigest()[:10]

# seed a small set of "repeat" anonymized device signatures (predator-pattern demo)
N_REPEAT_DEVICES = 22
repeat_device_hashes = [sim_hash(f"repeat-{i}-{rng.integers(0,1_000_000)}") for i in range(N_REPEAT_DEVICES)]

report_rows = []
report_id = 0

for _, r in df.iterrows():
    lighting_b, inc_w = ZONE_PROFILE[r.zone_type]
    night_crowd_proxy = lighting_b * 0.4
    report_lambda = 0.33 * (0.5 * r.historical_incidents_annual + 1.4 * (1 - r.lighting_score) + 0.6 * (1 - night_crowd_proxy))
    n_reports = rng.poisson(max(report_lambda, 0.02))
    for _ in range(n_reports):
        report_id += 1
        # timestamp uniform across the 30-day window, weighted slightly toward
        # evening/night for low-lighting segments (harassment skews after dark)
        night_bias = 1 - r.lighting_score
        hour_weights = np.array([
            1.0,  # morning share baseline
            1.0,  # afternoon
            1.0 + night_bias,   # evening
            0.6 + 1.4 * night_bias,  # night
        ])
        hour_weights = hour_weights / hour_weights.sum()
        bucket_choice = rng.choice(TIME_BUCKETS, p=hour_weights)
        bucket_hour_ranges = {"morning": (5, 11), "afternoon": (11, 17), "evening": (17, 21), "night": (21, 29)}
        lo, hi = bucket_hour_ranges[bucket_choice]
        hour = int(rng.integers(lo, hi)) % 24
        minute = int(rng.integers(0, 60))
        days_ago = rng.integers(0, WINDOW_DAYS)
        ts = (NOW - dt.timedelta(days=int(days_ago))).replace(hour=hour, minute=minute, second=0, microsecond=0)

        # jitter lat/lon within ~60m of segment center
        jlat = r.lat_center + rng.normal(0, 0.0004)
        jlon = r.lon_center + rng.normal(0, 0.0004)

        # device hash: 55% no device signature captured (opt-out / no BLE ping),
        # 40% one-off device, 5% drawn from the repeat-device pool
        roll = rng.random()
        if roll < 0.55:
            device_hash = None
        elif roll < 0.95:
            device_hash = sim_hash(f"oneoff-{report_id}-{rng.integers(0,10_000_000)}")
        else:
            device_hash = repeat_device_hashes[int(rng.integers(0, N_REPEAT_DEVICES))]

        report_rows.append({
            "report_id": f"RPT-{report_id:05d}",
            "segment_id": r.segment_id,
            "lat": round(jlat, 6),
            "lon": round(jlon, 6),
            "timestamp": ts.isoformat(sep=" "),
            "time_bucket": time_bucket_from_hour(hour),
            "device_hash_sim": device_hash,
        })

reports_df = pd.DataFrame(report_rows)

# aggregate report counts per (segment_id, time_bucket) to feed back as a feature
report_counts = (
    reports_df.groupby(["segment_id", "time_bucket"]).size()
    .reset_index(name="unsafe_reports_count")
)
features = features.merge(report_counts, on=["segment_id", "time_bucket"], how="left")
features["unsafe_reports_count"] = features["unsafe_reports_count"].fillna(0).astype(int)

# ---------------------------------------------------------------------------
# 6. GROUND-TRUTH RISK SCORE (kept OUT of the features table)
# ---------------------------------------------------------------------------
def norm(s):
    return (s - s.min()) / (s.max() - s.min() + 1e-9)

lighting_risk = (1 - features["lighting_score"]) * features["time_bucket"].map(LIGHTING_RELEVANCE)
crowd_risk = 1 - features["crowd_density"]
incident_risk = norm(features["historical_incidents_annual"])
report_risk = norm(features["unsafe_reports_count"])

risk_raw = 0.30 * norm(lighting_risk) + 0.25 * crowd_risk + 0.25 * incident_risk + 0.20 * report_risk
risk_score = (norm(risk_raw) * 100).round(1)

# rebalanced, quantile-based bands: ~30% low / 35% medium / 35% high
q_low, q_high = risk_score.quantile([0.30, 0.65])
def band(x):
    if x >= q_high: return "high"
    if x >= q_low: return "medium"
    return "low"

labels = features[["segment_id", "time_bucket"]].copy()
labels["risk_score"] = risk_score
labels["risk_band"] = risk_score.apply(band)

# ---------------------------------------------------------------------------
# 7. EXPORT — features and labels kept strictly separate
# ---------------------------------------------------------------------------
feature_cols = [
    "segment_id", "time_bucket", "lat_center", "lon_center", "zone_type",
    "nearest_landmark", "dist_to_anchor_km", "dist_from_center_km",
    "lighting_score", "streetlight_operational_pct", "crowd_density",
    "historical_incidents_annual", "unsafe_reports_count",
]
features = features[feature_cols]

features.to_csv("/home/claude/safegrid_features.csv", index=False)
labels.to_csv("/home/claude/safegrid_labels.csv", index=False)
reports_df.to_csv("/home/claude/safegrid_unsafe_reports.csv", index=False)

reference = features.merge(labels, on=["segment_id", "time_bucket"])
reference.to_csv("/home/claude/safegrid_reference_full.csv", index=False)

# ---------------------------------------------------------------------------
# sanity prints
# ---------------------------------------------------------------------------
print(f"segments: {df.segment_id.nunique()}  feature rows (segment x time_bucket): {len(features)}")
print("\nzone_type counts (unique segments):")
print(df["zone_type"].value_counts())
print("\nrisk_band distribution:")
print(labels["risk_band"].value_counts(normalize=True).round(3))
print(f"\nunsafe reports generated: {len(reports_df)}  | with device_hash: {reports_df.device_hash_sim.notna().sum()}")
print(f"repeat-device reports (predator-pattern signal): "
      f"{reports_df.device_hash_sim.isin(repeat_device_hashes).sum()}")
dup_check = reports_df.dropna(subset=['device_hash_sim']).groupby('device_hash_sim')['segment_id'].nunique()
print(f"devices appearing across >1 distinct segment: {(dup_check > 1).sum()}")

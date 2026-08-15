"""
SafeGrid Backend
Infinity Hacks Round 2

Backend responsibilities:
    1. predict_risk(lat, lon, time)
    2. get_risk_grid(time)
    3. submit_report(lat, lon)
    4. get_reroute(start, end)

Plain Python. No Flask/FastAPI server required.
"""

import os
import uuid
from datetime import datetime

import joblib
import numpy as np
import pandas as pd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(BASE_DIR, "safegrid_reference_full.csv")
REPORTS_PATH = os.path.join(BASE_DIR, "safegrid_unsafe_reports.csv")
MODEL_PATH = os.path.join(BASE_DIR, "risk_model.pkl")
ZONE_ENCODER_PATH = os.path.join(BASE_DIR, "zone_encoder.pkl")
TIME_ENCODER_PATH = os.path.join(BASE_DIR, "time_encoder.pkl")

TIME_BUCKETS = {"morning", "afternoon", "evening", "night"}

MODEL_FEATURES = [
    "lighting_score",
    "streetlight_operational_pct",
    "crowd_density",
    "historical_incidents_annual",
    "unsafe_reports_count",
    "zone_type_enc",
    "time_bucket_enc",
    "dist_to_anchor_km",
    "dist_from_center_km",
]


# Load once when backend.py is imported.
df = pd.read_csv(DATA_PATH)
model = joblib.load(MODEL_PATH)
zone_encoder = joblib.load(ZONE_ENCODER_PATH)
time_encoder = joblib.load(TIME_ENCODER_PATH)


def get_time_bucket(hour):
    """Convert hour to the project's four time buckets."""
    hour = int(hour) % 24

    if 5 <= hour < 11:
        return "morning"
    if 11 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 21:
        return "evening"
    return "night"


def normalize_time(time=None):
    """
    Accepts None, hour, 'HH:MM', or a time bucket.
    Returns a SafeGrid time bucket.
    """
    if time is None:
        return get_time_bucket(datetime.now().hour)

    if isinstance(time, (int, float)):
        return get_time_bucket(int(time))

    if isinstance(time, str):
        value = time.strip().lower()

        if value in TIME_BUCKETS:
            return value

        if ":" in value:
            try:
                return get_time_bucket(int(value.split(":")[0]))
            except ValueError:
                pass

        try:
            return get_time_bucket(int(value))
        except ValueError:
            pass

    raise ValueError(
        "Invalid time. Use an hour, HH:MM, or "
        "morning/afternoon/evening/night."
    )


def find_nearest_segment(lat, lon):
    """Return the segment nearest to the supplied coordinates."""
    lat = float(lat)
    lon = float(lon)

    distance = (
        (df["lat_center"] - lat) ** 2
        + (df["lon_center"] - lon) ** 2
    )

    return df.loc[distance.idxmin(), "segment_id"]


def _get_segment_row(segment_id, time_bucket):
    """Return the row for one segment and one time bucket."""
    rows = df[
        (df["segment_id"] == segment_id)
        & (df["time_bucket"] == time_bucket)
    ]

    if rows.empty:
        return None

    return rows.iloc[0]


def _encode_zone(zone_type):
    if zone_type in zone_encoder.classes_:
        return int(zone_encoder.transform([zone_type])[0])

    return int(zone_encoder.transform([zone_encoder.classes_[0]])[0])


def _encode_time(time_bucket):
    if time_bucket in time_encoder.classes_:
        return int(time_encoder.transform([time_bucket])[0])

    return int(time_encoder.transform([time_encoder.classes_[0]])[0])


def get_risk_band(score):
    """Convert numeric risk score to low/medium/high."""
    score = float(score)

    if score <= 25.1:
        return "low"
    if score <= 40.4:
        return "medium"
    return "high"


def _predict_row(row):
    """Run the trained XGBoost model on one feature row."""
    X = pd.DataFrame([{
        "lighting_score": float(row["lighting_score"]),
        "streetlight_operational_pct": float(
            row["streetlight_operational_pct"]
        ),
        "crowd_density": float(row["crowd_density"]),
        "historical_incidents_annual": float(
            row["historical_incidents_annual"]
        ),
        "unsafe_reports_count": float(row["unsafe_reports_count"]),
        "zone_type_enc": _encode_zone(row["zone_type"]),
        "time_bucket_enc": _encode_time(row["time_bucket"]),
        "dist_to_anchor_km": float(row["dist_to_anchor_km"]),
        "dist_from_center_km": float(row["dist_from_center_km"]),
    }])

    X = X[MODEL_FEATURES]
    score = float(model.predict(X)[0])

    return max(0.0, min(100.0, score))


def predict_risk(lat, lon, time=None):
    """
    Predict risk from location and time.

    Example:
        predict_risk(20.2961, 85.8245, "21:30")
    """
    lat = float(lat)
    lon = float(lon)
    time_bucket = normalize_time(time)

    segment_id = find_nearest_segment(lat, lon)
    row = _get_segment_row(segment_id, time_bucket)

    if row is None:
        raise ValueError(
            f"No data for segment {segment_id} "
            f"and time bucket {time_bucket}."
        )

    score = _predict_row(row)

    return {
        "lat": lat,
        "lon": lon,
        "segment_id": segment_id,
        "time_bucket": time_bucket,
        "score": round(score, 1),
        "band": get_risk_band(score),
    }


def get_risk_grid(time=None):
    """
    Predict risk for every segment in one time bucket.
    Returns data ready for Streamlit/Leaflet.
    """
    time_bucket = normalize_time(time)
    grid = df[df["time_bucket"] == time_bucket]

    results = []

    for _, row in grid.iterrows():
        score = _predict_row(row)

        results.append({
            "segment_id": row["segment_id"],
            "lat": float(row["lat_center"]),
            "lon": float(row["lon_center"]),
            "score": round(score, 1),
            "band": get_risk_band(score),
            "time_bucket": time_bucket,
            "zone_type": row["zone_type"],
            "landmark": row["nearest_landmark"],
        })

    return results


def submit_report(lat, lon):
    """
    Save a live 'felt unsafe' report to the report CSV.
    """
    lat = float(lat)
    lon = float(lon)

    segment_id = find_nearest_segment(lat, lon)
    now = datetime.now()
    time_bucket = get_time_bucket(now.hour)

    report_id = "LIVE-" + uuid.uuid4().hex[:8].upper()

    if os.path.exists(REPORTS_PATH):
        reports = pd.read_csv(REPORTS_PATH)
    else:
        reports = pd.DataFrame(columns=[
            "report_id",
            "segment_id",
            "lat",
            "lon",
            "timestamp",
            "time_bucket",
            "device_hash_sim",
        ])

    new_report = {
        "report_id": report_id,
        "segment_id": segment_id,
        "lat": round(lat, 6),
        "lon": round(lon, 6),
        "timestamp": now.isoformat(
            sep=" ", timespec="seconds"
        ),
        "time_bucket": time_bucket,
        "device_hash_sim": None,
    }

    reports = pd.concat(
        [reports, pd.DataFrame([new_report])],
        ignore_index=True,
    )

    reports.to_csv(REPORTS_PATH, index=False)

    return {
        "success": True,
        "report_id": report_id,
        "segment_id": segment_id,
        "time_bucket": time_bucket,
        "message": "Unsafe report submitted successfully.",
    }


def _generate_candidate_route(start, end, offset=0.0, num_points=25):
    """Generate a straight/curved candidate route."""
    start_lat, start_lon = start
    end_lat, end_lon = end

    points = []

    for i in range(num_points):
        t = i / (num_points - 1) if num_points > 1 else 0.0

        lat = start_lat + t * (end_lat - start_lat)
        lon = start_lon + t * (end_lon - start_lon)

        curve = np.sin(np.pi * t) * offset
        lat += curve
        lon += curve

        points.append((float(lat), float(lon)))

    return points


def _calculate_route_risk(route, time=None):
    """Calculate mean predicted risk along a candidate route."""
    risks = []

    for lat, lon in route:
        try:
            result = predict_risk(lat, lon, time)
            risks.append(result["score"])
        except Exception:
            # Unknown locations are treated conservatively.
            risks.append(100.0)

    return float(np.mean(risks)) if risks else 100.0


def get_reroute(start, end, time=None, num_points=25):
    """
    Compare candidate paths and return the lower-risk route.

    start/end format:
        (latitude, longitude)
    """
    start = (float(start[0]), float(start[1]))
    end = (float(end[0]), float(end[1]))

    time_bucket = normalize_time(time)

    offsets = [0.0, -0.0030, -0.0015, 0.0015, 0.0030]
    candidates = []

    for offset in offsets:
        route = _generate_candidate_route(
            start,
            end,
            offset=offset,
            num_points=num_points,
        )

        risk = _calculate_route_risk(
            route,
            time=time_bucket,
        )

        candidates.append({
            "route": route,
            "average_risk": risk,
        })

    safest = min(
        candidates,
        key=lambda item: item["average_risk"],
    )

    return {
        "start": {
            "lat": start[0],
            "lon": start[1],
        },
        "end": {
            "lat": end[0],
            "lon": end[1],
        },
        "route": [
            {"lat": lat, "lon": lon}
            for lat, lon in safest["route"]
        ],
        "average_risk": round(
            safest["average_risk"], 1
        ),
        "risk_band": get_risk_band(
            safest["average_risk"]
        ),
        "time_bucket": time_bucket,
        "compared_routes": len(candidates),
    }


def backend_info():
    """Quick health check."""
    return {
        "status": "ready",
        "segments": int(df["segment_id"].nunique()),
        "rows": int(len(df)),
        "time_buckets": sorted(
            df["time_bucket"].dropna().unique().tolist()
        ),
        "model_loaded": model is not None,
        "zone_encoder_loaded": zone_encoder is not None,
        "time_encoder_loaded": time_encoder is not None,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("SAFEGRID BACKEND TEST")
    print("=" * 60)

    print("\n[1] Backend info:")
    print(backend_info())

    print("\n[2] Risk prediction:")
    print(
        predict_risk(
            lat=20.2961,
            lon=85.8245,
            time="21:30",
        )
    )

    print("\n[3] Risk grid:")
    grid = get_risk_grid("night")
    print("Number of map points:", len(grid))
    if grid:
        print("First point:", grid[0])

    print("\n[4] Reroute:")
    route = get_reroute(
        start=(20.2961, 85.8245),
        end=(20.3100, 85.8400),
        time="night",
    )
    print("Average route risk:", route["average_risk"])
    print("Risk band:", route["risk_band"])
    print("Route points:", len(route["route"]))

    print("\n" + "=" * 60)
    print("BACKEND TEST COMPLETE")
    print("=" * 60)

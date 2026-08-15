"""
SafeGrid - Risk Score Model
Trains an XGBoost model to predict risk_score from segment features.
"""

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb

# ---- 1. Load data ----
DATA_PATH = "CODE-COVEN/safegrid_dataset (1).csv"   # update path if different
df = pd.read_csv(DATA_PATH)

FEATURE_COLS = [
    "lighting_score", "streetlight_operational_pct", "crowd_density",
    "historical_incidents_annual", "unsafe_reports_count",
    "zone_type", "time_bucket", "dist_to_anchor_km", "dist_from_center_km"
]
TARGET_COL = "risk_score"

data = df[FEATURE_COLS + [TARGET_COL]].copy()

# ---- 2. Encode categorical columns ----
le_zone = LabelEncoder()
le_time = LabelEncoder()
data["zone_type_enc"] = le_zone.fit_transform(data["zone_type"])
data["time_bucket_enc"] = le_time.fit_transform(data["time_bucket"])

MODEL_FEATURES = [
    "lighting_score", "streetlight_operational_pct", "crowd_density",
    "historical_incidents_annual", "unsafe_reports_count",
    "zone_type_enc", "time_bucket_enc", "dist_to_anchor_km", "dist_from_center_km"
]

X = data[MODEL_FEATURES]
y = data[TARGET_COL]

# ---- 3. Train/test split ----
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ---- 4. Train XGBoost model ----
model = xgb.XGBRegressor(
    n_estimators=150,
    max_depth=5,
    learning_rate=0.1,
    random_state=42
)
model.fit(X_train, y_train)

# ---- 5. Evaluate ----
preds = model.predict(X_test)
print(f"MAE: {mean_absolute_error(y_test, preds):.2f}")
print(f"R2 Score: {r2_score(y_test, preds):.3f}")

# ---- 6. Save model + encoders ----
joblib.dump(model, "risk_model.pkl")
joblib.dump(le_zone, "zone_encoder.pkl")
joblib.dump(le_time, "time_encoder.pkl")
print("Saved: risk_model.pkl, zone_encoder.pkl, time_encoder.pkl")


# ---- 7. Reusable prediction function (import this elsewhere) ----
def predict_risk(lighting_score, streetlight_pct, crowd_density,
                  historical_incidents, unsafe_reports,
                  zone_type, time_bucket, dist_to_anchor, dist_from_center):
    """
    Predict risk score (0-100) for a given segment's features.
    Falls back to a default category if an unseen zone_type/time_bucket is passed,
    instead of crashing.
    """
    m = joblib.load("risk_model.pkl")
    lz = joblib.load("zone_encoder.pkl")
    lt = joblib.load("time_encoder.pkl")

    # Safe encode: fallback to most common known category if unseen
    if zone_type in lz.classes_:
        zone_enc = lz.transform([zone_type])[0]
    else:
        zone_enc = lz.transform([lz.classes_[0]])[0]  # fallback

    if time_bucket in lt.classes_:
        time_enc = lt.transform([time_bucket])[0]
    else:
        time_enc = lt.transform([lt.classes_[0]])[0]  # fallback

    row = pd.DataFrame([{
        "lighting_score": lighting_score,
        "streetlight_operational_pct": streetlight_pct,
        "crowd_density": crowd_density,
        "historical_incidents_annual": historical_incidents,
        "unsafe_reports_count": unsafe_reports,
        "zone_type_enc": zone_enc,
        "time_bucket_enc": time_enc,
        "dist_to_anchor_km": dist_to_anchor,
        "dist_from_center_km": dist_from_center
    }])
    score = float(m.predict(row)[0])
    return max(0.0, min(100.0, score))  # clip to valid 0-100 range


def get_risk_band(score):
    """Convert numeric risk score into a user-facing band."""
    if score <= 25.1:
        return "low"
    elif score <= 40.4:
        return "medium"
    else:
        return "high"


if __name__ == "__main__":
    # quick sanity test on a real row
    sample = df.iloc[0]
    score = predict_risk(
        sample["lighting_score"], sample["streetlight_operational_pct"],
        sample["crowd_density"], sample["historical_incidents_annual"],
        sample["unsafe_reports_count"], sample["zone_type"],
        sample["time_bucket"], sample["dist_to_anchor_km"], sample["dist_from_center_km"]
    )
    print(f"Sample prediction: {score:.1f} (actual: {sample['risk_score']})")
    print(f"Band: {get_risk_band(score)} (actual: {sample['risk_band']})")

    # test with an unseen zone_type to confirm no crash
    score2 = predict_risk(0.3, 25, 0.2, 2, 1, "some_unknown_zone", "night", 3.0, 5.0)
    print(f"Unseen-category test prediction: {score2:.1f} (band: {get_risk_band(score2)})")
    # ============================================================
# API CONTRACT — for Backend Dev
# ============================================================
# Import:
#   from train_model import predict_risk, get_risk_band
#
# Call ONLY using keyword arguments (never positional):
#
#   score = predict_risk(
#       lighting_score=0.3,          # float, 0.0–1.0 (higher = better lit)
#       streetlight_pct=25,          # float, 0–100 (% streetlights working)
#       crowd_density=0.2,           # float, 0.0–1.0 (higher = more crowded)
#       historical_incidents=2,      # int, annual incident count for segment
#       unsafe_reports=1,            # int, unsafe_reports_count for this time_bucket
#       zone_type="residential_mixed",  # str, must match a value from the
#                                        # dataset's zone_type column
#                                        # e.g. residential_mixed, market_commercial,
#                                        # transit_hub, it_park, public_venue,
#                                        # heritage_dense, outskirts, university_campus,
#                                        # residential_dense
#       time_bucket="night",         # str, one of: morning, afternoon, evening, night
#       dist_to_anchor=3.0,          # float, km from nearest landmark/anchor point
#       dist_from_center=5.0         # float, km from city center
#   )
#
# Returns:
#   float — risk score from 0.0 to 100.0
#
# To convert into a display-friendly band:
#   band = get_risk_band(score)   # returns "low", "medium", or "high"
#
# IMPORTANT:
#   - All 9 values must be for the SAME segment + SAME time_bucket, pulled
#     from the dataset row (or live equivalent) — do not mix values from
#     different rows/times.
#   - Unknown zone_type or time_bucket values will NOT crash the app —
#     they fall back to a default category automatically.
#   - Always show `band`, not raw `score`, to the end user on the map.
# ============================================================
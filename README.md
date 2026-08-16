# SafeGrid - Predictive Urban Safety Matrix and AI Navigation

**Team Code Coven | Infinity Hacks 2026**

SafeGrid is a machine learning-driven urban safety intelligence web application engineered to protect women by shifting safety systems from reactive emergency dispatch to proactive danger prediction. Built for Bhubaneswar, SafeGrid analyzes infrastructural street lighting, operational streetlight ratios, diurnal crowd volumes, historical incident frequencies, and crowdsourced vigilance reports to recommend safer travel routes.

---

## 1. Executive Summary and Problem Statement

Traditional women's safety mobile applications only activate after an incident or distress situation is already unfolding (SOS alerts, panic sirens, live location sharing). 

SafeGrid changes this dynamic through **Predictive Prevention**:
- Evaluates city streets and intersections dynamically across 4 diurnal time buckets (morning, afternoon, evening, night).
- Predicts granular, segment-level risk scores (0 to 100) and risk classifications (Low, Medium, High).
- Evaluates alternative travel trajectories between any two urban landmarks to recommend the lowest-risk candidate route.
- Collects anonymous crowdsourced reports ("Felt Unsafe Here") to dynamically update the live grid.

---

## 2. Core Modules and System Architecture

### A. Live SafeGrid Geospatial Heatmap
- **Backend Function**: `get_risk_grid(time)`
- **Technology**: Leaflet / Folium embedded in Streamlit.
- **Visual Encoding**:
  - Green: Low Risk (Safe Zone)
  - Amber / Yellow: Moderate Risk (Caution)
  - Crimson / Red: Elevated Risk (High Alert)
- **Granularity**: 500-meter hexagonal and square grid cells covering the entire metropolitan bounding box of Bhubaneswar.
- **Inspection**: Click or hover over any segment to inspect zone type, nearest anchor landmark, operational streetlight percentage, and model risk score.

### B. Time-of-Day Risk Matrix
- **Diurnal Time Buckets**:
  - Morning: 05:00 - 10:59
  - Afternoon: 11:00 - 16:59
  - Evening: 17:00 - 20:59
  - Night: 21:00 - 04:59
- Dynamic recalculation adapts to variations in ambient lighting and crowd density throughout the day.

### C. AI Safe Route Navigator
- **Backend Function**: `get_reroute(start, end, time, num_points=25)`
- **Modes**:
  1. **Landmark Directory**: 1-click selection between 20+ major Bhubaneswar landmarks (KIIT, Patia Infocity, Esplanade Mall, Master Canteen, Airport, Railway Station, etc.) with a location swap button.
  2. **Pick on Map**: Click anywhere on the map to set origin or destination.
  3. **GPS Coordinates**: Custom latitude/longitude input.
- **Algorithm**: Generates candidate trajectories with sinusoidal lateral deviations and calculates integrated line-integral risk across all passing segments, outputting the path with the minimum average predicted risk.

### D. Crowdsourced Incident Reporter ("Felt Unsafe Here")
- **Backend Function**: `submit_report(lat, lon, note)`
- Captures coordinates via map clicks or manual entry.
- Categorizes hazard tags: Broken Streetlights, Suspicious Loiterers, Deserted Alleys, Catcalling/Harassment, Stalker Suspicion, Lack of Police Patrols.
- Appends to `safegrid_unsafe_reports.csv` and updates live grid weighting.

### E. Emergency Command and Deterrent Suite
- **1-Tap Distress Broadcast**: Formats live GPS distress messages with Google Maps links for rapid WhatsApp and SMS dispatch.
- **High-Decibel Siren Simulator**: Web Audio API oscillator delivering deterrent alarm frequencies directly in the browser.
- **Fake Call Assistant**: Simulated incoming call with custom caller IDs (Family Member, Police Control Room, SafeGrid Dispatch) to deter harassment.
- **Walk-With-Me Companion**: Time-window journey monitor with arrival check-ins.
- **Emergency Directory**: Quick dial links for National Emergency (112), Women Helpline (1091), Women in Distress (181), and Anti-Harassment (1090).

---

## 3. Technology Stack

- **Frontend Framework**: Streamlit (Python)
- **Geospatial Mapping**: Folium, Streamlit-Folium, Leaflet
- **Machine Learning Engine**: XGBoost Regressor and Classifier
- **Data Engineering**: Pandas, NumPy, Scikit-learn
- **Serialization**: Joblib (Models and Label Encoders)
- **Styling**: Vanilla CSS (Cyberpunk Soft-Glam Dark Theme)

---

## 4. Directory Structure

```text
CODE-COVEN/
|-- app.py                         # Main Streamlit web application frontend
|-- backend.py                     # Core backend ML functions and routing engine
|-- train_model.py                 # XGBoost training pipeline and evaluation
|-- build_safegrid_dataset_v2.py   # Geospatial dataset generation and calibration
|-- safegrid_dataset (1).csv       # Segment feature dataset across time buckets
|-- safegrid_unsafe_reports.csv    # Crowdsourced incident report database
|-- risk_model.pkl                 # Trained XGBoost regression model
|-- zone_encoder.pkl               # Scikit-learn LabelEncoder for urban zones
|-- time_encoder.pkl               # Scikit-learn LabelEncoder for time buckets
|-- requirements.txt               # Python package dependencies
`-- README.md                      # Project documentation and specifications
```

---

## 5. Installation and Setup Instructions

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Pip package manager

### Step 1: Clone the Repository
```bash
git clone <repository_url>
cd CODE-COVEN
```

### Step 2: Create a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501`.

---

## 6. Backend API and Functions Reference

### `predict_risk(lat, lon, time=None)`
- **Parameters**:
  - `lat` (float): Latitude coordinate.
  - `lon` (float): Longitude coordinate.
  - `time` (str/int/None): Time bucket or hour of day.
- **Returns**: Dictionary with `segment_id`, `score` (0-100), `band` ("low", "medium", "high"), and normalized `time_bucket`.

### `get_risk_grid(time=None)`
- **Parameters**: `time` (str/int/None)
- **Returns**: List of all city segments with coordinates, predicted risk scores, risk bands, zone types, and nearest landmarks. Vectorized for sub-10ms batch execution.

### `submit_report(lat, lon, note=None)`
- **Parameters**: `lat` (float), `lon` (float), `note` (str)
- **Returns**: Dictionary with `report_id`, `segment_id`, `time_bucket`, and submission confirmation status.

### `get_reroute(start, end, time=None, num_points=25)`
- **Parameters**: `start` (tuple), `end` (tuple), `time` (str/int), `num_points` (int)
- **Returns**: Dictionary containing start coordinates, end coordinates, safest route waypoint array, average risk score, risk band, and candidate comparison count.

---

## 7. Machine Learning Model Details

- **Model Type**: XGBoost Regressor (`n_estimators=150`, `max_depth=5`, `learning_rate=0.1`)
- **Key Predictive Features**:
  1. `lighting_score`: Ambient and street lighting index (0.0 to 1.0)
  2. `streetlight_operational_pct`: Percentage of working public streetlights (0 to 100)
  3. `crowd_density`: Diurnal pedestrian and vehicular volume index (0.0 to 1.0)
  4. `historical_incidents_annual`: Historical police incident records for segment
  5. `unsafe_reports_count`: Rolling 30-day crowdsourced report frequency
  6. `zone_type_enc`: Categorical zone encoding (IT park, market, residential, transit hub, heritage, public venue)
  7. `time_bucket_enc`: Diurnal period encoding
  8. `dist_to_anchor_km`: Distance to nearest major city landmark
  9. `dist_from_center_km`: Distance from metropolitan center
- **Risk Band Quantiles**:
  - Low Risk: <= 25.1
  - Medium Risk: 25.2 - 40.4
  - High Risk: > 40.4

---

## 8. License and Credits

Developed for Infinity Hacks 2026 by Team Code Coven.
Dedicated to women safety, urban accessibility, and predictive AI.

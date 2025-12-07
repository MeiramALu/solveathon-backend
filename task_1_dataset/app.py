# app.py
from flask import Flask, jsonify, request, render_template
import pandas as pd
import numpy as np
import os
import joblib

from task_1_model_dataset import WaterAISuite

app = Flask(__name__)

suite = WaterAISuite(dry_threshold=30.0, target_humidity=35.0, max_daily_m3_mu=40.0)

print("[INIT] Loading data...")
suite.load_and_process_data()

print("[INIT] Loading model...")
if os.path.exists("Irrigation_Model.pkl"):
    suite.model = joblib.load("Irrigation_Model.pkl")
else:
    print("Model file not found. Training a new one...")
    suite.train()
    suite.save_model()

print("[INIT] Computing predictions...")
pred_df = suite.get_predictions_table()
pred_df = suite.add_irrigation_recommendation(pred_df)

MAKTAARAL_LAT = 40.8366782
MAKTAARAL_LON = 68.2385339

center_x = pred_df["loc_x"].mean()
center_y = pred_df["loc_y"].mean()

pred_df["vis_lat"] = MAKTAARAL_LAT + (pred_df["loc_y"] - center_y)
pred_df["vis_lon"] = MAKTAARAL_LON + (pred_df["loc_x"] - center_x)

# Ensure date is proper datetime & sorted
pred_df["date"] = pd.to_datetime(pred_df["date"])
pred_df = pred_df.sort_values("date")

# Ensure date is datetime
pred_df["date"] = pd.to_datetime(pred_df["date"])
pred_df = pred_df.sort_values("date")
LAST_DATE = pred_df["date"].max()

# Snapshot for that date (one row per location)
last_day_df = pred_df[pred_df["date"] == LAST_DATE].copy()

N_FUTURE_DAYS = 7
# Mark historical rows
pred_df["is_future"] = False

future_frames = []
current_base = last_day_df.copy()

for step in range(1, N_FUTURE_DAYS + 1):
    # simulate 1 day ahead from current_base
    future_day = suite.simulate_future(current_base, days_ahead=1)
    future_day["is_future"] = True
    future_day["future_step"] = step

    # add visualization lat/lon for this future day too
    future_day["vis_lat"] = MAKTAARAL_LAT + (future_day["loc_y"] - center_y)
    future_day["vis_lon"] = MAKTAARAL_LON + (future_day["loc_x"] - center_x)

    future_frames.append(future_day)
    current_base = future_day.copy()  # next step starts from latest simulated day

future_df = pd.concat(future_frames, ignore_index=True)

# Combine historical + future into one big table
full_df = pd.concat([pred_df, future_df], ignore_index=True)
full_df = full_df.sort_values("date").reset_index(drop=True)

# Keep handy globals
FIRST_DATE = full_df["date"].min().date()
LAST_OBS_DATE = LAST_DATE.date()  # last real observed date
LAST_FULL_DATE = full_df["date"].max().date()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/dates")
def get_dates():
    dates = sorted(full_df["date"].dt.date.unique())
    dates_str = [d.isoformat() for d in dates]

    return jsonify(
        {
            "dates": dates_str,
            "first_date": FIRST_DATE.isoformat(),
            "last_observed_date": LAST_OBS_DATE.isoformat(),
            "last_full_date": LAST_FULL_DATE.isoformat(),
        }
    )


@app.route("/api/map")
def get_map_data():
    date_str = request.args.get("date")
    if not date_str:
        return jsonify({"error": "Missing 'date' parameter (YYYY-MM-DD)."}), 400

    try:
        d = pd.to_datetime(date_str).date()
    except Exception:
        return jsonify({"error": "Invalid date format."}), 400

    day_df = full_df[full_df["date"].dt.date == d].copy()
    points = []

    for _, row in day_df.iterrows():
        points.append(
            {
                "loc_x": float(row["loc_x"]),
                "loc_y": float(row["loc_y"]),
                "lat": float(row["vis_lat"]),
                "lon": float(row["vis_lon"]),
                "soil_humidity": float(row["soil_humidity(%)"]),
                "pred_humidity": float(row["Pred_Tomorrow_Humidity"]),
                "soil_temp": float(row["soil_temperature(°C)"]),
                "rain": float(row["rain(mm/day)"]),
                "air_temp": float(row["daily_mean_temperature(°C)"]),
                "irrigation": float(row["irrigation_amount(m3/mu)"]),
                "days_since_irrigation": int(row["days_since_irrigation"]),
                "recommended_irrigation": float(
                    row.get(
                        "Recommended_Irrigation_m3_mu",
                        row["Recommended_Irrigation_m3_mu"],
                    )
                ),
                "dry_risk": int(row["Dry_Risk"]),
                "action": row["Irrigation_Action"],
                "is_future": bool(row["is_future"]),  # NEW
            }
        )

    return jsonify({"date": date_str, "points": points})


@app.route("/api/date_summary")
def get_date_summary():
    df = full_df.copy()
    df["date_only"] = df["date"].dt.date

    grouped = (
        df.groupby("date_only")
        .agg(
            avg_pred=("Pred_Tomorrow_Humidity", "mean"),
            risk_count=("Dry_Risk", "sum"),
            point_count=("Pred_Tomorrow_Humidity", "size"),
        )
        .reset_index()
    )

    days = []
    for _, row in grouped.iterrows():
        days.append(
            {
                "date": row["date_only"].isoformat(),
                "avg_pred": float(row["avg_pred"]),
                "risk_count": int(row["risk_count"]),
                "point_count": int(row["point_count"]),
            }
        )

    return jsonify(
        {
            "dates": days,
            "last_observed_date": LAST_OBS_DATE.isoformat(),
        }
    )


@app.route("/api/timeseries")
def get_timeseries():
    loc_x_str = request.args.get("loc_x")
    loc_y_str = request.args.get("loc_y")

    if loc_x_str is None or loc_y_str is None:
        return (
            jsonify(
                {
                    "dates": [],
                    "actual": [],
                    "pred": [],
                    "irrigation": [],
                    "error": "loc_x and loc_y query params required",
                }
            ),
            400,
        )

    try:
        target_x = round(float(loc_x_str), 4)
        target_y = round(float(loc_y_str), 4)
    except ValueError:
        return (
            jsonify(
                {
                    "dates": [],
                    "actual": [],
                    "pred": [],
                    "irrigation": [],
                    "error": "Invalid loc_x/loc_y values",
                }
            ),
            400,
        )

    df = full_df.copy()
    df["loc_x_r"] = df["loc_x"].round(4)
    df["loc_y_r"] = df["loc_y"].round(4)

    mask = (df["loc_x_r"] == target_x) & (df["loc_y_r"] == target_y)
    loc_df = df.loc[mask].sort_values("date")

    if loc_df.empty:
        return jsonify(
            {
                "dates": [],
                "actual": [],
                "pred": [],
                "irrigation": [],
            }
        )

    dates = []
    actual = []
    pred = []
    irrigation = []

    for _, row in loc_df.iterrows():
        d = row["date"].date()
        dates.append(row["date"].strftime("%Y-%m-%d"))

        if d > LAST_OBS_DATE:
            # future → only prediction
            actual.append(None)  # becomes `null` in JSON, Chart.js will gap the line
        else:
            actual.append(float(row["soil_humidity(%)"]))

        pred.append(float(row["Pred_Tomorrow_Humidity"]))
        irrigation.append(float(row["irrigation_amount(m3/mu)"]))

    return jsonify(
        {
            "dates": dates,
            "actual": actual,
            "pred": pred,
            "irrigation": irrigation,
            "last_observed_date": LAST_OBS_DATE.isoformat(),
        }
    )


if __name__ == "__main__":
    app.run(debug=True)

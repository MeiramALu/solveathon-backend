import pandas as pd
import numpy as np


def generate_dataset_v2():
    print("🚀 Starting Corrected Dataset Generation...")

    # ==========================================
    # 1. LOAD DATA
    # ==========================================
    try:
        # Load core files
        humidity_df = pd.read_csv("HumiditySensor.csv")
        temp_df = pd.read_csv("TemSensor.csv")
        weather_df = pd.read_csv("Weather.csv")
        mgmt_df = pd.read_csv("ManagementInfo.csv")
        print("✅ Raw files loaded.")
    except FileNotFoundError as e:
        print(f"❌ Error: Missing file. {e}")
        return

    # ==========================================
    # 2. DATE PARSING HELPERS
    # ==========================================
    def parse_sensor_date(series):
        # YYYYMMDDHHMM -> Datetime
        return pd.to_datetime(series.astype(str), format="%Y%m%d%H%M", errors="coerce")

    def parse_daily_date(series):
        # YYYYMMDD -> Datetime
        return pd.to_datetime(series.astype(str), format="%Y%m%d", errors="coerce")

    # ==========================================
    # 3. PROCESS HUMIDITY (Target)
    # ==========================================
    print("💧 Processing Humidity...")
    humidity_df["timestamp"] = parse_sensor_date(humidity_df["collect_time"])
    humidity_df["date"] = humidity_df["timestamp"].dt.date
    humidity_df["date"] = pd.to_datetime(humidity_df["date"])

    # Group by Date AND Location (Round coords to avoid floating point mismatch)
    humidity_df["loc_x"] = humidity_df["location_info_x"].round(5)
    humidity_df["loc_y"] = humidity_df["location_info_y"].round(5)

    hum_daily = (
        humidity_df.groupby(["date", "loc_x", "loc_y"])["soil_humidity(%)"]
        .mean()
        .reset_index()
    )

    # ==========================================
    # 4. PROCESS TEMPERATURE (Feature)
    # ==========================================
    print("🌡️ Processing Temperature...")
    temp_df["timestamp"] = parse_sensor_date(temp_df["collect_time"])
    temp_df["date"] = temp_df["timestamp"].dt.date
    temp_df["date"] = pd.to_datetime(temp_df["date"])

    temp_df["loc_x"] = temp_df["location_info_x"].round(5)
    temp_df["loc_y"] = temp_df["location_info_y"].round(5)

    # Note: We do NOT use sensor_id here, just Location
    temp_daily = (
        temp_df.groupby(["date", "loc_x", "loc_y"])["soil_temperature(°C)"]
        .mean()
        .reset_index()
    )

    # ==========================================
    # 5. MERGE SENSORS (By Location & Date)
    # ==========================================
    print("🔗 Merging Sensors by Location...")
    # This was the failing step before. Now we merge on Coordinates.
    sensor_data = pd.merge(
        hum_daily, temp_daily, on=["date", "loc_x", "loc_y"], how="left"
    )

    # ==========================================
    # 6. PROCESS WEATHER & IRRIGATION
    # ==========================================
    print("☁️ Processing Environment Data...")

    # Weather
    weather_df["date"] = parse_daily_date(weather_df["date"])
    weather_cols = [
        "date",
        "rain(mm/day)",
        "wind(km/d)",
        "daily_mean_temperature(°C)",
        "srad(MJ/(m2*day))",
    ]
    weather_final = weather_df[weather_cols].copy()

    # Irrigation
    mgmt_df["irrigation_time"] = parse_daily_date(mgmt_df["irrigation_time"])
    mgmt_df["date"] = mgmt_df["irrigation_time"]
    daily_irrigation = (
        mgmt_df.groupby("date")["irrigation_amount(m3/mu)"].sum().reset_index()
    )

    # ==========================================
    # 7. FINAL MERGE
    # ==========================================
    print("🔄 Creating Final Dataset...")

    final_df = pd.merge(sensor_data, weather_final, on="date", how="left")
    final_df = pd.merge(final_df, daily_irrigation, on="date", how="left")

    # Fill NaNs
    final_df["irrigation_amount(m3/mu)"] = final_df["irrigation_amount(m3/mu)"].fillna(
        0
    )

    # Fix for Deprecation Warning: Use ffill() and bfill()
    w_cols = [
        "rain(mm/day)",
        "wind(km/d)",
        "daily_mean_temperature(°C)",
        "srad(MJ/(m2*day))",
    ]
    final_df[w_cols] = final_df[w_cols].ffill().bfill()

    # Calculate Days Since Irrigation
    print("⏳ Calculating Days Since Water...")
    irrigation_dates = daily_irrigation[
        daily_irrigation["irrigation_amount(m3/mu)"] > 0
    ]["date"]

    # Helper to calculate lag
    unique_dates = pd.DataFrame({"date": final_df["date"].unique()})

    def get_lag(d):
        past = irrigation_dates[irrigation_dates < d]
        if past.empty:
            return -1
        return (d - past.max()).days

    unique_dates["days_since_irrigation"] = unique_dates["date"].apply(get_lag)
    final_df = pd.merge(final_df, unique_dates, on="date", how="left")

    # Drop incomplete rows (e.g. if weather is missing entirely for that year)
    final_df = final_df.dropna(subset=["soil_humidity(%)"])

    # ==========================================
    # 8. SAVE
    # ==========================================
    output_filename = "Cotton_Water_Dataset_Fixed.csv"
    final_df.to_csv(output_filename, index=False)

    print(f"\n✅ SUCCESS! Dataset saved: {output_filename}")
    print(f"📊 Total Rows: {len(final_df)}")
    print(f"📍 Unique Locations: {len(final_df.groupby(['loc_x', 'loc_y']))}")
    print("First 5 rows:")
    print(final_df.head())


if __name__ == "__main__":
    generate_dataset_v2()

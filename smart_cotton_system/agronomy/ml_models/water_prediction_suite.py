"""
Enhanced Water AI Suite for Smart Cotton System
Adapted from task_1_model_dataset.py for Django integration
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import warnings
from pathlib import Path
from django.conf import settings
import os

warnings.filterwarnings("ignore")


class WaterAISuite:
    """
    Complete Pipeline for Water Resource Management.
    Handles Data Ingestion, Geospatial Aggregation, Training, and Analytics.
    """

    def __init__(self, dry_threshold=30.0, target_humidity=35.0, max_daily_m3_mu=40.0, data_dir=None):
        self.model = None
        self.data = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.preds = None

        self.dry_threshold = dry_threshold
        self.target_humidity = target_humidity
        self.max_daily_m3_mu = max_daily_m3_mu
        
        # Set data directory
        if data_dir is None:
            self.data_dir = Path(settings.BASE_DIR) / 'task_1_dataset' / 'dataset'
        else:
            self.data_dir = Path(data_dir)

        self.feature_cols = [
            "soil_humidity(%)",  # Current State
            "soil_temperature(°C)",  # Evaporation Factor
            "rain(mm/day)",  # Incoming Water
            "daily_mean_temperature(°C)",  # Heat Stress
            "irrigation_amount(m3/mu)",  # Human Action
            "days_since_irrigation",  # Time Lag
            "loc_x",
            "loc_y",  # Spatial Awareness
        ]
        self.target_col = "Target_Tomorrow_Humidity"

    def load_and_process_data(self):
        """Load and process CSV data from task_1_dataset"""
        print(" [1/5] Ingesting IoT & Weather Data...")
        try:
            # Load Raw Data
            hum = pd.read_csv(self.data_dir / "CottonSensor" / "HumiditySensor.csv")
            tem = pd.read_csv(self.data_dir / "CottonSensor" / "TemSensor.csv")
            weather = pd.read_csv(self.data_dir / "Weather" / "Weather.csv")
            mgmt = pd.read_csv(self.data_dir / "ManagementInfo.csv")
        except FileNotFoundError as e:
            print(f"Error: Missing CSV files - {e}")
            print(f"Looking in: {self.data_dir}")
            return

        # Helpers for Date Parsing
        def parse_time(s):
            return pd.to_datetime(s.astype(str), format="%Y%m%d%H%M", errors="coerce")

        def parse_date(s):
            return pd.to_datetime(s.astype(str), format="%Y%m%d", errors="coerce")

        print(" [2/5] Linking Sensors by Geo-Location...")

        # Process Humidity (Target)
        hum["ts"] = parse_time(hum["collect_time"])
        hum["date"] = hum["ts"].dt.date
        hum["loc_x"] = hum["location_info_x"].round(4)
        hum["loc_y"] = hum["location_info_y"].round(4)
        # Aggregating multiple readings per day per location
        hum_agg = (
            hum.groupby(["date", "loc_x", "loc_y"])["soil_humidity(%)"]
            .mean()
            .reset_index()
        )

        # Process Temperature (Feature)
        tem["ts"] = parse_time(tem["collect_time"])
        tem["date"] = tem["ts"].dt.date
        tem["loc_x"] = tem["location_info_x"].round(4)
        tem["loc_y"] = tem["location_info_y"].round(4)
        tem_agg = (
            tem.groupby(["date", "loc_x", "loc_y"])["soil_temperature(°C)"]
            .mean()
            .reset_index()
        )

        # Merge Sensors (Space-Time Join)
        df = pd.merge(hum_agg, tem_agg, on=["date", "loc_x", "loc_y"], how="left")
        df["date"] = pd.to_datetime(df["date"])

        # Process External Factors (Weather & Mgmt)
        weather["date"] = parse_date(weather["date"])
        w_cols = [
            "date",
            "rain(mm/day)",
            "wind(km/d)",
            "daily_mean_temperature(°C)",
            "srad(MJ/(m2*day))",
        ]

        mgmt["date"] = parse_date(mgmt["irrigation_time"])
        irr_agg = mgmt.groupby("date")["irrigation_amount(m3/mu)"].sum().reset_index()

        # Broadcast environmental data to all sensors
        df = pd.merge(df, weather[w_cols], on="date", how="left")
        df = pd.merge(df, irr_agg, on="date", how="left")

        # Cleaning & Imputation
        df["irrigation_amount(m3/mu)"] = df["irrigation_amount(m3/mu)"].fillna(0)
        df = df.ffill().bfill()  # Handle missing weather days

        # Feature Engineering: 'Days Since Last Irrigation'
        irr_dates = irr_agg[irr_agg["irrigation_amount(m3/mu)"] > 0]["date"]

        def calc_days_since(d):
            past = irr_dates[irr_dates < d]
            return (d - past.max()).days if not past.empty else -1

        # Calculate once per unique date
        unique_dates = pd.DataFrame({"date": df["date"].unique()})
        unique_dates["days_since_irrigation"] = unique_dates["date"].apply(
            calc_days_since
        )
        df = pd.merge(df, unique_dates, on="date", how="left")

        # Generate Target (Next Day's Humidity)
        df = df.sort_values(["loc_x", "loc_y", "date"])
        df["Target_Tomorrow_Humidity"] = df.groupby(["loc_x", "loc_y"])[
            "soil_humidity(%)"
        ].shift(-1)

        self.data = df.dropna()
        
        # Save processed dataset
        output_path = Path(settings.BASE_DIR) / 'agronomy' / 'data' / 'daily_dataset.parquet'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.data.to_parquet(output_path, index=False)
        
        print(f"       Dataset Built: {self.data.shape[0]} valid training samples.")
        print(f"       Saved to: {output_path}")

    def train(self):
        """Train Random Forest Regressor"""
        print(" [3/5] Training Random Forest Regressor...")

        if self.data is None:
            raise ValueError("No data loaded. Call load_and_process_data() first.")

        X = self.data[self.feature_cols]
        y = self.data[self.target_col]

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model = RandomForestRegressor(
            n_estimators=150, max_depth=15, random_state=42, n_jobs=-1
        )
        self.model.fit(self.X_train, self.y_train)
        self.preds = self.model.predict(self.X_test)
        print("       Training Complete.")

    def get_predictions_table(self):
        """
        Returns a dataframe with:
        - current features
        - model prediction for tomorrow's humidity
        - binary drought risk flag
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded.")

        df = self.data.copy()
        df["Pred_Tomorrow_Humidity"] = self.model.predict(df[self.feature_cols])
        df["Dry_Risk"] = (df["Pred_Tomorrow_Humidity"] < self.dry_threshold).astype(int)
        return df

    def add_irrigation_recommendation(self, df, target_humidity=None, max_daily_m3_mu=None):
        """
        Adds two columns:
        - Irrigation_Action: 'IRRIGATE' or 'SKIP'
        - Recommended_Irrigation_m3_mu: simple heuristic amount
        """
        if target_humidity is None:
            target_humidity = self.target_humidity
        if max_daily_m3_mu is None:
            max_daily_m3_mu = self.max_daily_m3_mu
            
        df = df.copy()
        deficit = target_humidity - df["Pred_Tomorrow_Humidity"]
        deficit = deficit.clip(lower=0)  # only positive deficit matters

        # Normalize deficit into 0..1 band, then scale to max water
        normalized = (deficit / target_humidity).clip(0, 1)
        df["Recommended_Irrigation_m3_mu"] = normalized * max_daily_m3_mu

        df["Irrigation_Action"] = np.where(
            df["Pred_Tomorrow_Humidity"] < self.dry_threshold, "IRRIGATE", "SKIP"
        )

        return df

    def simulate_future(self, base_day_df: pd.DataFrame, days_ahead: int = 1):
        """
        Multi-step simulation for ALL locations at once.

        base_day_df: rows for the last observed day (one per loc_x, loc_y)
        days_ahead:  how many days forward to simulate

        Returns: dataframe with same columns as pred_df for the future date.
        """
        if self.model is None:
            raise ValueError("Model must be trained / loaded before simulation.")

        # Copy so we don't mutate original
        df = base_day_df.copy()

        # Start from current state
        df["sim_humidity"] = df["soil_humidity(%)"]
        df["sim_days_since_irr"] = df["days_since_irrigation"]

        # Simple scenario: keep last day's weather and soil temp constant
        scenario_rain = df["rain(mm/day)"].iloc[0] if len(df) > 0 else 0
        scenario_temp = df["daily_mean_temperature(°C)"].iloc[0] if len(df) > 0 else 25
        # soil_temperature per location stays as last observed
        soil_temp_const = df["soil_temperature(°C)"].values

        for step in range(days_ahead):
            # Build features for this simulated day
            X = pd.DataFrame(
                {
                    "soil_humidity(%)": df["sim_humidity"],
                    "soil_temperature(°C)": soil_temp_const,
                    "rain(mm/day)": scenario_rain,
                    "daily_mean_temperature(°C)": scenario_temp,
                    "irrigation_amount(m3/mu)": 0.0,  # assume no irrigation actually applied in scenario
                    "days_since_irrigation": df["sim_days_since_irr"],
                    "loc_x": df["loc_x"],
                    "loc_y": df["loc_y"],
                }
            )

            # Predict humidity for "tomorrow"
            next_humidity = self.model.predict(X)

            # Update state for next loop
            df["sim_humidity"] = next_humidity
            df["sim_days_since_irr"] = df["sim_days_since_irr"] + 1

        # Build a future-day dataframe in same shape as pred_df
        future = df.copy()

        # Set the future date
        last_date = pd.to_datetime(base_day_df["date"].iloc[0]) if len(base_day_df) > 0 else pd.Timestamp.now()
        future_date = last_date + pd.Timedelta(days=days_ahead)
        future["date"] = future_date

        # Replace relevant columns with simulated values
        future["soil_humidity(%)"] = df["sim_humidity"]
        future["Target_Tomorrow_Humidity"] = df["sim_humidity"]
        future["Pred_Tomorrow_Humidity"] = df["sim_humidity"]
        future["days_since_irrigation"] = df["sim_days_since_irr"]
        future["irrigation_amount(m3/mu)"] = 0.0  # scenario: no water applied yet

        # Recompute recommendations & risk on simulated humidity
        future = self.add_irrigation_recommendation(future)

        return future

    def evaluate_and_plot(self):
        """Generate evaluation metrics and plots"""
        print(" [4/5] Generating Analytics & Plots...")

        if self.preds is None:
            raise ValueError("No predictions available. Train the model first.")

        mae = mean_absolute_error(self.y_test, self.preds)
        rmse = np.sqrt(mean_squared_error(self.y_test, self.preds))
        r2 = r2_score(self.y_test, self.preds)

        print(f"   MAE  (Mean Absolute Error): ±{mae:.2f} %")
        print(f"   RMSE (Root Mean Sq Error):  ±{rmse:.2f} %")
        print(f"   R^2   (Variance Explained):  {r2*100:.1f} %")

        # Create figures directory
        figures_dir = Path(settings.BASE_DIR) / 'agronomy' / 'figures'
        figures_dir.mkdir(parents=True, exist_ok=True)

        # Feature Importance
        plt.figure(figsize=(10, 6))
        importances = self.model.feature_importances_
        feat_names = self.X_train.columns
        indices = np.argsort(importances)[::-1]

        sns.barplot(x=importances[indices], y=feat_names[indices], palette="viridis")
        plt.title("What Drives Soil Moisture? (Feature Importance)")
        plt.xlabel("Relative Importance")
        plt.tight_layout()
        plt.savefig(figures_dir / "feature_importance.png")
        print(f"       Saved: {figures_dir / 'feature_importance.png'}")

        # Actual vs Predicted
        plt.figure(figsize=(8, 8))
        sns.scatterplot(
            x=self.y_test, y=self.preds, alpha=0.3, color="blue", edgecolor=None
        )
        plt.plot(
            [self.y_test.min(), self.y_test.max()],
            [self.y_test.min(), self.y_test.max()],
            "r--",
            lw=2,
        )
        plt.xlabel("Actual Tomorrow Humidity (%)")
        plt.ylabel("AI Predicted Humidity (%)")
        plt.title("Accuracy Check: Prediction vs Reality")
        plt.tight_layout()
        plt.savefig(figures_dir / "actual_vs_pred.png")
        print(f"       Saved: {figures_dir / 'actual_vs_pred.png'}")

        # Residuals
        plt.figure(figsize=(10, 6))
        residuals = self.y_test - self.preds
        sns.histplot(residuals, bins=50, kde=True, color="purple")
        plt.axvline(x=0, color="k", linestyle="--")
        plt.title("Error Distribution (Residuals)")
        plt.xlabel("Error (Actual - Predicted)")
        plt.tight_layout()
        plt.savefig(figures_dir / "residuals.png")
        print(f"       Saved: {figures_dir / 'residuals.png'}")

        plt.close('all')  # Clean up

    def save_model(self, filepath=None):
        """Save trained model to disk"""
        print(" [5/5] Serializing Model to Disk...")
        
        if filepath is None:
            filepath = Path(settings.BASE_DIR) / 'agronomy' / 'ml_models' / 'Irrigation_Model.pkl'
        else:
            filepath = Path(filepath)
            
        filepath.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, filepath)
        print(f"       Model Saved: {filepath}")
        
    def load_model(self, filepath=None):
        """Load trained model from disk"""
        if filepath is None:
            filepath = Path(settings.BASE_DIR) / 'agronomy' / 'ml_models' / 'Irrigation_Model.pkl'
        else:
            filepath = Path(filepath)
            
        if not filepath.exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")
            
        self.model = joblib.load(filepath)
        print(f"Model loaded from {filepath}")
        return self.model

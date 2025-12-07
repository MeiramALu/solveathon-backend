import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load raw sensor data
sensors = pd.read_csv("./CottonSensor/HumiditySensor.csv")

# Filter for a specific date to visualize (e.g., July 1st)
# Convert 'collect_time' to string -> slice YYYYMMDD -> Filter
sensors["date_str"] = sensors["collect_time"].astype(str).str[:8]
target_date = "20240701"
daily_snapshot = sensors[sensors["date_str"] == target_date]

# Aggregate mean humidity per location (Sensor X, Y)
map_data = (
    daily_snapshot.groupby(["location_info_x", "location_info_y"])["soil_humidity(%)"]
    .mean()
    .reset_index()
)

# Plot
plt.figure(figsize=(10, 6))
scatter = plt.scatter(
    map_data["location_info_x"],
    map_data["location_info_y"],
    c=map_data["soil_humidity(%)"],
    cmap="RdYlGn",
    s=100,
)
plt.colorbar(scatter, label="Soil Humidity (%)")
plt.title(f"Field Moisture Map ({target_date})")
plt.xlabel("Longitude (X)")
plt.ylabel("Latitude (Y)")
plt.grid(True)
plt.savefig("Moisture_Map.png")  # Save to view
print("Map saved as Moisture_Map.png")

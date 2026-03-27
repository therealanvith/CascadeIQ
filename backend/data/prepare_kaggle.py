import pandas as pd
from pathlib import Path

def prepare():
    df = pd.read_csv("data/vessel_delays.csv")
    
    out = pd.DataFrame({
        "speed_deviation": df["speed_deviation_kn"],
        "weather_severity": df["weather_severity"] * 10,  # scale 0-1 to 0-10
        "port_congestion": df["port_congestion_idx"] * 10,  # scale 0-1 to 0-10
        "distance_remaining": df["route_distance_nm"],
        "month": df["month"],
        "delay_hours": df["delay_hours"]
    })
    
    out.to_csv("data/training_data.csv", index=False)
    print(f"Saved {len(out)} rows to data/training_data.csv")

if __name__ == "__main__":
    prepare()
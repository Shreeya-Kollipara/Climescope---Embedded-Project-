"""
Sensor data simulation, model training, prediction and visualization for an ESP32-based IoT weather demo.
Generates weather data for Chennai (Oct 29 - Nov 11, 2025) during monsoon transition:
dramatic shift from cool/wet to hot/humid conditions, with consistently high humidity
and moderate to poor air quality. Trains a RandomForest to predict next-day averages.

Outputs:
 - sensor_data.csv
 - figures: temperature_timeseries.png, humidity_timeseries.png, aqi_timeseries.png, actual_vs_predicted.png, day8_prediction.png
 - forecast_model.pkl (optional bonus)

Run: python scripts/sensor_forecast.py

Dependencies: numpy, pandas, matplotlib, scikit-learn, joblib
If missing, install with: pip install numpy pandas matplotlib scikit-learn joblib

Author: Generated for hackathon/demo use. Tweak random seeds or parameters to change variability.
"""

import os
import sys
import math
from datetime import datetime, timedelta

# defensive imports with user-friendly message
try:
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from sklearn.model_selection import train_test_split
    import joblib
except Exception as e:
    print("Missing required Python packages. Install with: pip install numpy pandas matplotlib scikit-learn joblib")
    raise

# -------------------------
# Configuration
# -------------------------
OUT_DIR = os.path.abspath(".")  # save outputs to repo root by default
CSV_PATH = os.path.join(OUT_DIR, "sensor_data.csv")
MODEL_PATH = os.path.join(OUT_DIR, "forecast_model.pkl")
FIG_TEMPERATURE = os.path.join(OUT_DIR, "temperature_timeseries.png")
FIG_HUMIDITY = os.path.join(OUT_DIR, "humidity_timeseries.png")
FIG_AQI = os.path.join(OUT_DIR, "aqi_timeseries.png")
FIG_ACT_VS_PRED = os.path.join(OUT_DIR, "actual_vs_predicted.png")
FIG_DAY8 = os.path.join(OUT_DIR, "day8_prediction.png")

# Simulation params
START = datetime(2025, 10, 29).replace(hour=0, minute=0, second=0, microsecond=0)  # Oct 29, 2025
PERIODS_PER_MIN = 1  # not used but kept for clarity
FREQ_MIN = 5  # 5-minute intervals
DAYS = 14  # Two weeks of data
TOTAL_RECORDS = int((24 * 60 / FREQ_MIN) * DAYS)  # 2016
np.random.seed(42)

# Model params
LAG_DAYS = 3  # use past 3 days as features (you can change to 4 or 5)
TEST_SIZE = 0.2
RANDOM_STATE = 42

# -------------------------
# Helper functions
# -------------------------

def clamp(arr, low, high):
    """Clamp numpy array values to [low, high]"""
    return np.minimum(np.maximum(arr, low), high)


def generate_data(start_time=START, days=DAYS, freq_min=FREQ_MIN):
    """
    Generate time-series sensor data for DHT11-like temperature & humidity and MQ135-like AQI.
    Uses sinusoidal daily patterns plus random noise; tuned for Chennai's monsoon transition (Oct-Nov):
    - Temperature: 23.3-35.6°C with dramatic shift from cool/wet to hot/humid
    - Humidity: Very high (50-95%), especially during night/rain
    - AQI: Moderate to Poor (80-140), better during rain
    Returns DataFrame with timestamp, temperature_c, humidity_pct, aqi.
    Saves CSV to disk.
    """
    total_minutes = int(days * 24 * 60)
    periods = total_minutes // freq_min
    timestamps = [start_time + timedelta(minutes=freq_min * i) for i in range(periods)]

    # Time-of-day in radians for daily cycle (0..2pi)
    secs_in_day = 24 * 60 * 60
    t_seconds = np.array([(ts - start_time).total_seconds() for ts in timestamps])
    tod = (t_seconds % secs_in_day) / secs_in_day * 2 * np.pi
    
    # Calculate day number (0 to 13) for trending
    day_nums = t_seconds / (24 * 60 * 60)

    # Temperature: Complex pattern with dramatic shift
    # Base rises from ~27°C to ~32°C over the period
    temp_base = 27.0 + 5.0 * (1 - np.exp(-day_nums/3))  # exponential transition
    temp_amplitude = 4.5  # daily swing
    phase_shift = (14 / 24.0) * 2 * np.pi  # peak at 2 PM
    temp = temp_base + temp_amplitude * np.sin(tod - phase_shift)
    # Add afternoon heat buildup
    temp += 0.8 * np.sin(tod * 2 + 0.3)  # second harmonic
    # Add random variations
    temp += np.random.normal(scale=0.5, size=periods)
    # Initial period is cooler (monsoon influence)
    temp = clamp(temp, 23.3, 35.6)

    # Humidity: Very high, especially at night/morning
    # Base decreases slightly as temperature rises
    hum_base = 75.0 - 5.0 * (1 - np.exp(-day_nums/4))  # slight decrease trend
    hum_amplitude = 15.0
    hum_phase = (4 / 24.0) * 2 * np.pi  # peak at 4 AM
    hum = hum_base + hum_amplitude * np.sin(tod - hum_phase)
    
    # Add early morning peaks and random rain effects
    morning_boost = 10.0 * np.exp(-((tod - (5/24.0)*2*np.pi)**2)/(0.1))
    rain_effect = np.random.choice([0, 1], size=periods, p=[0.85, 0.15])  # random rain periods
    hum += morning_boost + 15.0 * rain_effect
    
    # Add noise and clamp
    hum += np.random.normal(scale=2.0, size=periods)
    # Higher humidity in first week (monsoon influence)
    hum = clamp(hum, 50, 95)

    # AQI: Moderate to Poor, improves during rain
    # Base increases as conditions get drier
    aqi_base = 90.0 + 20.0 * (1 - np.exp(-day_nums/5))
    aqi = aqi_base + 15.0 * np.sin(tod - (8 / 24.0) * 2 * np.pi)  # morning peak
    aqi += 10.0 * np.sin(tod * 2 - (17 / 24.0) * 2 * np.pi)  # evening peak
    
    # Improve AQI during rain periods
    aqi = aqi * (1.0 - 0.3 * rain_effect)  # 30% better during rain
    
    # Add random variations
    spikes = np.random.choice([0, 1], size=periods, p=[0.97, 0.03])
    spike_magnitude = np.random.normal(loc=20, scale=10, size=periods) * spikes
    aqi = aqi + spike_magnitude + np.random.normal(scale=5, size=periods)
    aqi = clamp(aqi, 80, 140)  # enforce Chennai's typical range

    df = pd.DataFrame({
        "timestamp": timestamps,
        "temperature_c": np.round(temp, 2),
        "humidity_pct": np.round(hum, 2),
        "aqi": np.round(aqi, 0).astype(int),
    })

    df.to_csv(CSV_PATH, index=False)
    print(f"Saved simulated sensor data to {CSV_PATH} ({len(df)} records)")
    return df


def feature_engineering(df):
    """
    Aggregate to daily statistics: mean, min, max for temp, humidity, AQI. Add day_number 1..7.
    Returns daily_df sorted by day_number.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["timestamp"]).dt.date
    daily = df.groupby("date").agg(
        temp_mean=("temperature_c", "mean"),
        temp_min=("temperature_c", "min"),
        temp_max=("temperature_c", "max"),
        hum_mean=("humidity_pct", "mean"),
        hum_min=("humidity_pct", "min"),
        hum_max=("humidity_pct", "max"),
        aqi_mean=("aqi", "mean"),
        aqi_min=("aqi", "min"),
        aqi_max=("aqi", "max"),
    ).reset_index()
    daily = daily.sort_values("date").reset_index(drop=True)
    daily["day_number"] = np.arange(1, len(daily) + 1)
    print("Computed daily aggregates (mean/min/max)")
    return daily


def build_lag_features(daily_df, lag_days=LAG_DAYS):
    """
    Build dataset where each sample uses the previous `lag_days` daily averages to predict the next day average values.
    Features: for each lag day, include temp_mean, hum_mean, aqi_mean with suffix _t-1, etc.
    Targets: next_day temp_mean, hum_mean, aqi_mean
    Returns X (DataFrame), y (DataFrame), and mapping of feature names.
    """
    records = []
    cols = []
    for lag in range(1, lag_days + 1):
        cols += [f"temp_mean_t-{lag}", f"hum_mean_t-{lag}", f"aqi_mean_t-{lag}"]

    for idx in range(lag_days, len(daily_df)):
        features = []
        for lag in range(1, lag_days + 1):
            row = daily_df.loc[idx - lag]
            features += [row["temp_mean"], row["hum_mean"], row["aqi_mean"]]
        target_row = daily_df.loc[idx]
        targets = [target_row["temp_mean"], target_row["hum_mean"], target_row["aqi_mean"]]
        records.append((features, targets, int(target_row["day_number"])))

    X = pd.DataFrame([r[0] for r in records], columns=cols)
    y = pd.DataFrame([r[1] for r in records], columns=["temp_mean_next", "hum_mean_next", "aqi_mean_next"])
    day_numbers = [r[2] for r in records]
    print(f"Built lag features using past {lag_days} days -> {len(X)} samples")
    return X, y, day_numbers


def train_model(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE):
    """
    Train a RandomForestRegressor to predict three targets simultaneously.
    Returns trained model, X_test, y_test, and predictions on test set.
    """
    # time-series style split: keep order, use first (1-test_size) as train
    n_samples = len(X)
    n_train = max(1, int((1 - test_size) * n_samples))
    X_train = X.iloc[:n_train]
    y_train = y.iloc[:n_train]
    X_test = X.iloc[n_train:]
    y_test = y.iloc[n_train:]

    model = RandomForestRegressor(n_estimators=200, random_state=random_state)
    model.fit(X_train, y_train.values)
    print(f"Trained RandomForest on {len(X_train)} samples; testing on {len(X_test)} samples")

    y_pred = model.predict(X_test)
    # metrics
    mae = mean_absolute_error(y_test, y_pred)
    rmse = math.sqrt(mean_squared_error(y_test, y_pred))
    print(f"Test MAE (multi-target): {mae:.3f}")
    print(f"Test RMSE (multi-target): {rmse:.3f}")

    # per-target metrics
    mae_per_target = mean_absolute_error(y_test.iloc[:, 0], y_pred[:, 0]) if len(y_test) > 0 else None
    # For multi-target, compute per-column errors if available
    per_target = {}
    if len(y_test) > 0:
        for i, name in enumerate(["temp_mean_next", "hum_mean_next", "aqi_mean_next"]):
            per_target[name] = {
                "MAE": mean_absolute_error(y_test.iloc[:, i], y_pred[:, i]),
                "RMSE": math.sqrt(mean_squared_error(y_test.iloc[:, i], y_pred[:, i]))
            }
        print("Per-target metrics:")
        for k, v in per_target.items():
            print(f"  {k}: MAE={v['MAE']:.3f}, RMSE={v['RMSE']:.3f}")

    return model, X_test, y_test, y_pred


def predict_next_day(model, daily_df, lag_days=LAG_DAYS):
    """
    Use the most recent `lag_days` of daily_df to predict the next day averages.
    Returns predicted dict with temp_mean_next, hum_mean_next, aqi_mean_next (rounded appropriately).
    """
    recent = daily_df.tail(lag_days)
    if len(recent) < lag_days:
        raise ValueError("Not enough days to build lag features for prediction")
    features = []
    for i in range(lag_days, 0, -1):  # t-1, t-2, ...
        row = recent.iloc[-i]
        features += [row["temp_mean"], row["hum_mean"], row["aqi_mean"]]
    X_pred = np.array(features).reshape(1, -1)
    y_pred = model.predict(X_pred)[0]
    pred = {
        "temperature_c": float(np.round(y_pred[0], 2)),
        "humidity_pct": float(np.round(y_pred[1], 2)),
        "aqi": int(np.round(y_pred[2]))
    }
    return pred


def rule_based_label(pred):
    """Simple rule-based label applied to predicted next-day averages."""
    temp = pred["temperature_c"]
    hum = pred["humidity_pct"]
    aqi = pred["aqi"]
    labels = []
    if temp > 32 and hum < 65:
        labels.append("Hot & Dry")
    if hum > 75:
        labels.append("Humid")
    if aqi > 110:
        labels.append("Poor Air Quality")
    if not labels:
        labels = ["Pleasant"]
    return ", ".join(labels)


def visualize_time_series(df):
    """Plot temperature, humidity, AQI time-series and save PNGs."""
    plt.style.use("seaborn-v0_8")

    # Temperature
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(pd.to_datetime(df["timestamp"]), df["temperature_c"], color="orangered", linewidth=0.8)
    ax.set_title("Temperature over 14 days")
    ax.set_ylabel("Temperature (°C)")
    fig.tight_layout()
    fig.savefig(FIG_TEMPERATURE)
    plt.close(fig)

    # Humidity
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(pd.to_datetime(df["timestamp"]), df["humidity_pct"], color="teal", linewidth=0.8)
    ax.set_title("Humidity over 14 days")
    ax.set_ylabel("Humidity (%)")
    fig.tight_layout()
    fig.savefig(FIG_HUMIDITY)
    plt.close(fig)

    # AQI
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(pd.to_datetime(df["timestamp"]), df["aqi"], color="purple", linewidth=0.8)
    ax.set_title("Air Quality Index (AQI) over 14 days")
    ax.set_ylabel("AQI")
    fig.tight_layout()
    fig.savefig(FIG_AQI)
    plt.close(fig)

    print(f"Saved figures: {FIG_TEMPERATURE}, {FIG_HUMIDITY}, {FIG_AQI}")


def plot_actual_vs_predicted(y_test, y_pred):
    """Plot actual vs predicted next-day averages (for test set) and save PNG."""
    if len(y_test) == 0:
        print("No test samples to plot actual vs predicted")
        return
    y_test_idx = list(range(len(y_test)))

    fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(14, 4))
    names = ["temp_mean_next", "hum_mean_next", "aqi_mean_next"]
    colors = ["orangered", "teal", "purple"]
    for i, ax in enumerate(axes):
        ax.plot(y_test_idx, y_test.iloc[:, i], label="Actual", marker="o", color=colors[i])
        ax.plot(y_test_idx, y_pred[:, i], label="Predicted", marker="x", linestyle="--", color="black")
        ax.set_title(names[i])
        ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_ACT_VS_PRED)
    plt.close(fig)
    print(f"Saved actual vs predicted figure: {FIG_ACT_VS_PRED}")


def plot_day8_prediction(pred):
    """Save a small bar chart for day 8 prediction."""
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = ["Temperature (°C)", "Humidity (%)", "AQI"]
    values = [pred["temperature_c"], pred["humidity_pct"], pred["aqi"]]
    colors = ["orangered", "teal", "purple"]
    ax.bar(labels, values, color=colors)
    ax.set_title("Next Day Prediction")
    for i, v in enumerate(values):
        ax.text(i, v + (0.02 * v), str(v), ha="center")
    fig.tight_layout()
    fig.savefig(FIG_DAY8)
    plt.close(fig)
    print(f"Saved next day prediction chart: {FIG_DAY8}")


# -------------------------
# Main script
# -------------------------

def main():
    # Step 1: Generate simulated sensor data
    df = generate_data()

    # Step 2: Feature engineering - daily aggregates
    daily = feature_engineering(df)
    print(daily[["day_number", "date", "temp_mean", "hum_mean", "aqi_mean"]])

    # Step 3: Build lag features using past LAG_DAYS to predict next-day averages
    X, y, day_numbers = build_lag_features(daily, lag_days=LAG_DAYS)

    # Step 4: Train model
    model, X_test, y_test, y_pred = train_model(X, y)

    # Bonus: save model
    try:
        joblib.dump(model, MODEL_PATH)
        print(f"Saved trained model to {MODEL_PATH}")
    except Exception as e:
        print(f"Could not save model: {e}")

    # Step 5: Predict next day
    pred_day8 = predict_next_day(model, daily, lag_days=LAG_DAYS)
    label = rule_based_label(pred_day8)

    # Step 6: Visualizations
    visualize_time_series(df)
    plot_actual_vs_predicted(y_test, y_pred)
    plot_day8_prediction(pred_day8)

    # Final: Print summary
    print("\nPredicted Next-Day Conditions:")
    print(f"Temperature: {pred_day8['temperature_c']} °C")
    print(f"Humidity: {pred_day8['humidity_pct']} %")
    print(f"Air Quality Index: {pred_day8['aqi']}")
    print(f"Expected Weather: {label}")


if __name__ == "__main__":
    main()
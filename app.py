from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import os
import numpy as np
import pandas as pd


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Absolute path to the model file (one level above src/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "forecast_model.pkl")
CSV_PATH = os.path.join(BASE_DIR, "sensor_data.csv")

# Try to load the trained RandomForest model
try:
    model = joblib.load(MODEL_PATH)
    print(f"✅ Loaded model from {MODEL_PATH}")
except FileNotFoundError:
    print(f"❌ Error: forecast_model.pkl not found at {MODEL_PATH}")
    model = None
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None


@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 500
    try:
        data = request.get_json(force=True)
        temperature = float(data.get('temperature'))
        humidity = float(data.get('humidity'))
        aqi = float(data.get('aqi'))

        # load last 3 days of averages
        df = pd.read_csv(CSV_PATH)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        daily = df.groupby(df["timestamp"].dt.date).agg(
            temp_mean=("temperature_c", "mean"),
            hum_mean=("humidity_pct", "mean"),
            aqi_mean=("aqi", "mean")
        ).tail(3)

        # flatten to [t-1_temp, t-1_hum, t-1_aqi, ...]
        features = []
        for _, row in daily.iterrows():
            features += [row["temp_mean"], row["hum_mean"], row["aqi_mean"]]

        # append today's live reading as the most recent point
        features += [temperature, humidity, aqi]

        X_pred = np.array(features[-9:]).reshape(1, -1)
        y_pred = model.predict(X_pred)[0]

        return jsonify({
            "next_day_predictions": {
                "temperature": round(float(y_pred[0]), 2),
                "humidity": round(float(y_pred[1]), 2),
                "aqi": round(float(y_pred[2]), 2)
            }
        })

    except Exception as e:
        return jsonify({'error': f'Prediction error: {str(e)}'}), 500


if __name__ == '__main__':
    print("🚀 Flask Weather API running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000)

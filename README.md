

# 🌿 ClimeScope: ESP32 Environmental Monitoring Dashboard


---

## 👥 **Team Members**
- **Shreeya Kollipara**
- **Saumya Agarwal**
- **Meghna Mandawra**

---

## 📌 **Project Title**
# **Real-Time IoT-Based Environmental Monitoring & Weather Prediction System**

---

## ❗ Problem Statement

There is a significant lack of **localized, real-time weather prediction systems** that rely on **live environmental sensor data**.  
Traditional weather forecasts do not utilize **on-site parameters** such as:

- 🌡️ *Temperature*  
- 💧 *Humidity*  
- 🌫️ *Air Quality*

As a result, predictions are often generalized and not tailored to local micro-climates.

---

## 🎯 **Objective**

To design and develop a **smart IoT-based weather prediction system** that:

- Uses **ESP32** to collect live environmental data  
- Integrates **DHT11** (temperature + humidity) and **MQ135** (air quality) sensors  
- Sends real-time readings to a **Flask-based Machine Learning API**  
- Predicts **next-day weather conditions**  
- Displays data and predictions on a **live visualization dashboard**

---

## 🛠️ **Technologies & Components Used**

### **Hardware**
- ESP32 Microcontroller  
- DHT11 Sensor  
- MQ135 Gas/Air Quality Sensor  

### **Software**
- Python (Flask API)  
- Machine Learning Model  
- HTML/CSS/JavaScript Dashboard  

---

## 🚀 **Key Features**

✔️ Real-time temperature monitoring  
✔️ Real-time humidity tracking  
✔️ Air quality detection (MQ135)  
✔️ REST API communication using Flask  
✔️ Next-day weather prediction using ML  
✔️ Dashboard visualization for easy monitoring  

---

## 🧠 **Why This Project?**

- To make weather forecasting **more accurate, immediate, and location-specific**  
- To demonstrate a full **IoT → API → ML → Dashboard** pipeline  
- To show how embedded systems and AI can work together for smart city solutions  

---

## ✅ **Conclusion**

This project successfully integrates:  
**IoT sensing + real-time data streaming + machine learning prediction + UI visualization**  
to create a functional, intelligent environmental monitoring system.

It proves how embedded systems and AI can be combined to build **smart, real-time predictive weather solutions.**

- Climescope---Embedded-Project/
  - README.md

  - Weather/  # ESP32 IoT Firmware (PlatformIO)
    - include/
    - lib/
    - src/
      - app.py  # API communication script
      - test_post.py  # Test POST script
    - test/
    - platformio.ini

  - ClimeScope/  # Machine Learning Forecasting System
    - scripts/
      - sensor_forecast.py
      - sensor_forecast_chennai.py
    - src/
      - app.py  # Flask API backend
      - test_post.py  # API testing client
    - ClimeScope.code-workspace
    - LICENSE
    - aqi_timeseries.png
    - day8_prediction.png
    - forecast_model.pkl  # Trained ML model
    - humidity_timeseries.png
    - sensor_data.csv
    - temperature_timeseries.png

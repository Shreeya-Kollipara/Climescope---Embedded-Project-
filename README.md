

# 🌿 ESP32 Environmental Monitoring Dashboard

This project showcases an ESP32-based IoT dashboard that monitors temperature, humidity, and air quality using the DHT11 and MQ-135 sensors. It displays live data on a web interface and an I²C-connected 16x2 LCD using a PCF8574T I/O expander.

## 🛠 Features

* 📡 WiFi-enabled ESP32 web server (auto-refreshing)
* 🌡️ Temperature & humidity readings via DHT11
* 🏭 Air quality measurement using MQ-135
* 🖥️ Real-time data on:

  * Web interface (responsive & modern design)
  * LCD (16x2 I²C module using PCF8574T)
* 🔄 Auto-refresh web page every 5 seconds

## 🔧 Hardware Components

* ESP32 Dev Board
* DHT11 Temperature & Humidity Sensor
* MQ-135 Air Quality Sensor (Analog)
* 16x2 LCD with I²C interface (based on PCF8574T, ABW958 chip)
* Breadboard + jumper wires
* USB cable (for power & serial monitoring)

## ⚙️ Wiring Guide

| Component   | ESP32 Pin        |
| ----------- | ---------------- |
| DHT11       | GPIO 4           |
| MQ-135      | GPIO 34 (Analog) |
| LCD SDA     | GPIO 21          |
| LCD SCL     | GPIO 22          |
| LCD VCC/GND | 3.3V / GND       |

💡 Ensure the I²C address for PCF8574T is 0x27 (can vary, scan with I²C scanner if unsure)

## 🚀 Getting Started

1. Open the project in Arduino IDE or PlatformIO.
2. Install the following libraries:

   * DHT sensor library (by Adafruit)
   * LiquidCrystal\_I2C (by Frank de Brabander or similar)
3. Set your WiFi credentials in the code:

   ```cpp
   const char* ssid = "Your_SSID";
   const char* password = "Your_PASSWORD";
   ```
4. Upload to ESP32 and open Serial Monitor (115200 baud).
5. Access the ESP32 IP shown in Serial Monitor from your browser.

## 🖼️ Web Interface

* Displays temperature, humidity, and raw/voltage from MQ-135.
* Classifies air quality into:

  * Excellent, Good, Fair, Poor, Very Poor
* Uses a clean responsive UI styled with Inter font.

## 📦 File Structure

```
├── src/
│   └── main.ino
├── README.md
```

## Pin Connections

| Component | ESP32 Pin | Description |
|-----------|-----------|-------------|
| DHT11     | GPIO 4    | Temperature and humidity sensor |
| MQ135     | GPIO 34   | Air quality sensor (analog input) |

## Sensor Details:

1. **DHT11 Temperature and Humidity Sensor**
   - Connected to GPIO 4
   - Uses the DHT library
   - Provides temperature (°C) and relative humidity (%)

2. **MQ135 Air Quality Sensor**
   - Connected to GPIO 34 (Analog input)
   - Measures air quality (raw values)
   - Voltage output: 0-3.3V (mapped from 0-4095)
   - Air quality interpretation:
     - < 150: Excellent
     - 150-299: Good
     - 300-449: Fair
     - 450-599: Poor
     - ≥ 600: Very Poor

## 📜 License

MIT License. Feel free to use, modify, and share.

---

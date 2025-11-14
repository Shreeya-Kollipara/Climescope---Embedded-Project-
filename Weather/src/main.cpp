#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"

#define DHTPIN 4
#define DHTTYPE DHT11
#define MQ135PIN 34

// API endpoint configuration
const char* API_ENDPOINT = "http://10.38.192.228:5000/predict";
const unsigned long API_INTERVAL = 60000; // Send data every 60 seconds

DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "vivo Y02t";
const char* password = "sakethwaste";

WiFiServer server(80);

// Global variables to store predictions
float predictedAQI = 0;
float predictedHumidity = 0;
float predictedTemperature = 0;
bool predictionAvailable = false;

void connectToWiFi() {
  Serial.printf("Connecting to WiFi SSID: %s\n", ssid);
  WiFi.begin(ssid, password);

  int retryCount = 0;
  while (WiFi.status() != WL_CONNECTED && retryCount < 20) {
    delay(1000);
    Serial.print(".");
    retryCount++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected.");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    server.begin();
  } else {
    Serial.println("\nFailed to connect to WiFi.");
  }
}

const char* interpretAirQuality(float raw) {
  if (raw < 150) return "Excellent";
  else if (raw < 300) return "Good";
  else if (raw < 450) return "Fair";
  else if (raw < 600) return "Poor";
  else return "Very Poor";
}

void handleClient(WiFiClient &client) {
  Serial.println("New client connected");

  String request = "";
  unsigned long timeout = millis() + 2000;

  while (client.connected() && millis() < timeout) {
    while (client.available()) {
      char c = client.read();
      request += c;
      if (request.endsWith("\r\n\r\n")) {
        timeout = 0;
        break;
      }
    }
    delay(1);
  }

  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  int mq135Raw = analogRead(MQ135PIN);
  float mq135Voltage = mq135Raw * (3.3 / 4095.0);
  

  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Failed to read from DHT sensor!");
    humidity = 0;
    temperature = 0;
  }

  Serial.printf("Temperature: %.1f °C, Humidity: %.1f %%\n", temperature, humidity);
  Serial.printf("MQ-135 Raw: %d, Voltage: %.2f V\n", mq135Raw, mq135Voltage);

  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: text/html; charset=UTF-8");
  client.println("Connection: close");
  client.println();

  client.println(R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta http-equiv="refresh" content="5" />
<title>ESP32 Environmental Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --bg-light: #fdf6e3;
  --bg-dark: #2b2a28;
  --card-light: rgba(255, 255, 240, 0.95);
  --card-dark: rgba(44, 38, 32, 0.85);
  --prediction-light: rgba(230, 245, 255, 0.95);
  --prediction-dark: rgba(32, 44, 52, 0.85);
  --text-light: #222;
  --text-dark: #eee;
  --accent-light: #6b8e23;
  --accent-dark: #a1c181;
  --prediction-accent-light: #2196F3;
  --prediction-accent-dark: #64B5F6;
  --border-color-light: #d2c1a3;
  --border-color-dark: #5a5045;
}

html, body {
  margin: 0;
  padding: 0;
  font-family: 'Poppins', sans-serif;
  transition: background 0.5s, color 0.5s;
}

body.light {
  background: var(--bg-light);
  color: var(--text-light);
}

body.dark {
  background: var(--bg-dark);
  color: var(--text-dark);
}

header {
  text-align: center;
  padding: 30px 40px 10px 40px;
  position: relative;
}

.toggle-wrapper {
  position: absolute;
  top: 30px;
  right: 40px;
}

.logo-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 5px;
}

.logo {
  font-size: 2.5rem;
}

h1 {
  font-weight: 700;
  font-size: 2rem;
  margin: 0;
  background: linear-gradient(90deg, var(--accent-light), #556b2f);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  font-size: 0.95rem;
  opacity: 0.8;
  margin-top: 8px;
  font-weight: 400;
}

.toggle-btn {
  padding: 10px 24px;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  background: var(--accent-light);
  color: #fff;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.toggle-btn:hover {
  background: #556b2f;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.25);
}

.section-title {
  text-align: center;
  font-size: 1.5rem;
  font-weight: 700;
  margin: 30px 0 10px 0;
  color: var(--accent-light);
}

body.dark .section-title {
  color: var(--accent-dark);
}

.section-subtitle {
  text-align: center;
  font-size: 0.9rem;
  opacity: 0.7;
  margin-bottom: 20px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 32px;
  padding: 20px 40px;
  max-width: 1100px;
  margin: auto;
}

.card {
  padding: 24px 28px;
  border-radius: 16px;
  backdrop-filter: blur(8px);
  box-shadow: 0 6px 18px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  border: 1.5px solid var(--border-color-light);
  transition: transform 0.3s, box-shadow 0.3s;
  background: var(--card-light);
}

body.dark .card {
  background: var(--card-dark);
  border-color: var(--border-color-dark);
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 25px rgba(0,0,0,0.25);
}

.card.prediction {
  background: var(--prediction-light);
  border-color: var(--prediction-accent-light);
}

body.dark .card.prediction {
  background: var(--prediction-dark);
  border-color: var(--prediction-accent-dark);
}

.label {
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 8px;
}

.prediction-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 8px;
  background: var(--prediction-accent-light);
  color: white;
}

body.dark .prediction-badge {
  background: var(--prediction-accent-dark);
}

.value {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 6px;
}

.interpretation {
  font-size: 1rem;
  font-weight: 600;
  color: var(--accent-light);
}

body.dark .interpretation {
  color: var(--accent-dark);
}

.card.prediction .interpretation {
  color: var(--prediction-accent-light);
}

body.dark .card.prediction .interpretation {
  color: var(--prediction-accent-dark);
}

.info-section {
  max-width: 1100px;
  margin: 20px auto;
  padding: 20px 25px;
  border-radius: 16px;
  backdrop-filter: blur(8px);
  border: 1.5px solid var(--border-color-light);
  background: var(--card-light);
}

body.dark .info-section {
  background: rgba(44, 38, 32, 0.85);
  border-color: var(--border-color-dark);
}

.info-section h2 {
  font-weight: 700;
  margin-top: 0;
  color: var(--accent-light);
}

body.dark .info-section h2 {
  color: var(--accent-dark);
}

.info-section ul {
  padding-left: 20px;
  line-height: 1.8;
}

footer {
  text-align: center;
  padding: 25px 20px;
  font-size: 0.9rem;
  opacity: 0.7;
}

.no-prediction {
  font-size: 0.9rem;
  opacity: 0.7;
  font-style: italic;
}

@media (max-width: 768px) {
  header {
    padding: 20px;
  }
  
  .toggle-wrapper {
    position: static;
    margin-top: 15px;
  }
  
  .grid {
    padding: 20px;
  }
}
</style>
</head>
<body class="light">
<header>
  <div class="logo-title">
    <span class="logo">🌿</span>
    <h1>ClimeScope</h1>
  </div>
  <div class="subtitle">ESP32 Environmental Monitoring Dashboard with AI Predictions</div>
  <div class="toggle-wrapper">
    <button class="toggle-btn" onclick="toggleMode()">🌙 Toggle Dark/Light</button>
  </div>
</header>

<div class="section-title">📊 Current Readings</div>
<div class="section-subtitle">Real-time sensor data</div>

<div class="grid">
  <div class="card">
    <div class="label">Temperature</div>
    <div class="value">)rawliteral");

  client.printf("%.1f &deg;C", temperature);

  client.println(R"rawliteral(
    </div>
  </div>

  <div class="card">
    <div class="label">Humidity</div>
    <div class="value">)rawliteral");

  client.printf("%.1f %%", humidity);

  client.println(R"rawliteral(
    </div>
  </div>

  <div class="card">
    <div class="label">Air Quality (MQ-135)</div>
    <div class="value">)rawliteral");

  client.printf("%d<br><span style='font-size:1rem;'>%.2f V</span>", mq135Raw, mq135Voltage);

  client.println(R"rawliteral(
    </div>
    <div class="interpretation">)rawliteral");

  client.print(interpretAirQuality(mq135Raw));

  client.println(R"rawliteral(
    </div>
  </div>
</div>

<div class="section-title">🔮 Next Day Predictions</div>
<div class="section-subtitle">AI model predictions (updates every 60 seconds)</div>

<div class="grid">)rawliteral");

  if (predictionAvailable) {
    // Temperature prediction
    client.println(R"rawliteral(
  <div class="card prediction">
    <div class="prediction-badge">🤖 AI PREDICTED</div>
    <div class="label">Temperature</div>
    <div class="value">)rawliteral");
    
    client.printf("%.2f &deg;C", predictedTemperature);
    
    client.println(R"rawliteral(
    </div>
  </div>

  <div class="card prediction">
    <div class="prediction-badge">🤖 AI PREDICTED</div>
    <div class="label">Humidity</div>
    <div class="value">)rawliteral");
    
    client.printf("%.2f %%", predictedHumidity);
    
    client.println(R"rawliteral(
    </div>
  </div>

  <div class="card prediction">
    <div class="prediction-badge">🤖 AI PREDICTED</div>
    <div class="label">Air Quality Index</div>
    <div class="value">)rawliteral");
    
    client.printf("%.2f", predictedAQI);
    
    client.println(R"rawliteral(
    </div>
    <div class="interpretation">)rawliteral");
    
    client.print(interpretAirQuality(predictedAQI));
    
    client.println(R"rawliteral(
    </div>
  </div>)rawliteral");
  } else {
    client.println(R"rawliteral(
  <div class="card prediction">
    <div class="label">⏳ Predictions Loading...</div>
    <div class="no-prediction">Waiting for first prediction cycle<br>(Model updates every 60 seconds)</div>
  </div>)rawliteral");
  }

  client.println(R"rawliteral(
</div>

<div class="info-section">
  <h2>Project Details</h2>
  <p>This ESP32-based IoT dashboard monitors environmental data using DHT11 (Temperature & Humidity) and MQ-135 (Air Quality) sensors. Real-time data is displayed alongside AI-powered predictions for the next day, updated every minute.</p>
  <h2>Hardware Components</h2>
  <ul>
    <li>ESP32 Dev Board</li>
    <li>DHT11 Temperature & Humidity Sensor (GPIO 4)</li>
    <li>MQ-135 Air Quality Sensor (Analog GPIO 34)</li>
    <li>16x2 LCD with I²C interface (PCF8574T, SDA GPIO 21, SCL GPIO 22)</li>
    <li>Breadboard + jumper wires</li>
    <li>USB cable</li>
  </ul>
  <h2>Air Quality Interpretation (MQ-135)</h2>
  <ul>
    <li>&lt; 150 : Excellent</li>
    <li>150–299 : Good</li>
    <li>300–449 : Fair</li>
    <li>450–599 : Poor</li>
    <li>≥ 600 : Very Poor</li>
  </ul>
  <h2>Features</h2>
  <ul>
    <li>WiFi-enabled ESP32 web server (auto-refresh every 5 seconds)</li>
    <li>AI-powered next day predictions (updated every 60 seconds)</li>
    <li>Responsive & modern UI with dark/light mode</li>
    <li>Optional 16x2 I²C LCD display</li>
    <li>Real-time temperature, humidity, and air quality readings</li>
  </ul>
</div>

<footer>Page refreshes every 5 seconds | Predictions update every 60 seconds | MIT License | Designed by ClimeScope</footer>

<script>
function toggleMode() {
  const body = document.body;
  const btn = document.querySelector('.toggle-btn');
  
  if (body.classList.contains('light')) {
    body.classList.remove('light');
    body.classList.add('dark');
    btn.textContent = '☀ Toggle Dark/Light';
  } else {
    body.classList.remove('dark');
    body.classList.add('light');
    btn.textContent = '🌙 Toggle Dark/Light';
  }
}
</script>
</body>
</html>
)rawliteral");

  delay(1);
  client.stop();
  Serial.println("Client disconnected");
}

// Function to send sensor data to API and get predictions
void getPredictions() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected. Skipping prediction request.");
    return;
  }

  HTTPClient http;
  http.begin(API_ENDPOINT);
  http.addHeader("Content-Type", "application/json");

  // Read current sensor values
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  int mq135Raw = analogRead(MQ135PIN);

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Failed to read from DHT sensor! Skipping prediction request.");
    http.end();
    return;
  }

  // Prepare JSON payload
  char jsonBuffer[128];
  snprintf(jsonBuffer, sizeof(jsonBuffer),
           "{\"temperature\": %.2f, \"humidity\": %.2f, \"aqi\": %d}",
           temperature, humidity, mq135Raw);

  // Send POST request
  int httpResponseCode = http.POST(jsonBuffer);

  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("\n--- Prediction Results ---");
    Serial.println(response);
    Serial.println("------------------------");
    
    // Simple string parsing for JSON response
    // Expected format: {"next_day_predictions":{"aqi":104.18,"humidity":73.21,"temperature":31.71}}
    
    // First, find the "next_day_predictions" object
    int predStart = response.indexOf("\"next_day_predictions\":");
    if (predStart != -1) {
      // Get the substring starting from predictions object
      String predSection = response.substring(predStart);
      
      // Now find values within this section
      int aqiIndex = predSection.indexOf("\"aqi\":");
      int humidityIndex = predSection.indexOf("\"humidity\":");
      int temperatureIndex = predSection.indexOf("\"temperature\":");
      
      if (aqiIndex != -1 && humidityIndex != -1 && temperatureIndex != -1) {
        // Extract AQI value
        int aqiStart = aqiIndex + 6;
        int aqiEnd = predSection.indexOf(",", aqiStart);
        if (aqiEnd == -1) aqiEnd = predSection.indexOf("}", aqiStart);
        String aqiStr = predSection.substring(aqiStart, aqiEnd);
        aqiStr.trim();
        predictedAQI = aqiStr.toFloat();
        
        // Extract Humidity value
        int humStart = humidityIndex + 11;
        int humEnd = predSection.indexOf(",", humStart);
        if (humEnd == -1) humEnd = predSection.indexOf("}", humStart);
        String humStr = predSection.substring(humStart, humEnd);
        humStr.trim();
        predictedHumidity = humStr.toFloat();
        
        // Extract Temperature value
        int tempStart = temperatureIndex + 14;
        int tempEnd = predSection.indexOf("}", tempStart);
        if (tempEnd == -1) tempEnd = predSection.indexOf(",", tempStart);
        String tempStr = predSection.substring(tempStart, tempEnd);
        tempStr.trim();
        predictedTemperature = tempStr.toFloat();
        
        predictionAvailable = true;
        
        Serial.println("Predictions parsed successfully:");
        Serial.printf("  Predicted Temperature: %.2f °C\n", predictedTemperature);
        Serial.printf("  Predicted Humidity: %.2f %%\n", predictedHumidity);
        Serial.printf("  Predicted AQI: %.2f\n", predictedAQI);
        Serial.println("Raw extracted strings:");
        Serial.printf("  AQI string: '%s'\n", aqiStr.c_str());
        Serial.printf("  Humidity string: '%s'\n", humStr.c_str());
        Serial.printf("  Temperature string: '%s'\n", tempStr.c_str());
      } else {
        Serial.println("Failed to find prediction fields in response");
      }
    } else {
      Serial.println("Failed to find 'next_day_predictions' in response");
    }
  } else {
    Serial.printf("Error on sending POST: %s\n", http.errorToString(httpResponseCode).c_str());
  }

  http.end();
}

void setup() {
  Serial.begin(115200);

  Serial.println("Initializing sensors...");
  dht.begin();
  delay(2000); // Allow sensors to stabilize

  float initHumidity = dht.readHumidity();
  float initTemp = dht.readTemperature();
  if (!isnan(initHumidity) && !isnan(initTemp)) {
    Serial.printf("Initial Temperature: %.1f °C\n", initTemp);
    Serial.printf("Initial Humidity: %.1f %%\n", initHumidity);
  } else {
    Serial.println("Initial sensor read failed.");
  }

  connectToWiFi();
  getPredictions();
}

void loop() {
  static unsigned long lastPredictionTime = 0;
  unsigned long currentMillis = millis();

  // Handle web client requests
  WiFiClient client = server.available();
  if (client) {
    handleClient(client);
  }

  // Get predictions every API_INTERVAL milliseconds
  if (currentMillis - lastPredictionTime >= API_INTERVAL) {
    getPredictions();
    lastPredictionTime = currentMillis;
  }
}
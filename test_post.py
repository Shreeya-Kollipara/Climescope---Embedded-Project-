import requests

resp = requests.post(
    "http://localhost:5000/predict",
    json={"temperature": 28.5, "humidity": 65.0, "aqi": 150.0}
)
print(resp.status_code)
print(resp.text)

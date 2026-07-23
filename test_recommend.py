import requests

res = requests.get("http://localhost:5000/recommend?season=Rabi&state=Punjab&lang=en")
try:
    data = res.json()
    print("Found", len(data), "crops")
    for crop in data:
        print(crop, data[crop]["score"])
except Exception as e:
    print(res.status_code, res.text)

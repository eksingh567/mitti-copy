import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# Fix layout html for weather
app_py = app_py.replace('Weather: 24°C | 60% Humidity', 'Weather: {{ data.temp }}°C | {{ data.humidity }}% Humidity')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)
    
print("Successfully replaced HTML weather in layout")

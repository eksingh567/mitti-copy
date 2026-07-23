import re

with open('app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Add cache buster to fetchDashboardData
js = js.replace('await fetch(${API_URL}/?state=);', 'await fetch(${API_URL}/?state=&t=);')

# Add cache buster to loadRecommendations
js = js.replace('await fetch(${API_URL}/recommend?season=&state=);', 'await fetch(${API_URL}/recommend?season=&state=&t=);')

with open('app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Added cache busting to app.js")

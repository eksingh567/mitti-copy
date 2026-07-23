import re

with open('app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Update fetchDashboardData
js = js.replace('await fetch(${API_URL}/?state=&t=);', 'await fetch(${API_URL}/?state=&lang=&t=);')

# Update loadRecommendations
js = js.replace('await fetch(${API_URL}/recommend?season=&state=&t=);', 'await fetch(${API_URL}/recommend?season=&state=&lang=&t=);')

# Update loadEncyclopedia
js = js.replace('await fetch(${API_URL}/crops);', 'await fetch(${API_URL}/crops);') # crops endpoint doesn't strictly need it unless we translated it, but wait! The crops names are already hi/en in the json

# Make sure setNativeLanguage triggers a re-fetch!
js = js.replace('if(Object.keys(currentRecommendations).length > 0) {\n        renderCropsGrid(currentRecommendations);\n        const activeBtn = document.querySelector(\'.crop-btn.active\');\n        if(activeBtn) {\n            const cropKey = activeBtn.id.replace(\'btn-\', \'\');\n            selectCrop(cropKey);\n        }\n    }', 'fetchDashboardData();')

with open('app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated app.js to send lang parameter and re-fetch on language change")

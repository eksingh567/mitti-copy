import re

with open('frontend/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Inside loadRecommendations, update the Active Soil Profile text
target_string = "const res = await fetch(`${API_URL}/recommend?season=${season}&state=${state}&soil=${soil}&water=${water}&type=${type}&lang=${currentLang}&t=${Date.now()}`);"

injection = """
        // Update the Active Soil Profile text based on the override
        const soilDisplay = document.getElementById('soilProfileName');
        if (soil !== 'Auto') {
            soilDisplay.innerHTML = `<span style="color: #fbbf24;">${soil} (Override)</span>`;
        } else {
            // If set back to Auto, we should re-fetch the real sensor data to update the display
            fetch(`${API_URL}/?state=${state}&lang=${currentLang}&t=${Date.now()}`)
                .then(r => r.json())
                .then(data => {
                    soilDisplay.innerText = data.soil_profile || "Unknown";
                });
        }
        
        const res = await fetch(`${API_URL}/recommend?season=${season}&state=${state}&soil=${soil}&water=${water}&type=${type}&lang=${currentLang}&t=${Date.now()}`);
"""

js = js.replace(target_string, injection)

with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated app.js to reflect soil override in the UI!")

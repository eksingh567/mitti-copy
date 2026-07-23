import re

with open('frontend/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Add DOM element reference
dom_refs_old = """const waterSelect = document.getElementById('waterSelect');
const typeSelect = document.getElementById('typeSelect');"""

dom_refs_new = """const waterSelect = document.getElementById('waterSelect');
const typeSelect = document.getElementById('typeSelect');
const phenomenonSelect = document.getElementById('phenomenonSelect');"""

js = js.replace(dom_refs_old, dom_refs_new)

# 2. Update fetch logic
fetch_old = """        const type = typeSelect ? typeSelect.value : 'Any';
        
        const res = await fetch(`${API_URL}/recommend?season=${season}&state=${state}&soil=${soil}&water=${water}&type=${type}&lang=${currentLang}&t=${Date.now()}`);"""

fetch_new = """        const type = typeSelect ? typeSelect.value : 'Any';
        const phenomenon = phenomenonSelect ? phenomenonSelect.value : 'None';
        
        const res = await fetch(`${API_URL}/recommend?season=${season}&state=${state}&soil=${soil}&water=${water}&type=${type}&phenomenon=${phenomenon}&lang=${currentLang}&t=${Date.now()}`);"""

js = js.replace(fetch_old, fetch_new)

# 3. Add event listener
listeners_old = """if (waterSelect) waterSelect.addEventListener('change', loadRecommendations);
if (typeSelect) typeSelect.addEventListener('change', loadRecommendations);"""

listeners_new = """if (waterSelect) waterSelect.addEventListener('change', loadRecommendations);
if (typeSelect) typeSelect.addEventListener('change', loadRecommendations);
if (phenomenonSelect) phenomenonSelect.addEventListener('change', loadRecommendations);"""

js = js.replace(listeners_old, listeners_new)

with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated app.js to support the phenomenon filter!")

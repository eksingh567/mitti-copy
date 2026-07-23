import re

with open('frontend/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Add DOM element references
dom_refs = """const stateSelect = document.getElementById('stateSelect');
const seasonSelect = document.getElementById('seasonSelect');
const soilSelect = document.getElementById('soilSelect');
const waterSelect = document.getElementById('waterSelect');
const typeSelect = document.getElementById('typeSelect');
"""
js = re.sub(r'const stateSelect.*?;.*?const seasonSelect.*?;', dom_refs, js, flags=re.DOTALL)

# 2. Update loadRecommendations to use the new filters
old_load = "const res = await fetch(`${API_URL}/recommend?season=${season}&state=${state}&lang=${currentLang}&t=${Date.now()}`);"
new_load = """
        const soil = soilSelect ? soilSelect.value : 'Auto';
        const water = waterSelect ? waterSelect.value : 'Any';
        const type = typeSelect ? typeSelect.value : 'Any';
        
        const res = await fetch(`${API_URL}/recommend?season=${season}&state=${state}&soil=${soil}&water=${water}&type=${type}&lang=${currentLang}&t=${Date.now()}`);
"""
js = js.replace(old_load, new_load)

# 3. Add event listeners to the new dropdowns
listeners = """seasonSelect.addEventListener('change', loadRecommendations);
if (soilSelect) soilSelect.addEventListener('change', loadRecommendations);
if (waterSelect) waterSelect.addEventListener('change', loadRecommendations);
if (typeSelect) typeSelect.addEventListener('change', loadRecommendations);
"""
js = js.replace("seasonSelect.addEventListener('change', loadRecommendations);", listeners)

with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated app.js to use the new multi-filters!")

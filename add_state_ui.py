import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# Extract STATE_TO_REGION logic
import json
# We will use the python dictionaries to generate HTML options
STATE_TO_REGION = {
    "Punjab": "North", "Haryana": "North", "Himachal Pradesh": "North", "Uttarakhand": "North",
    "Uttar Pradesh": "North", "Delhi": "North", "Jammu & Kashmir": "North", "Ladakh": "North",
    "Chandigarh": "North",
    "Rajasthan": "West", "Gujarat": "West", "Maharashtra": "West", "Goa": "West",
    "Dadra & Nagar Haveli and Daman & Diu": "West",
    "Madhya Pradesh": "Central", "Chhattisgarh": "Central",
    "Bihar": "East", "Jharkhand": "East", "West Bengal": "East", "Odisha": "East",
    "Andhra Pradesh": "South", "Karnataka": "South", "Kerala": "South", "Tamil Nadu": "South",
    "Telangana": "South", "Puducherry": "South", "Andaman & Nicobar Islands": "South",
    "Lakshadweep": "South",
    "Assam": "Northeast", "Arunachal Pradesh": "Northeast", "Manipur": "Northeast",
    "Meghalaya": "Northeast", "Mizoram": "Northeast", "Nagaland": "Northeast",
    "Tripura": "Northeast", "Sikkim": "Northeast"
}

state_options = ""
for state, region in STATE_TO_REGION.items():
    selected = ' selected' if state == 'Rajasthan' else ''
    state_options += f'<option value="{state}" data-region="{region}"{selected}>{state}</option>\n            '

# Replace HTML to include state dropdown
old_region_html = '''        <!-- Region Selector -->
        <div>
          <span style="font-size: 0.75rem; color: #558b2f; margin-right: 0.25rem; font-weight: bold; text-transform: uppercase;">Region:</span>
          <select id="regionSelect" onchange="loadRecommendations()" class="filter-select">
            <option value="North" selected>North India</option>
            <option value="South">South India</option>
            <option value="East">East India</option>
            <option value="West">West India</option>
            <option value="Central">Central India</option>
            <option value="Northeast">Northeast India</option>
          </select>
        </div>'''

new_region_html = f'''        <!-- State Selector -->
        <div>
          <span style="font-size: 0.75rem; color: #558b2f; margin-right: 0.25rem; font-weight: bold; text-transform: uppercase;">State:</span>
          <select id="stateSelect" onchange="updateRegionAndLoad()" class="filter-select" style="max-width: 150px;">
            {state_options}
          </select>
        </div>
        <!-- Region Selector (Auto-updated but overridable) -->
        <div>
          <span style="font-size: 0.75rem; color: #558b2f; margin-right: 0.25rem; font-weight: bold; text-transform: uppercase;">Region:</span>
          <select id="regionSelect" onchange="loadRecommendations()" class="filter-select">
            <option value="North">North India</option>
            <option value="South">South India</option>
            <option value="East">East India</option>
            <option value="West" selected>West India</option>
            <option value="Central">Central India</option>
            <option value="Northeast">Northeast India</option>
          </select>
        </div>'''

app_py = app_py.replace(old_region_html, new_region_html)

# Also fallback if the previous block doesn't match perfectly because of missing Central/Northeast options
if new_region_html not in app_py:
    old_region_html_fallback = '''        <!-- Region Selector -->
        <div>
          <span style="font-size: 0.75rem; color: #558b2f; margin-right: 0.25rem; font-weight: bold; text-transform: uppercase;">Region:</span>
          <select id="regionSelect" onchange="loadRecommendations()" class="filter-select">
            <option value="North" selected>North India</option>
            <option value="South">South India</option>
            <option value="East">East India</option>
            <option value="West">West India</option>
          </select>
        </div>'''
    app_py = app_py.replace(old_region_html_fallback, new_region_html)

# Update Javascript
old_js = '''  function loadRecommendations() {
    const season = document.getElementById('seasonSelect').value;
    const region = document.getElementById('regionSelect').value;
    
    fetch(/recommend?season=&region=)'''

new_js = '''  function updateRegionAndLoad() {
    const stateSelect = document.getElementById('stateSelect');
    const selectedOption = stateSelect.options[stateSelect.selectedIndex];
    const region = selectedOption.getAttribute('data-region');
    document.getElementById('regionSelect').value = region;
    loadRecommendations();
  }

  function loadRecommendations() {
    const season = document.getElementById('seasonSelect').value;
    const region = document.getElementById('regionSelect').value;
    const state = document.getElementById('stateSelect').value;
    
    fetch(/recommend?season=&region=&state=)'''

app_py = app_py.replace(old_js, new_js)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Injected state dropdown")

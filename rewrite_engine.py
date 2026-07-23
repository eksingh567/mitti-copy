import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# 1. Replace STATE_TO_REGION
new_state_to_region = """STATE_TO_REGION = {
    # NORTH
    "Jammu & Kashmir": "North", "Ladakh": "North", "Himachal Pradesh": "North", 
    "Punjab": "North", "Chandigarh": "North", "Uttarakhand": "North", 
    "Haryana": "North", "Delhi": "North", "Uttar Pradesh": "North", 
    "Madhya Pradesh": "North", "Chhattisgarh": "North",
    # WEST
    "Rajasthan": "West", "Gujarat": "West", "Maharashtra": "West", 
    "Goa": "West", "Dadra & Nagar Haveli and Daman & Diu": "West",
    # SOUTH
    "Karnataka": "South", "Kerala": "South", "Lakshadweep": "South", 
    "Tamil Nadu": "South", "Puducherry": "South", "Andhra Pradesh": "South", 
    "Telangana": "South", "Andaman & Nicobar Islands": "South",
    # EAST
    "Bihar": "East", "Jharkhand": "East", "Odisha": "East", "West Bengal": "East", 
    "Sikkim": "East", "Assam": "East", "Arunachal Pradesh": "East", 
    "Nagaland": "East", "Manipur": "East", "Mizoram": "East", 
    "Tripura": "East", "Meghalaya": "East"
}"""

app_py = re.sub(r'STATE_TO_REGION = \{.*?\}', new_state_to_region, app_py, flags=re.DOTALL)

# 2. Fix crop_profiles regions
# We need to map "Central" -> "North" or "West"
# Let's just strip "Central" and "Northeast" and ensure they are covered by the 4 main ones.
def fix_regions(match):
    regions_str = match.group(1)
    # Parse the list
    regions = eval('[' + regions_str + ']')
    new_regions = set(regions)
    if "Central" in new_regions:
        new_regions.remove("Central")
        new_regions.add("North")
        new_regions.add("West")
    if "Northeast" in new_regions:
        new_regions.remove("Northeast")
        new_regions.add("East")
    
    # Format back to string
    new_list_str = ", ".join([f'"{r}"' for r in sorted(list(new_regions))])
    return f'"regions": [{new_list_str}]'

app_py = re.sub(r'"regions": \[(.*?)\]', fix_regions, app_py)

# 3. Rewrite the recommend endpoint
new_recommend = """@app.route("/recommend")
def recommend():
    season = request.args.get("season", "Rabi")
    state = request.args.get("state", "Rajasthan")
    region = STATE_TO_REGION.get(state, "North")
    lang = request.args.get("lang", "en")
    
    results = {}
    for crop in crop_profiles.keys():
        score, details = calculate_suitability(crop, latest, season, region, state=state, lang=lang)
        if isinstance(details, dict):
            # Strict season filtering: only suggest crops for the selected season
            if crop_profiles[crop].get("season") == season:
                # Add a boost if it matches the region perfectly
                if region in crop_profiles[crop].get("regions", []):
                    score = min(100, score + 10)
                
                details["score"] = score
                # Only return crops that are somewhat viable (> 40%)
                if score >= 40:
                    results[crop] = details
                
    # If filter is too strict (e.g. bad soil), return at least something in season
    if not results:
        for crop in crop_profiles.keys():
            if crop_profiles[crop].get("season") == season:
                score, details = calculate_suitability(crop, latest, season, region, state=state, lang=lang)
                details["score"] = score
                results[crop] = details
                
    return jsonify(results)"""

app_py = re.sub(r'@app\.route\("/recommend"\).*?return jsonify\(results\)', new_recommend, app_py, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Engine completely rewritten to 4 regions!")

import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# 1. Inject the 2D Array generation
array_code = """
# ==========================================
# 2D ARRAY: STATE -> SEASON -> CROPS
# ==========================================
STATE_SEASON_CROP_MAP = {}
for _s in STATE_TO_REGION.keys():
    STATE_SEASON_CROP_MAP[_s] = {"Kharif": [], "Rabi": [], "Zaid": []}
    _r = STATE_TO_REGION[_s]
    for _c, _p in crop_profiles.items():
        if _r in _p.get("regions", []):
            _szn = _p.get("season")
            if _szn in STATE_SEASON_CROP_MAP[_s]:
                STATE_SEASON_CROP_MAP[_s][_szn].append(_c)
"""

if "STATE_SEASON_CROP_MAP = {}" not in app_py:
    # Insert it right before def calculate_suitability
    app_py = app_py.replace("def calculate_suitability", array_code + "\ndef calculate_suitability")

# 2. Rewrite recommend endpoint
new_recommend = """@app.route("/recommend")
def recommend():
    season = request.args.get("season", "Rabi")
    state = request.args.get("state", "Rajasthan")
    region = STATE_TO_REGION.get(state, "North")
    lang = request.args.get("lang", "en")
    
    # 1. EASY ACCESS VIA 2D ARRAY
    valid_crops = STATE_SEASON_CROP_MAP.get(state, {}).get(season, [])
    
    # If the 2D array has nothing, fallback to all crops in that season
    if not valid_crops:
        valid_crops = [c for c, p in crop_profiles.items() if p.get("season") == season]
        
    results = {}
    for crop in valid_crops:
        # 2. ADD SOIL FEATURE AND EVERYTHING INTO CONSIDERATION
        score, details = calculate_suitability(crop, latest, season, region, state=state, lang=lang)
        
        # We start with a baseline score of 100 for being in the correct State and Season,
        # then we subtract penalties strictly based on SOIL conditions (N, P, K, pH, Moisture)
        
        # Let's dynamically calculate the soil penalty
        soil_penalty = 0
        profile = crop_profiles[crop]
        
        # Moisture check
        if latest["moisture"] > 0: # Only penalize if sensor is actually active
            if latest["moisture"] < profile["moisture"][0]: soil_penalty += 15
            elif latest["moisture"] > profile["moisture"][1]: soil_penalty += 15
            
        # pH check
        if latest["ph"] < profile["ph"][0] or latest["ph"] > profile["ph"][1]:
            soil_penalty += 15
            
        # NPK checks
        if latest["n"] > 0 and latest["n"] < profile["n"][0]: soil_penalty += 10
        if latest["p"] > 0 and latest["p"] < profile["p"][0]: soil_penalty += 10
        if latest["k"] > 0 and latest["k"] < profile["k"][0]: soil_penalty += 10
        
        # Soil Type Check
        active_profile = detect_soil_profile(latest, state=state, lang="en")
        if active_profile not in profile.get("soils", []):
            soil_penalty += 15
            
        # Final Priority Score
        final_score = 100 - soil_penalty
        
        details["score"] = max(10, final_score) # Don't go below 10
        results[crop] = details
                
    return jsonify(results)"""

app_py = re.sub(r'@app\.route\("/recommend"\).*?return jsonify\(results\)', new_recommend, app_py, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Injected 2D Array and updated recommend engine!")

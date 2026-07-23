import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

new_recommend = """@app.route("/recommend")
def recommend():
    season = request.args.get("season", "Rabi")
    state = request.args.get("state", "Rajasthan")
    region = STATE_TO_REGION.get(state, "North")
    lang = request.args.get("lang", "en")
    
    # New Multi-Filters
    water_filter = request.args.get("water", "Any")
    type_filter = request.args.get("type", "Any")
    soil_override = request.args.get("soil", "Auto")
    
    # 1. EASY ACCESS VIA 2D ARRAY
    valid_crops = STATE_SEASON_CROP_MAP.get(state, {}).get(season, [])
    
    # If the 2D array has nothing, fallback to all crops in that season
    if not valid_crops:
        valid_crops = [c for c, p in crop_profiles.items() if p.get("season") == season]
        
    results = {}
    for crop in valid_crops:
        profile = crop_profiles[crop]
        
        # Apply Multi-Filters (Hard Filters)
        if water_filter != "Any" and profile.get("water_needs") != water_filter:
            continue
        if type_filter != "Any" and profile.get("crop_type") != type_filter:
            continue
            
        # 2. ADD SOIL FEATURE AND EVERYTHING INTO CONSIDERATION
        score, details = calculate_suitability(crop, latest, season, region, state=state, lang=lang)
        
        soil_penalty = 0
        
        # Moisture check
        if latest["moisture"] > 0: 
            if latest["moisture"] < profile["moisture"][0]: soil_penalty += 15
            elif latest["moisture"] > profile["moisture"][1]: soil_penalty += 15
            
        # pH check
        if latest["ph"] < profile["ph"][0] or latest["ph"] > profile["ph"][1]:
            soil_penalty += 15
            
        # NPK checks
        if latest["n"] > 0 and latest["n"] < profile["n"][0]: soil_penalty += 10
        if latest["p"] > 0 and latest["p"] < profile["p"][0]: soil_penalty += 10
        if latest["k"] > 0 and latest["k"] < profile["k"][0]: soil_penalty += 10
        
        # Soil Type Check (Override or Auto)
        if soil_override != "Auto":
            active_profile = soil_override
        else:
            active_profile = detect_soil_profile(latest, state=state, lang="en")
            
        if active_profile not in profile.get("soils", []):
            soil_penalty += 15
            
        # Final Priority Score
        final_score = 100 - soil_penalty
        
        details["score"] = max(10, final_score) 
        results[crop] = details
                
    return jsonify(results)"""

app_py = re.sub(r'@app\.route\("/recommend"\).*?return jsonify\(results\)', new_recommend, app_py, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Updated /recommend to support multi-filters!")

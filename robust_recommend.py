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
        
    results = {}
    for crop, profile in crop_profiles.items():
        # HARD FILTERS: If these don't match, the crop is instantly rejected
        if profile.get("season") != season:
            continue
        if water_filter != "Any" and profile.get("water_needs") != water_filter:
            continue
        if type_filter != "Any" and profile.get("crop_type") != type_filter:
            continue
            
        score, details = calculate_suitability(crop, latest, season, region, state=state, lang=lang)
        
        penalty = 0
        
        # Region penalty
        if region not in profile.get("regions", []):
            penalty += 15
            
        # Moisture penalty
        if latest["moisture"] > 0: 
            if latest["moisture"] < profile["moisture"][0] or latest["moisture"] > profile["moisture"][1]: 
                penalty += 15
            
        # pH penalty
        if latest["ph"] < profile["ph"][0] or latest["ph"] > profile["ph"][1]:
            penalty += 15
            
        # NPK penalties
        if latest["n"] > 0 and latest["n"] < profile["n"][0]: penalty += 10
        if latest["p"] > 0 and latest["p"] < profile["p"][0]: penalty += 10
        if latest["k"] > 0 and latest["k"] < profile["k"][0]: penalty += 10
        
        # Soil Type Check (Override or Auto)
        if soil_override != "Auto":
            active_profile = soil_override
        else:
            active_profile = detect_soil_profile(latest, state=state, lang="en")
            
        if active_profile not in profile.get("soils", []):
            penalty += 15
            
        # Final Priority Score (100 is spot on perfect)
        final_score = 100 - penalty
        
        details["score"] = max(10, final_score) 
        results[crop] = details
                
    return jsonify(results)"""

app_py = re.sub(r'@app\.route\("/recommend"\).*?return jsonify\(results\)', new_recommend, app_py, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Removed 2D array logic and made the multi-filter scoring completely robust!")

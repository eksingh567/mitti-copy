import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# Let's update the /recommend route to filter out 0% matches or crops that don't match the fundamental season/region.
old_recommend = '''@app.route("/recommend")
def recommend():
    season = request.args.get("season", "Kharif")
    state = request.args.get("state", "Rajasthan")
    
    region = STATE_TO_REGION.get(state, "North")
    
    results = {}
    for crop_name in crop_profiles.keys():
        score, details = calculate_suitability(crop_name, SENSOR_DATA, season, region, state=state)
        results[crop_name] = {"score": score, "details": details}
        
    return jsonify(results)'''

new_recommend = '''@app.route("/recommend")
def recommend():
    season = request.args.get("season", "Kharif")
    state = request.args.get("state", "Rajasthan")
    
    region = STATE_TO_REGION.get(state, "North")
    
    results = {}
    for crop_name in crop_profiles.keys():
        score, details = calculate_suitability(crop_name, SENSOR_DATA, season, region, state=state)
        
        # Hard filtering: Crop must match Season, and have a reasonable score
        profile = crop_profiles[crop_name]
        
        # Check hard filters
        season_match = profile.get("season") == season
        region_match = region in profile.get("regions", [])
        
        active_profile = detect_soil_profile(SENSOR_DATA, state=state)
        soil_match = active_profile in profile.get("soils", [])
        
        # If the user strictly wants it filtered by Season, Soil, and Region:
        if season_match and region_match and soil_match:
            results[crop_name] = {"score": score, "details": details}
        elif score > 60 and season_match: 
            # Allow some leeway if it's the right season and high score but maybe bordering region
            results[crop_name] = {"score": score, "details": details}
            
    # If no crops survive the strict filter, fallback to returning the best 3 for the season
    if not results:
        for crop_name in crop_profiles.keys():
            score, details = calculate_suitability(crop_name, SENSOR_DATA, season, region, state=state)
            if crop_profiles[crop_name].get("season") == season:
                results[crop_name] = {"score": score, "details": details}
        
    return jsonify(results)'''

app_py = app_py.replace(old_recommend, new_recommend)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Updated /recommend to filter by Season, Soil, and Region")

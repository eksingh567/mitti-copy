import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

new_routes = """def get_greeting(state, lang):
    greetings = {
        "Punjab": "Sat Sri Akal",
        "Haryana": "Ram Ram",
        "Uttar Pradesh": "Namaste",
        "Maharashtra": "Namaskar",
        "Tamil Nadu": "Vanakkam",
        "Gujarat": "Kem Cho",
        "West Bengal": "Nomoshkar",
        "Kerala": "Namaskaram",
        "Karnataka": "Namaskara",
        "Andhra Pradesh": "Namaskaram",
        "Telangana": "Namaskaram",
        "Odisha": "Namaskar",
        "Assam": "Nomoskar"
    }
    
    if lang == "hi":
        return "नमस्ते किसान भाई!"
    
    return f"{greetings.get(state, 'Namaste')}!"

@app.route("/")
def dashboard():
    \"\"\"Serve the live dashboard data as JSON.\"\"\"
    user_state = request.args.get("state", "Rajasthan")
    lang = request.args.get("lang", "en")
    
    soil_profile = detect_soil_profile(latest, state=user_state, lang=lang)
    
    advisories = ["खरीफ फसलों के लिए अनुकूल परिस्थितियां।", "मिट्टी की नमी बनाए रखें।"] if lang == "hi" else ["Optimal conditions for Kharif crops.", "Maintain soil moisture."]
    
    return jsonify({
        "status": "ok",
        "data": latest,
        "advisories": advisories,
        "wisdom": generate_wisdom(lang=lang),
        "soil_profile": soil_profile,
        "greeting": get_greeting(user_state, lang)
    })

@app.route("/recommend")
def recommend():
    state = request.args.get("state", "Rajasthan")
    region = request.args.get("region", "West")
    season = request.args.get("season", "Kharif")
    lang = request.args.get("lang", "en")
    
    results = {}
    for crop in crop_profiles.keys():
        score, details = calculate_suitability(crop, latest, season, region, state=state, lang=lang)
        if isinstance(details, dict):
            details["score"] = score
            
            # Hard filtering logic
            profile = crop_profiles[crop]
            season_match = profile.get("season") == season
            region_match = region in profile.get("regions", [])
            
            active_profile = detect_soil_profile(latest, state=state, lang="en")
            soil_match = active_profile in profile.get("soils", [])
            
            if season_match and region_match and soil_match:
                results[crop] = details
            elif score > 60 and season_match: 
                results[crop] = details
                
    if not results:
        for crop in crop_profiles.keys():
            score, details = calculate_suitability(crop, latest, season, region, state=state, lang=lang)
            if crop_profiles[crop].get("season") == season:
                details["score"] = score
                results[crop] = details
        
    return jsonify(results)"""

app_py = re.sub(r'@app\.route\("/"\)\s*def get_greeting.*?return jsonify\(results\)', new_routes, app_py, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Successfully replaced routes in app.py")

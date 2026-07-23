import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# Let's replace the calculate_suitability logic to be extremely detailed.
new_logic = '''def calculate_suitability(crop_name, soil_data, season, region, state=None):
    if crop_name not in crop_profiles:
        return 0, {"error": "Crop not found"}
        
    profile = crop_profiles[crop_name].copy()
    penalties = 0
    feedback_items = []
    
    # 1. Season Check
    if profile.get("season") != season:
        penalties += 30
        feedback_items.append(f"Wrong season. {crop_name} is best grown in {profile.get('season')}.")
        
    # 2. Region Check
    if region not in profile.get("regions", []):
        penalties += 15
        feedback_items.append(f"Not typically grown in {region} region.")
        
    # 3. Soil Profile Check
    active_profile = detect_soil_profile(soil_data, state=state)
    if active_profile not in profile.get("soils", []):
        penalties += 20
        feedback_items.append(f"Soil mismatch. Prefers {', '.join(profile.get('soils', []))} but current is {active_profile}.")
        
    # 4. NPK & pH Deficiencies
    if "n" in profile:
        req_n = profile["n"]
        if soil_data.get("n", 0) < req_n[0]:
            diff = req_n[0] - soil_data.get("n", 0)
            penalties += 10
            feedback_items.append(f"Nitrogen is low by {diff} mg/kg. Add Urea or N-rich fertilizer.")
        elif soil_data.get("n", 0) > req_n[1]:
            feedback_items.append("Nitrogen is slightly high.")
            
    if "p" in profile:
        req_p = profile["p"]
        if soil_data.get("p", 0) < req_p[0]:
            diff = req_p[0] - soil_data.get("p", 0)
            penalties += 10
            feedback_items.append(f"Phosphorus is low by {diff} mg/kg. Add DAP or SSP.")
            
    if "k" in profile:
        req_k = profile["k"]
        if soil_data.get("k", 0) < req_k[0]:
            diff = req_k[0] - soil_data.get("k", 0)
            penalties += 10
            feedback_items.append(f"Potassium is low by {diff} mg/kg. Add MOP.")
            
    if "ph" in profile:
        req_ph = profile["ph"]
        profile["ph_range"] = f"{req_ph[0]} - {req_ph[1]}"
        if soil_data.get("ph", 7) < req_ph[0]:
            penalties += 15
            feedback_items.append(f"Soil is too acidic for {crop_name}. Apply agricultural lime.")
        elif soil_data.get("ph", 7) > req_ph[1]:
            penalties += 15
            feedback_items.append(f"Soil is too alkaline for {crop_name}. Add gypsum or organic matter.")
    else:
        profile["ph_range"] = "N/A"
        
    if "moisture" in profile:
        req_m = profile["moisture"]
        profile["moisture_range"] = f"{req_m[0]}% - {req_m[1]}%"
        if soil_data.get("moisture", 0) < req_m[0]:
            feedback_items.append(f"Moisture is critically low. Immediate irrigation required (needs {req_m[0]}%).")
    else:
        profile["moisture_range"] = "N/A"
        
    if not feedback_items:
        feedback_items.append("Excellent match! Soil and conditions are highly optimal.")
        
    profile["feedback_list"] = feedback_items
    profile["feedback"] = " ".join(feedback_items)
    
    score = max(0, 100 - penalties)
    return score, profile'''

# Replace the old calculate_suitability logic completely
app_py = re.sub(r'def calculate_suitability\(.*?\n    return max\(0, 100 - penalties\), profile', new_logic, app_py, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Updated app.py with detailed deficiency logic")

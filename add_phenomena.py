import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# 1. Add Mango to crop_profiles
mango_profile = """
    "Mango": {"name_en": "Mango", "name_hi": "Mango / आम", "season": "Zaid", "regions": ["North", "South", "East", "West"], "ph": (5.5, 7.5), "moisture": (40, 70), "ec": (0, 1.5), "n": (80, 150), "p": (20, 40), "k": (100, 200), "soils": ["Alluvial Soil (Fertile)", "Red & Yellow Soil", "Laterite Soil"], "water_needs": "Medium", "crop_type": "Plantation"},
"""
app_py = app_py.replace('"Wheat": {"name_en": "Wheat"', mango_profile + '    "Wheat": {"name_en": "Wheat"')

# 2. Update recommend logic to handle phenomenon
old_recommend_params = """    type_filter = request.args.get("type", "Any")
    soil_override = request.args.get("soil", "Auto")"""

new_recommend_params = """    type_filter = request.args.get("type", "Any")
    soil_override = request.args.get("soil", "Auto")
    phenomenon = request.args.get("phenomenon", "None")"""

app_py = app_py.replace(old_recommend_params, new_recommend_params)

# Insert the phenomenon scoring logic right before details["score"] = max(10, final_score)
old_score_calc = """        # Final Priority Score (100 is spot on perfect)
        final_score = 100 - penalty"""

new_score_calc = """        # Final Priority Score (100 is spot on perfect)
        final_score = 100 - penalty
        
        # Localized Weather Phenomena Boosts & Penalties
        if phenomenon == "Mango Showers":
            if region in ["South", "West"] and crop in ["Mango", "Coffee"]:
                final_score += 20
                details["feedback_list"].append("Benefiting from Mango/Cherry Blossom Showers! Optimal ripening conditions.")
        elif phenomenon == "Kal Baisakhi":
            if region == "East" and crop in ["Tea", "Jute"]:
                final_score += 20
                details["feedback_list"].append("Benefiting from Kal Baisakhi / Nor'westers! High moisture advantage.")
        elif phenomenon == "Western Disturbances":
            if region == "North" and season == "Rabi" and crop in ["Wheat", "Mustard", "Gram"]:
                final_score += 20
                details["feedback_list"].append("Benefiting from Western Disturbances! Winter rainfall boosting yield.")
        elif phenomenon == "Loo":
            if region in ["North", "West"] and crop in ["Wheat", "Mustard", "Gram", "Potato"]:
                final_score -= 30
                details["feedback_list"].append("Warning: 'Loo' hot winds detected. Severe heat stress risk. Increase irrigation immediately.")
"""

app_py = app_py.replace(old_score_calc, new_score_calc)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Added Mango and weather phenomena logic to app.py!")

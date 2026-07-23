import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

new_detect = """def detect_soil_profile(soil_data, state=None, lang="en"):
    ph = soil_data.get("ph", 7.0)
    ec = soil_data.get("ec", 0.0)
    moist = soil_data.get("moisture", 0)
    k = soil_data.get("k", 0)
    n = soil_data.get("n", 0)
    
    profile = "Alluvial Soil (Fertile)"
    if ec > 4.0:
        profile = "Saline/Alkaline Soil"
    elif ph < 5.0:
        profile = "Laterite Soil"
    elif ph < 6.0 and moist > 50:
        profile = "Forest/Mountain Soil"
    elif ph > 7.5 and ec > 1.8 and moist < 25:
        profile = "Arid / Desert Soil"
    elif ph >= 7.0 and k > 180 and moist > 45:
        profile = "Black Soil (Regur)"
    elif ph < 6.8 and n < 100:
        profile = "Red & Yellow Soil"
    elif ph < 5.0 and moist > 70:
        profile = "Peaty/Marshy Soil"
    elif ec > 1.5 and moist < 40:
        profile = "Coastal Sandy Soil"

    if lang == "hi":
        translations = {
            "Alluvial Soil (Fertile)": "जलोढ़ मिट्टी (उपजाऊ)",
            "Arid / Desert Soil": "शुष्क / मरुस्थलीय मिट्टी",
            "Black Soil (Regur)": "काली मिट्टी (रेगुर)",
            "Red & Yellow Soil": "लाल और पीली मिट्टी",
            "Laterite Soil": "लैटेराइट मिट्टी",
            "Forest/Mountain Soil": "वन/पहाड़ी मिट्टी",
            "Coastal Sandy Soil": "तटीय रेतीली मिट्टी",
            "Peaty/Marshy Soil": "दलदली मिट्टी",
            "Saline/Alkaline Soil": "खारी/क्षारीय मिट्टी"
        }
        return translations.get(profile, profile)
    return profile"""

app_py = re.sub(r'def detect_soil_profile\(soil_data, state=None\):.*?return "Alluvial Soil \(Fertile\)"', new_detect, app_py, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Fixed detect_soil_profile")

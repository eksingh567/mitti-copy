import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# 1. Update detect_soil_profile to handle translation
new_detect = '''def detect_soil_profile(soil_data, state=None, lang="en"):
    ph = soil_data.get("ph", 7.0)
    moisture = soil_data.get("moisture", 50)
    
    if state and state in STATE_SOIL_TYPES:
        profile = STATE_SOIL_TYPES[state]
    elif ph < 6.0 and moisture > 70:
        profile = "Laterite Soil"
    elif ph > 7.5 and moisture < 40:
        profile = "Arid / Desert Soil"
    elif 6.5 <= ph <= 7.5 and moisture > 50:
        profile = "Alluvial Soil (Fertile)"
    else:
        profile = "Red & Yellow Soil"
        
    if lang == "hi":
        translations = {
            "Alluvial Soil (Fertile)": "जलोढ़ मिट्टी (उपजाऊ)",
            "Arid / Desert Soil": "शुष्क / मरुस्थलीय मिट्टी",
            "Black Soil (Regur)": "काली मिट्टी (रेगुर)",
            "Red & Yellow Soil": "लाल और पीली मिट्टी",
            "Laterite Soil": "लैटेराइट मिट्टी",
            "Forest/Mountain Soil": "वन/पहाड़ी मिट्टी",
            "Coastal Sandy Soil": "तटीय रेतीली मिट्टी",
            "Peaty/Marshy Soil": "दलदली मिट्टी"
        }
        return translations.get(profile, profile)
    return profile'''

app_py = re.sub(r'def detect_soil_profile\(soil_data, state=None\):.*?return profile', new_detect, app_py, flags=re.DOTALL)


# 2. Update calculate_suitability to use lang
new_calc = '''def calculate_suitability(crop_name, soil_data, season, region, state=None, lang="en"):
    if crop_name not in crop_profiles:
        return 0, {"error": "Crop not found"}
        
    profile = crop_profiles[crop_name].copy()
    penalties = 0
    feedback_items = []
    
    # helper for translation
    def t(en_text, hi_text):
        return hi_text if lang == "hi" else en_text
        
    c_name = profile.get("name_hi", crop_name) if lang == "hi" else profile.get("name_en", crop_name)
    
    active_profile = detect_soil_profile(soil_data, state=state, lang="en") # use en for logic
    
    # 1. Season Check
    if profile.get("season") != season:
        penalties += 30
        feedback_items.append(t(
            f"Wrong season. {c_name} is best grown in {profile.get('season')}.",
            f"गलत मौसम। {c_name} को {profile.get('season')} में उ गाना सबसे अच्छा है।"
        ))
        
    # 2. Region Check
    if region not in profile.get("regions", []):
        penalties += 15
        feedback_items.append(t(
            f"Not typically grown in {region} region.",
            f"आमतौर पर {region} क्षेत्र में नहीं उगाया जाता है।"
        ))
        
    # 3. Soil Profile Check
    if active_profile not in profile.get("soils", []):
        penalties += 20
        feedback_items.append(t(
            f"Soil mismatch. Prefers {', '.join(profile.get('soils', []))} but current is {active_profile}.",
            f"मिट्टी का प्रकार मेल नहीं खाता। यह {', '.join(profile.get('soils', []))} पसंद करता है, लेकिन वर्तमान में {active_profile} है।"
        ))
        
    # 4. NPK & pH Deficiencies
    if "n" in profile:
        req_n = profile["n"]
        if soil_data.get("n", 0) < req_n[0]:
            diff = req_n[0] - soil_data.get("n", 0)
            penalties += 10
            feedback_items.append(t(
                f"Nitrogen is low by {diff} mg/kg. Add Urea or N-rich fertilizer.",
                f"नाइट्रोजन {diff} mg/kg कम है। यूरिया या N-समृद्ध उर्वरक डालें।"
            ))
            
    if "p" in profile:
        req_p = profile["p"]
        if soil_data.get("p", 0) < req_p[0]:
            diff = req_p[0] - soil_data.get("p", 0)
            penalties += 10
            feedback_items.append(t(
                f"Phosphorus is low by {diff} mg/kg. Add DAP or SSP.",
                f"फास्फोरस {diff} mg/kg कम है। DAP या SSP डालें।"
            ))
            
    if "k" in profile:
        req_k = profile["k"]
        if soil_data.get("k", 0) < req_k[0]:
            diff = req_k[0] - soil_data.get("k", 0)
            penalties += 10
            feedback_items.append(t(
                f"Potassium is low by {diff} mg/kg. Add MOP.",
                f"पोटेशियम {diff} mg/kg कम है। MOP डालें।"
            ))
            
    if "ph" in profile:
        req_ph = profile["ph"]
        profile["ph_range"] = f"{req_ph[0]} - {req_ph[1]}"
        if soil_data.get("ph", 7) < req_ph[0]:
            penalties += 15
            feedback_items.append(t(
                f"Soil is too acidic for {c_name}. Apply agricultural lime.",
                f"मिट्टी {c_name} के लिए बहुत अधिक अम्लीय है। कृषि चूना डालें।"
            ))
        elif soil_data.get("ph", 7) > req_ph[1]:
            penalties += 15
            feedback_items.append(t(
                f"Soil is too alkaline for {c_name}. Add gypsum or organic matter.",
                f"मिट्टी {c_name} के लिए बहुत अधिक क्षारीय है। जिप्सम या जैविक खाद डालें।"
            ))
    else:
        profile["ph_range"] = "N/A"
        
    if "moisture" in profile:
        req_m = profile["moisture"]
        profile["moisture_range"] = f"{req_m[0]}% - {req_m[1]}%"
        if soil_data.get("moisture", 0) < req_m[0]:
            feedback_items.append(t(
                f"Moisture is critically low. Immediate irrigation required (needs {req_m[0]}%).",
                f"नमी गंभीर रूप से कम है। तत्काल सिंचाई की आवश्यकता है ({req_m[0]}% की आवश्यकता है)।"
            ))
    else:
        profile["moisture_range"] = "N/A"
        
    if not feedback_items:
        feedback_items.append(t(
            "Excellent match! Soil and conditions are highly optimal.",
            "उत्कृष्ट! मिट्टी और स्थितियां अत्यधिक अनुकूल हैं।"
        ))
        
    profile["feedback_list"] = feedback_items
    profile["feedback"] = " ".join(feedback_items)
    
    score = max(0, 100 - penalties)
    return score, profile'''

app_py = re.sub(r'def calculate_suitability\(crop_name, soil_data, season, region, state=None\):.*?return score, profile', new_calc, app_py, flags=re.DOTALL)


# 3. Update generate_wisdom
new_wisdom = '''def generate_wisdom(lang="en"):
    if lang == "hi":
        wisdoms = [
            "कृषि पाराशर: 'श्रावण मास में वर्षा भरपूर फसल लाती है।'",
            "वृक्षायुर्वेद: 'नीम की खली मिट्टी को समृद्ध करती है और प्राकृतिक कीट निवारक का काम करती है।'",
            "पारंपरिक ज्ञान: 'गर्मियों में गहरी जोती गई खेत मानसून की बारिश को पूरी तरह से पी लेती है।'",
            "प्राचीन ज्ञान: 'अनाज के साथ फलीदार फसलों को उगाने से पृथ्वी की जीवन शक्ति बहाल होती है।'",
            "चाणक्य नीति: 'कृषि सभी धन का मूल है।' अपनी ऊपरी मिट्टी की सोने की तरह रक्षा करें।"
        ]
    else:
        wisdoms = [
            "Krishi Parashara: 'Rainfall in the month of Shravana brings an abundant harvest.'",
            "Vrikshayurveda: 'Applying Neem cake not only enriches the soil but acts as a powerful natural pest deterrent.'",
            "Traditional Knowledge: 'A deeply ploughed field in the hot summer drinks the monsoon rain completely.'",
            "Ancient Wisdom: 'Rotating leguminous crops with cereals restores the earth's vital life force.'",
            "Chanakya Niti: 'Agriculture is the root of all wealth.' Protect your topsoil like gold."
        ]
    return random.choice(wisdoms)'''
app_py = re.sub(r'def generate_wisdom\(\):.*?return random\.choice\(wisdoms\)', new_wisdom, app_py, flags=re.DOTALL)

# 4. Update / and /recommend routes to pass lang
app_py = app_py.replace('soil_profile = detect_soil_profile(SENSOR_DATA, state=state)', 'lang = request.args.get("lang", "en")\n    soil_profile = detect_soil_profile(SENSOR_DATA, state=state, lang=lang)')
app_py = app_py.replace('def dashboard():\n    state = request.args.get("state", "Rajasthan")', 'def dashboard():\n    state = request.args.get("state", "Rajasthan")\n    lang = request.args.get("lang", "en")')
app_py = app_py.replace('"wisdom": generate_wisdom(),', '"wisdom": generate_wisdom(lang=lang),')

# Update advisories in dashboard
advisories_en = '["Optimal conditions for Kharif crops.", "Maintain soil moisture."]'
advisories_hi = '["खरीफ फसलों के लिए अनुकूल परिस्थितियां।", "मिट्टी की नमी बनाए रखें।"]'
app_py = app_py.replace('"advisories": ["Optimal conditions for Kharif crops.", "Maintain soil moisture."],', f'"advisories": {advisories_hi} if lang == "hi" else {advisories_en},')


app_py = app_py.replace('def recommend():\n    season = request.args.get("season", "Kharif")', 'def recommend():\n    season = request.args.get("season", "Kharif")\n    lang = request.args.get("lang", "en")')
app_py = app_py.replace('score, details = calculate_suitability(crop_name, SENSOR_DATA, season, region, state=state)', 'score, details = calculate_suitability(crop_name, SENSOR_DATA, season, region, state=state, lang=lang)')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Updated app.py with full dynamic Hindi translations")

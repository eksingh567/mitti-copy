import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# 1. Expand STATE_SOIL_TYPES
old_states = '''STATE_SOIL_TYPES = {
    "Punjab": "Alluvial Soil (Fertile)",
    "Haryana": "Alluvial Soil (Fertile)",
    "Rajasthan": "Arid / Desert Soil",
    "Gujarat": "Black Soil (Regur)",
    "Maharashtra": "Black Soil (Regur)",
    "Madhya Pradesh": "Black Soil (Regur)",
    "Uttar Pradesh": "Alluvial Soil (Fertile)",
    "Andhra Pradesh": "Red & Yellow Soil",
    "Karnataka": "Red & Yellow Soil",
    "Tamil Nadu": "Red & Yellow Soil",
    "Kerala": "Laterite Soil",
    "West Bengal": "Alluvial Soil (Fertile)",
    "Assam": "Alluvial Soil (Fertile)"
}'''

new_states = '''STATE_SOIL_TYPES = {
    "Andhra Pradesh": "Red & Yellow Soil",
    "Arunachal Pradesh": "Forest/Mountain Soil",
    "Assam": "Alluvial Soil (Fertile)",
    "Bihar": "Alluvial Soil (Fertile)",
    "Chhattisgarh": "Red & Yellow Soil",
    "Goa": "Laterite Soil",
    "Gujarat": "Black Soil (Regur)",
    "Haryana": "Alluvial Soil (Fertile)",
    "Himachal Pradesh": "Forest/Mountain Soil",
    "Jharkhand": "Red & Yellow Soil",
    "Karnataka": "Red & Yellow Soil",
    "Kerala": "Laterite Soil",
    "Madhya Pradesh": "Black Soil (Regur)",
    "Maharashtra": "Black Soil (Regur)",
    "Manipur": "Forest/Mountain Soil",
    "Meghalaya": "Laterite Soil",
    "Mizoram": "Forest/Mountain Soil",
    "Nagaland": "Forest/Mountain Soil",
    "Odisha": "Red & Yellow Soil",
    "Punjab": "Alluvial Soil (Fertile)",
    "Rajasthan": "Arid / Desert Soil",
    "Sikkim": "Forest/Mountain Soil",
    "Tamil Nadu": "Red & Yellow Soil",
    "Telangana": "Red & Yellow Soil",
    "Tripura": "Red & Yellow Soil",
    "Uttar Pradesh": "Alluvial Soil (Fertile)",
    "Uttarakhand": "Forest/Mountain Soil",
    "West Bengal": "Alluvial Soil (Fertile)",
    "Andaman and Nicobar Islands": "Coastal Sandy Soil",
    "Chandigarh": "Alluvial Soil (Fertile)",
    "Dadra and Nagar Haveli and Daman and Diu": "Coastal Sandy Soil",
    "Lakshadweep": "Coastal Sandy Soil",
    "Delhi": "Alluvial Soil (Fertile)",
    "Puducherry": "Coastal Sandy Soil",
    "Jammu and Kashmir": "Forest/Mountain Soil",
    "Ladakh": "Arid / Desert Soil"
}'''
app_py = app_py.replace(old_states, new_states)

# 2. Update /call endpoint
old_call = '''@app.route("/call")
def make_call():
    """Trigger a mock Twilio voice call alert."""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return jsonify({"status": "error", "message": "Twilio not configured"})
        
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            twiml='<Response><Say>Alert from Mitti Platform. Please check your dashboard for new soil recommendations.</Say></Response>',
            to=TO_PHONE_NUMBER,
            from_=TWILIO_PHONE_NUMBER
        )
        return jsonify({"status": "success", "call_sid": call.sid})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})'''

new_call = '''@app.route("/call", methods=["GET", "POST"])
def make_call():
    """Trigger a Twilio voice call advisory in Hindi."""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return jsonify({"status": "error", "message": "Twilio not configured"})
        
    try:
        state = request.args.get("state", "Rajasthan")
        season = request.args.get("season", "Kharif")
        
        # Determine best crops
        region_map = {
            "Punjab": "North", "Uttar Pradesh": "North", "Haryana": "North", "Delhi": "North", "Himachal Pradesh": "North", "Uttarakhand": "North",
            "Rajasthan": "West", "Gujarat": "West", "Maharashtra": "West", "Goa": "West",
            "Madhya Pradesh": "Central", "Chhattisgarh": "Central",
            "Andhra Pradesh": "South", "Karnataka": "South", "Kerala": "South", "Tamil Nadu": "South", "Telangana": "South",
            "Bihar": "East", "Jharkhand": "East", "Odisha": "East", "West Bengal": "East",
            "Assam": "Northeast", "Arunachal Pradesh": "Northeast", "Manipur": "Northeast", "Meghalaya": "Northeast", "Mizoram": "Northeast", "Nagaland": "Northeast", "Sikkim": "Northeast", "Tripura": "Northeast"
        }
        region = region_map.get(state, "North")
        
        results = {}
        for crop_name in crop_profiles.keys():
            score, details = calculate_suitability(crop_name, SENSOR_DATA, season, region, state=state)
            if score > 50:
                results[crop_name] = {"score": score, "details": details}
        
        sorted_crops = sorted(results.items(), key=lambda item: item[1]['score'], reverse=True)
        top_crops = [item[1]['details'].get('name_hi', item[0]).split('/')[1].strip() if '/' in item[1]['details'].get('name_hi', item[0]) else item[0] for item in sorted_crops[:2]]
        
        crop_text = " और ".join(top_crops) if top_crops else "कोई उपयुक्त फसल नहीं"
        
        twiml_msg = f'<Response><Say language="hi-IN">नमस्ते किसान भाई। मिट्टी प्लेटफॉर्म से सूचना। आपके {state} के खेत और वर्तमान मौसम के अनुसार, {crop_text} की खेती सबसे अच्छी रहेगी। अधिक जानकारी के लिए मिट्टी ऐप देखें। धन्यवाद।</Say></Response>'
        
        # If twilio credentials are not real, we will just return success and the twiml string to verify it works without actually crashing
        if TWILIO_ACCOUNT_SID == 'your_account_sid':
            return jsonify({"status": "success", "message": "Mock call successful (Twilio not configured)", "twiml": twiml_msg})
            
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            twiml=twiml_msg,
            to=TO_PHONE_NUMBER,
            from_=TWILIO_PHONE_NUMBER
        )
        return jsonify({"status": "success", "call_sid": call.sid, "twiml": twiml_msg})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})'''

app_py = app_py.replace(old_call, new_call)

# Fix STATE_TO_REGION
old_region = '''STATE_TO_REGION = {
    "Punjab": "North", "Haryana": "North", "Uttar Pradesh": "North", "Delhi": "North",
    "Rajasthan": "West", "Gujarat": "West", "Maharashtra": "West",
    "Madhya Pradesh": "Central", "Chhattisgarh": "Central",
    "Andhra Pradesh": "South", "Karnataka": "South", "Tamil Nadu": "South", "Kerala": "South",
    "West Bengal": "East", "Bihar": "East", "Odisha": "East", "Jharkhand": "East",
    "Assam": "Northeast"
}'''

new_region = '''STATE_TO_REGION = {
    "Punjab": "North", "Haryana": "North", "Uttar Pradesh": "North", "Delhi": "North", "Himachal Pradesh": "North", "Uttarakhand": "North",
    "Rajasthan": "West", "Gujarat": "West", "Maharashtra": "West", "Goa": "West",
    "Madhya Pradesh": "Central", "Chhattisgarh": "Central",
    "Andhra Pradesh": "South", "Karnataka": "South", "Tamil Nadu": "South", "Kerala": "South", "Telangana": "South",
    "West Bengal": "East", "Bihar": "East", "Odisha": "East", "Jharkhand": "East",
    "Assam": "Northeast", "Arunachal Pradesh": "Northeast", "Manipur": "Northeast", "Meghalaya": "Northeast", "Mizoram": "Northeast", "Nagaland": "Northeast", "Sikkim": "Northeast", "Tripura": "Northeast",
    "Jammu and Kashmir": "North", "Ladakh": "North", "Andaman and Nicobar Islands": "South", "Chandigarh": "North", "Dadra and Nagar Haveli and Daman and Diu": "West", "Lakshadweep": "South", "Puducherry": "South"
}'''
app_py = app_py.replace(old_region, new_region)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Updated app.py with Twilio Hindi Logic and All Indian Soils")

import re

with open('frontend/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Fix the i18n dictionary that got corrupted
new_dict = """const i18n = {
    "Dashboard": {"hinglish": "Dashboard", "hi": "डैशबोर्ड"},
    "Crop Encyclopedia": {"hinglish": "Fasal Ki Jankari", "hi": "फसल ज्ञानकोष"},
    "Yield History": {"hinglish": "Pichli Paidawar", "hi": "पिछली पैदावार"},
    "Settings": {"hinglish": "Settings", "hi": "सेटिंग्स"},
    "Region Map": {"hinglish": "Kshetra Naksha", "hi": "क्षेत्र नक्शा"},
    "Active Soil Profile": {"hinglish": "Aapki Mitti Ka Prakar", "hi": "सक्रिय मिट्टी प्रोफ़ाइल"},
    "Macronutrients": {"hinglish": "Zaroori Tatva (NPK)", "hi": "मुख्य पोषक तत्व (NPK)"},
    "Soil Health": {"hinglish": "Mitti Ki Sehat", "hi": "मिट्टी का स्वास्थ्य"},
    "Suitability Engine": {"hinglish": "Sahi Fasal Engine", "hi": "उपयुक्तता इंजन"},
    "Daily Wisdom & Advisories": {"hinglish": "Kheti Ka Gyan & Alerts", "hi": "कृषि ज्ञान और अलर्ट"},
    "Scan Sensors": {"hinglish": "Sensor Scan Karein", "hi": "सेंसर स्कैन करें"},
    "Call The Farmer": {"hinglish": "Kisan Ko Call Karein", "hi": "किसान को कॉल करें"},
    "State": {"hinglish": "Rajya", "hi": "राज्य"},
    "Season": {"hinglish": "Mausam", "hi": "मौसम"},
    "Required Actions:": {"hinglish": "Zaroori Kadam:", "hi": "आवश्यक कदम:"},
    "Log New Yield": {"hinglish": "Nayi Paidawar Darj Karein", "hi": "नई उपज दर्ज करें"},
    "Past Yield Records": {"hinglish": "Pichla Record", "hi": "पिछला रिकॉर्ड"},
    "Save Record": {"hinglish": "Record Save Karein", "hi": "रिकॉर्ड सहेजें"}
};"""

js = re.sub(r'const i18n = \{.*?^\};', new_dict, js, flags=re.DOTALL | re.MULTILINE)

# 2. Fix the fetch calls to include lang and cache buster
js = re.sub(r'const res = await fetch\(`\$\{API_URL\}/\?state=\$\{state\}`\);', 'const res = await fetch(`${API_URL}/?state=${state}&lang=${currentLang}&t=${Date.now()}`);', js)
js = re.sub(r'const res = await fetch\(`\$\{API_URL\}/recommend\?season=\$\{season\}&state=\$\{state\}`\);', 'const res = await fetch(`${API_URL}/recommend?season=${season}&state=${state}&lang=${currentLang}&t=${Date.now()}`);', js)

# 3. Apply the greeting from the backend to the UI
# The user wants greeting personalized. I'll insert a line in updateMetrics to set the greeting.
# Look for: if(dashboardWisdom && data.wisdom) dashboardWisdom.innerText = `"${data.wisdom}"`;
greeting_logic = """        // Update Greeting
        const greetingEl = document.querySelector('header h1');
        if (greetingEl && data.greeting) {
            greetingEl.innerText = data.greeting;
        }
        
        // Update Wisdom and Advisories"""
js = js.replace('// Update Wisdom and Advisories', greeting_logic)

with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Fixed app.js unicode and logic")

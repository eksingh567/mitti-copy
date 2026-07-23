import re

with open('app.js', 'r', encoding='utf-8') as f:
    js = f.read()

translations = '''
// ─── NATIVE TRANSLATION DICTIONARY ──────────────────────────
const i18n = {
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
};

let currentLang = 'en';

function setNativeLanguage(lang) {
    currentLang = lang;
    
    // Update active button state
    document.querySelectorAll('[id^="lang-btn-"]').forEach(btn => btn.style.background = 'none');
    document.getElementById(lang-btn-).style.background = 'rgba(16, 185, 129, 0.4)';
    
    // Quick and dirty text replacement by searching for English keys in text nodes
    walkDOM(document.body, function(node) {
        if(node.nodeType === 3) { // Text node
            let text = node.originalText || node.nodeValue.trim();
            if(!node.originalText && text.length > 0) node.originalText = text; // Save original
            
            if(node.originalText) {
                // Try exact match
                if(i18n[node.originalText]) {
                    node.nodeValue = lang === 'en' ? node.originalText : i18n[node.originalText][lang];
                }
            }
        }
    });
    
    // Also re-render dynamic content
    if(Object.keys(currentRecommendations).length > 0) {
        renderCropsGrid(currentRecommendations);
        const activeBtn = document.querySelector('.crop-btn.active');
        if(activeBtn) {
            const cropKey = activeBtn.id.replace('btn-', '');
            selectCrop(cropKey);
        }
    }
}

function walkDOM(node, func) {
    func(node);
    node = node.firstChild;
    while(node) {
        walkDOM(node, func);
        node = node.nextSibling;
    }
}
'''

js = js + '\n' + translations

with open('app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Added Hinglish/Hindi Translation Logic")

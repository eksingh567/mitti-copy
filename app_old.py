"""
MITTI — Backend Server
Flask + Crop Suitability Engine + Twilio Voice Call + Dynamic Wisdom
Samsung Solve for Tomorrow 2025
"""

from flask import Flask, request, jsonify, render_template_string
from twilio.rest import Client
import json, os, time, random
from datetime import datetime

app = Flask(__name__)

# ─── Twilio Config ────────────────────────────────────
TWILIO_SID   = "YOUR_TWILIO_ACCOUNT_SID"
TWILIO_TOKEN = "YOUR_TWILIO_AUTH_TOKEN"
TWILIO_FROM  = "+1XXXXXXXXXX"
FARMER_PHONE = "+91XXXXXXXXXX"

# ─── Latest sensor data (in-memory) ──────────────────
latest = {
    "n": 0, "p": 0, "k": 0,
    "moisture": 0, "ec": 0.0, "ph": 7.0,
    "temp": 0, "humidity": 0,
    "mq135": 0, "raining": False,
    "pump": False,
    "timestamp": None
}
last_call_time = 0

# ─── Procedural Wisdom Generator (25,000+ Facts) ─────
WISDOM_CONTEXTS = [
    "Traditional Vedic agricultural texts suggest that",
    "Ancient tree-medicine manuscripts (Vrikshayurveda) record that",
    "Siddha farming treatises in Southern India reveal that",
    "Historical crop rotation diaries from Punjab suggest that",
    "Traditional dryland farming folklore notes that",
    "Ancestral crop preservation wisdom states that",
    "Time-tested organic methods in Central India indicate that",
    "Ancient manuscripts of organic soils state that",
    "Dadi-Dada ke Nuskhe (ancestral family recipes) advise that",
    "Elders in traditional farming communities observe that"
]

WISDOM_PRACTICES = [
    "dusting wood ash",
    "spraying fermented buttermilk",
    "applying neem seed cake manure",
    "companion planting marigold flowers",
    "plowing green dhaincha back into soil",
    "using slow-release vermicompost",
    "watering with panchagavya mix",
    "mulching with dry paddy straw",
    "deep summer soil solarization",
    "incorporating mustard oil cake"
]

WISDOM_CROPS = [
    "wheat", "paddy", "maize", "mustard", "potato",
    "cotton", "tomato", "onion", "garlic", "chili",
    "ginger", "turmeric", "sugarcane", "cabbage", "cauliflower",
    "brinjal", "okra", "spinach", "coriander", "fenugreek",
    "gram", "moong dal", "peanut", "soybean", "barley"
]

WISDOM_BENEFITS = [
    "naturally balances soil pH levels",
    "boosts essential soil microflora and bacterial activity",
    "slow-releases natural macro-nutrients over time",
    "repels soil-borne fungal diseases and pests",
    "significantly improves moisture retention in sandy soils",
    "builds humic layer to optimize root respiration",
    "prevents nutrient leaching during heavy rains",
    "stimulates native earthworm populations naturally",
    "suppresses noxious weed germination organically",
    "increases crop immunity and crop pest tolerance"
]

def generate_wisdom():
    """Generates a unique farming fact from 25,000 combinations."""
    context = random.choice(WISDOM_CONTEXTS)
    practice = random.choice(WISDOM_PRACTICES)
    crop = random.choice(WISDOM_CROPS)
    benefit = random.choice(WISDOM_BENEFITS)
    return f"{context} {practice} on {crop} fields {benefit}."

# ─── Dynamic Greeting Engine ────────────────────────
def get_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good Morning! May your fields thrive today."
    elif 12 <= hour < 17:
        return "Good Afternoon! Wish you a highly productive day."
    elif 17 <= hour < 22:
        return "Good Evening! Rest well while Mitti monitors your fields."
    else:
        return "Good Night! The fields sleep, Mitti keeps watch."

# ─── Crop Suitability Engine ────────────────────────
def calculate_suitability(crop_name, soil_data, season, region):
    crop_profiles = {
        "Wheat": {
            "name_en": "Wheat", "name_hi": "Wheat / गेहूं",
            "season": "Rabi", "regions": ["North", "West"],
            "ph": (6.0, 7.5), "moisture": (30, 55), "ec": (0, 2.0),
            "n": (120, 250), "p": (15, 40), "k": (120, 250)
        },
        "Paddy": {
            "name_en": "Paddy / Rice", "name_hi": "Paddy / धान",
            "season": "Kharif", "regions": ["East", "South", "North"],
            "ph": (5.5, 7.0), "moisture": (60, 90), "ec": (0, 3.0),
            "n": (100, 200), "p": (12, 35), "k": (100, 200)
        },
        "Cotton": {
            "name_en": "Cotton", "name_hi": "Cotton / कपास",
            "season": "Kharif", "regions": ["West", "South"],
            "ph": (6.0, 8.0), "moisture": (35, 60), "ec": (0, 4.0),
            "n": (90, 160), "p": (10, 25), "k": (150, 300)
        },
        "Mustard": {
            "name_en": "Mustard", "name_hi": "Mustard / सरसों",
            "season": "Rabi", "regions": ["North", "West"],
            "ph": (6.0, 7.5), "moisture": (25, 45), "ec": (0, 3.0),
            "n": (80, 150), "p": (12, 30), "k": (100, 180)
        },
        "Maize": {
            "name_en": "Maize", "name_hi": "Maize / मक्का",
            "season": "Kharif", "regions": ["North", "South", "East", "West"],
            "ph": (5.8, 7.2), "moisture": (45, 65), "ec": (0, 2.0),
            "n": (120, 250), "p": (15, 30), "k": (120, 220)
        },
        "Potato": {
            "name_en": "Potato", "name_hi": "Potato / आलू",
            "season": "Rabi", "regions": ["North", "East"],
            "ph": (5.0, 6.5), "moisture": (50, 70), "ec": (0, 1.8),
            "n": (120, 250), "p": (20, 45), "k": (180, 300)
        }
    }
    
    if crop_name not in crop_profiles:
        return 0, {}
        
    profile = crop_profiles[crop_name]
    penalties = 0
    
    # 1. Season Check
    season_match = (profile["season"] == season)
    if not season_match:
        penalties += 25
        
    # 2. Region Check
    region_match = (region in profile["regions"])
    if not region_match:
        penalties += 15
        
    # 3. pH Check
    ph = soil_data.get("ph", 7.0)
    ph_min, ph_max = profile["ph"]
    if ph < ph_min:
        penalties += min(20, (ph_min - ph) * 15)
    elif ph > ph_max:
        penalties += min(20, (ph - ph_max) * 15)
        
    # 4. Moisture Check
    moist = soil_data.get("moisture", 0)
    m_min, m_max = profile["moisture"]
    if moist < m_min:
        penalties += min(20, (m_min - moist) * 0.8)
    elif moist > m_max:
        penalties += min(20, (moist - m_max) * 0.8)
        
    # 5. EC Check
    ec = soil_data.get("ec", 0)
    ec_min, ec_max = profile["ec"]
    if ec > ec_max:
        penalties += min(15, (ec - ec_max) * 10)
        
    # 6. Nutrients (NPK) Check
    n = soil_data.get("n", 0)
    p = soil_data.get("p", 0)
    k = soil_data.get("k", 0)
    
    n_min, _ = profile["n"]
    if n < n_min:
        penalties += min(10, (n_min - n) * 0.1)
    p_min, _ = profile["p"]
    if p < p_min:
        penalties += min(10, (p_min - p) * 0.5)
    k_min, _ = profile["k"]
    if k < k_min:
        penalties += min(10, (k_min - k) * 0.1)
        
    score = max(0, min(100, 100 - penalties))
    
    # English feedback lists for reliable translation
    feedback = []
    if not season_match:
        feedback.append(f"Not optimal for {season} season (prefers {profile['season']}).")
    if not region_match:
        feedback.append(f"Not recommended for {region} India region.")
    if ph < ph_min:
        feedback.append(f"Soil pH is acidic ({ph:.1f}) - below target ({ph_min}). Add lime/chuna.")
    elif ph > ph_max:
        feedback.append(f"Soil pH is alkaline ({ph:.1f}) - above target ({ph_max}). Add gypsum.")
    if moist < m_min:
        feedback.append("Soil moisture is dry. Immediate irrigation is recommended.")
    elif moist > m_max:
        feedback.append("Soil is waterlogged. Please ensure proper drainage.")
    if ec > ec_max:
        feedback.append("High soil salinity limits root nutrient uptake.")
    if n < n_min:
        feedback.append("Low Nitrogen. Supplement with organic compost or urea.")
    if p < p_min:
        feedback.append("Low Phosphorus. Apply Single Super Phosphate (SSP) or bone meal.")
    if k < k_min:
        feedback.append("Low Potassium. Add organic wood ash or muriate of potash (MOP).")
        
    if not feedback:
        feedback.append("Soil parameters are highly optimal for this crop!")
        
    return int(score), {
        "name_en": profile["name_en"],
        "name_hi": profile["name_hi"],
        "score": int(score),
        "season": profile["season"],
        "regions": ", ".join(profile["regions"]),
        "feedback": " ".join(feedback),
        "ph_range": f"{ph_min} - {ph_max}",
        "moisture_range": f"{m_min}% - {m_max}%"
    }

# ─── ICAR Advisory Engine ────────────────────────────
def get_advisory(data):
    """
    Generate English advisories (for dashboard translation) and Hindi advisories (for Twilio).
    Based on ICAR soil health card guidelines.
    Returns: (english_list, hindi_list, issues_list)
    """
    issues = []
    english = []
    hindi = []

    n  = data.get("n", 0)
    p  = data.get("p", 0)
    k  = data.get("k", 0)
    ph = data.get("ph", 7.0)
    ec = data.get("ec", 0.0)
    moist   = data.get("moisture", 0)
    mq135   = data.get("mq135", 0)
    raining = data.get("raining", False)

    # ── Nitrogen ─────────────────────────────────────
    if n < 150:
        issues.append("Nitrogen deficient")
        english.append("Nitrogen level is low: Apply 25 kg Urea or 50 kg DAP per bigha to boost vegetative growth.")
        hindi.append("नाइट्रोजन की कमी है। 25 किलो यूरिया या 50 किलो डीएपी प्रति बीघा डालने की आवश्यकता है।")
    elif n > 500:
        issues.append("Nitrogen excess")
        english.append("Nitrogen level is high: Avoid applying Urea this week to prevent crop leaf burn.")
        hindi.append("नाइट्रोजन अधिक है। इस बार यूरिया बिल्कुल न डालें।")

    # ── Phosphorus ───────────────────────────────────
    if p < 11:
        issues.append("Phosphorus deficient")
        english.append("Phosphorus level is low: Apply 20 kg Single Super Phosphate (SSP) per bigha for root strength.")
        hindi.append("फास्फोरस की कमी है। जड़ की मजबूती के लिए 20 किलो एसएसपी प्रति बीघा डालें।")
    elif p > 80:
        issues.append("Phosphorus excess")
        english.append("Phosphorus level is high: Do not add SSP or phosphate fertilizers this cycle.")
        hindi.append("फास्फोरस पर्याप्त है। इस बार एसएसपी या फास्फेट खाद डालने की आवश्यकता नहीं है।")

    # ── Potassium ────────────────────────────────────
    if k < 110:
        issues.append("Potassium deficient")
        english.append("Potassium level is low: Add 10 kg MOP per bigha to improve yield and disease resistance.")
        hindi.append("पोटैशियम की कमी है। फसल के अच्छे विकास के लिए 10 किलो एमओपी प्रति बीघा डालें।")
    elif k > 280:
        issues.append("Potassium excess")
        english.append("Potassium level is high: Stop adding potash or MOP fertilizers.")
        hindi.append("पोटैशियम अधिक है। एमओपी या पोटाश का उपयोग न करें।")

    # ── pH ───────────────────────────────────────────
    if ph < 5.5:
        issues.append("Soil highly acidic")
        english.append(f"Soil pH is highly acidic ({ph:.1f}): Apply 2 quintals of lime per acre to balance soil pH.")
        hindi.append(f"मिट्टी अत्यधिक अम्लीय (pH {ph:.1f}) है। 2 क्विंटल चूना प्रति एकड़ खेतों में डालें।")
    elif 5.5 <= ph < 6.0:
        issues.append("Soil mildly acidic")
        english.append(f"Soil pH is mildly acidic ({ph:.1f}): Apply 1 quintal of lime per acre.")
        hindi.append(f"मिट्टी थोड़ी अम्लीय (pH {ph:.1f}) है। 1 क्विंटल चूना डालना सही रहेगा।")
    elif ph > 7.5:
        issues.append("Soil alkaline")
        english.append(f"Soil is alkaline ({ph:.1f}): Apply 2 quintals of gypsum per acre to balance pH.")
        hindi.append(f"मिट्टी क्षारीय (pH {ph:.1f}) है। 2 क्विंटल जिप्सम प्रति एकड़ से सुधार करें।")

    # ── EC / Salinity ────────────────────────────────
    if ec > 4.0:
        issues.append("High salinity")
        english.append(f"Salinity is high (EC: {ec:.2f} mS/cm): Flush field with clean water and improve drainage.")
        hindi.append(f"लवणता (EC: {ec:.2f} mS/cm) अधिक है। खेत में पानी भरकर अच्छे से जलनिकास करें।")

    # ── Moisture / Irrigation ─────────────────────────
    if raining:
        english.append("It is raining: Stop irrigation. Water pump is automatically turned off.")
        hindi.append("आज बारिश हो रही है। सिंचाई बंद रखें। पंप स्वचालित रूप से बंद कर दिया गया है।")
    elif moist < 30:
        english.append(f"Soil is dry ({moist:.0f}%): Light irrigation is required today.")
        hindi.append(f"मिट्टी सूखी ({moist:.0f}%) है। आज खेतों में हल्की सिंचाई अवश्य करें।")
    elif moist > 70:
        english.append(f"Soil moisture is high ({moist:.0f}%): Irrigation is not required.")
        hindi.append(f"मिट्टी में पर्याप्त नमी ({moist:.0f}%) है। अभी सिंचाई की आवश्यकता नहीं है।")

    # ── Ammonia / MQ135 ───────────────────────────────
    if mq135 > 600:
        issues.append("High ammonia gas")
        english.append("Ammonia levels are high: Reduce nitrogenous fertilizer dosage to protect crop health.")
        hindi.append("खेत में अमोनिया गैस अधिक है। यूरिया का अत्यधिक छिड़काव अभी रोकें।")

    # ── If everything is fine ─────────────────────────
    if not english:
        english.append("Soil health parameters are optimal: No action needed this week.")
        hindi.append("आपकी मिट्टी का स्वास्थ्य बहुत अच्छा है। कोई विशेष उपाय करने की आवश्यकता नहीं है।")

    return english, hindi, issues

# ─── Twilio Voice Call ────────────────────────────────
def make_call(hindi_text):
    """Trigger Twilio voice call with Hindi TTS advisory."""
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say language="hi-IN" voice="Polly.Aditi">
    Namaste. Yeh Mitti hai, aapka mitti ka sahayak.
    {hindi_text}
    Dhanyavaad. Apni fasal ka dhyan rakhein.
  </Say>
</Response>"""
        call = client.calls.create(
            twiml=twiml,
            to=FARMER_PHONE,
            from_=TWILIO_FROM
        )
        print(f"Call initiated: {call.sid}")
        return call.sid
    except Exception as e:
        print(f"Twilio error: {e}")
        return None

# ─── Dashboard HTML ───────────────────────────────────
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mitti — Soil Intelligence</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
  *{margin:0;padding:0;box-sizing:border-box;}
  body{font-family:'Inter',sans-serif;background:#0a0f0a;color:#e8f5e9;min-height:100vh;}

  .header {
    background: #0d2b0d;
    padding: 1.25rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #2d5a2d;
    flex-wrap: wrap;
    gap: 1rem;
  }
  .header-left {
    display: flex;
    flex-direction: column;
  }
  .logo {
    font-size: 1.8rem;
    font-weight: 900;
    color: #4caf50;
    letter-spacing: -0.5px;
  }
  .tagline {
    font-size: 0.75rem;
    color: #558b2f;
    font-style: italic;
    margin-top: 2px;
  }
  .greeting {
    font-size: 0.9rem;
    color: #a5d6a7;
    margin-top: 0.5rem;
    font-weight: 600;
  }
  .header-right {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }
  
  /* Google Translate override styling */
  #google_translate_element {
    display: inline-block;
  }
  .goog-logo-link { display: none !important; }
  .goog-te-gadget { color: transparent !important; font-size: 0px !important; }
  .goog-te-gadget .goog-te-combo {
    background: #111f11 !important;
    color: #e8f5e9 !important;
    border: 1px solid #4caf50 !important;
    border-radius: 8px !important;
    padding: 6px 12px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    cursor: pointer !important;
    outline: none;
  }
  .goog-te-banner-frame { display: none !important; }
  body { top: 0px !important; }

  .demo-btn {
    background: #111f11;
    border: 1px solid #2d5a2d;
    color: #81c784;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 0.85rem;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.2s;
  }
  .demo-btn:hover {
    border-color: #4caf50;
    background: #1a301a;
    color: #e8f5e9;
  }

  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
    gap:1.5rem;padding:2rem;max-width:1400px;margin:0 auto;}

  .card{background:#111f11;border:1px solid #2d5a2d;border-radius:16px;
    padding:1.5rem;transition:transform .2s;display:flex;flex-direction:column;}
  .card:hover{transform:translateY(-4px);border-color:#4caf50;}
  .card h2{font-size:.75rem;text-transform:uppercase;letter-spacing:2px;
    color:#558b2f;margin-bottom:1rem;}

  .metric{display:flex;justify-content:space-between;align-items:center;
    padding:.75rem 0;border-bottom:1px solid #1a3a1a;}
  .metric:last-child{border:none;}
  .metric-label{color:#81c784;font-size:.9rem;}
  .metric-value{font-size:1.4rem;font-weight:700;color:#4caf50;}
  .metric-unit{font-size:.75rem;color:#558b2f;margin-left:.25rem;}

  .status-good{color:#4caf50;}
  .status-warn{color:#ff9800;}
  .status-bad{color:#f44336;}

  .chart-container{position:relative;margin-top:1.25rem;height:140px;width:100%;}

  .advisory{background:#0d2b0d;border:2px solid #4caf50;
    border-radius:16px;padding:1.5rem;}
  .advisory h2{color:#4caf50;font-size:1rem;margin-bottom:0.75rem;}
  .advisory-list {
    list-style: none;
    margin-bottom: 1rem;
  }
  .advisory-item {
    font-size: 0.95rem;
    line-height: 1.5;
    color: #c8e6c9;
    background: #0a1f0a;
    padding: 0.5rem 0.75rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    border-left: 3px solid #4caf50;
  }
  .advisory-english{font-size:.8rem;color:#558b2f;font-style:italic;}

  .wisdom{background:#1a1a0a;border:1px solid #827717;
    border-radius:16px;padding:1.5rem;}
  .wisdom h2{color:#cddc39;font-size:.75rem;text-transform:uppercase;
    letter-spacing:2px;margin-bottom:0.75rem;}
  .wisdom p{color:#e6ee9c;line-height:1.6;font-size:.95rem;}
  .wisdom-label{color:#827717;font-size:.7rem;margin-bottom:.5rem;display:block;}

  .pump-on{color:#4caf50;animation:pulse 1s infinite;}
  .pump-off{color:#558b2f;}
  @keyframes pulse{0%,100%{opacity:1;}50%{opacity:.5;}}

  .timestamp{text-align:center;color:#2d5a2d;font-size:.75rem;padding:2rem 1rem;}

  .call-btn{display:block;margin:1rem 0 0 0;padding:0.75rem 1.5rem;
    background:#4caf50;color:#000;font-weight:700;border:none;
    border-radius:10px;font-size:0.9rem;cursor:pointer;text-decoration:none;
    text-align:center;}
  .call-btn:hover{background:#66bb6a;}

  /* Crop Selector Styling */
  .crop-btn {
    background: #111f11;
    border: 1px solid #2d5a2d;
    color: #e8f5e9;
    border-radius: 12px;
    padding: 0.75rem 1rem;
    cursor: pointer;
    text-align: left;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.2s ease;
    width: 100%;
  }
  .crop-btn:hover {
    border-color: #4caf50;
    background: #1a301a;
  }
  .crop-btn.active {
    border-color: #4caf50;
    background: #254a25;
    box-shadow: 0 0 10px rgba(76, 175, 80, 0.2);
  }
  .crop-title {
    font-size: 0.85rem;
    font-weight: 600;
    line-height: 1.3;
  }
  .crop-badge {
    background: #1a3a1a;
    border: 1px solid #2d5a2d;
    padding: 0.25rem 0.5rem;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: bold;
    color: #4caf50;
  }
  .suitability-high { color: #4caf50; border-color: #4caf50; background: rgba(76, 175, 80, 0.1); }
  .suitability-medium { color: #ff9800; border-color: #ff9800; background: rgba(255, 152, 0, 0.1); }
  .suitability-low { color: #f44336; border-color: #f44336; background: rgba(244, 67, 54, 0.1); }

  .filter-select {
    background: #111f11; 
    color: #e8f5e9; 
    border: 1px solid #2d5a2d; 
    padding: 6px 12px; 
    border-radius: 8px; 
    font-size: 0.85rem; 
    cursor: pointer;
    outline: none;
  }
  .filter-select:focus {
    border-color: #4caf50;
  }
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <span class="logo">🌱 Mitti <span style="font-weight:300;font-size:1.1rem;color:#81c784;">Soil Intelligence</span></span>
    <span class="tagline">"The farmer who stayed. And the generation that forgot."</span>
    <span class="greeting" id="greetingText">{{greeting}}</span>
  </div>
  <div class="header-right">
    <div id="google_translate_element"></div>
    <a href="/demo" class="demo-btn">🧪 Load Demo Data</a>
  </div>
</div>

<div class="grid">

  <!-- NPK Card -->
  <div class="card">
    <h2>🧪 Soil NPK</h2>
    <div class="metric">
      <span class="metric-label">Nitrogen (N)</span>
      <span class="metric-value
        {% if data.n < 150 %}status-bad
        {% elif data.n > 500 %}status-warn
        {% else %}status-good{% endif %}">
        {{data.n}}<span class="metric-unit">mg/kg</span>
      </span>
    </div>
    <div class="metric">
      <span class="metric-label">Phosphorus (P)</span>
      <span class="metric-value
        {% if data.p < 11 %}status-bad
        {% elif data.p > 80 %}status-warn
        {% else %}status-good{% endif %}">
        {{data.p}}<span class="metric-unit">mg/kg</span>
      </span>
    </div>
    <div class="metric">
      <span class="metric-label">Potassium (K)</span>
      <span class="metric-value
        {% if data.k < 110 %}status-bad
        {% elif data.k > 280 %}status-warn
        {% else %}status-good{% endif %}">
        {{data.k}}<span class="metric-unit">mg/kg</span>
      </span>
    </div>
    <div class="chart-container">
      <canvas id="npkChart"></canvas>
    </div>
  </div>

  <!-- Soil Health Card -->
  <div class="card">
    <h2>🌍 Soil Health</h2>
    <div class="metric">
      <span class="metric-label">pH Level</span>
      <span class="metric-value
        {% if data.ph < 5.5 or data.ph > 7.5 %}status-bad
        {% elif data.ph < 6.0 %}status-warn
        {% else %}status-good{% endif %}">
        {{data.ph}}</span>
    </div>
    <div class="metric">
      <span class="metric-label">EC (Salinity)</span>
      <span class="metric-value
        {% if data.ec > 4 %}status-bad
        {% elif data.ec > 2 %}status-warn
        {% else %}status-good{% endif %}">
        {{data.ec}}<span class="metric-unit">mS/cm</span>
      </span>
    </div>
    <div class="metric">
      <span class="metric-label">Moisture</span>
      <span class="metric-value
        {% if data.moisture < 30 %}status-bad
        {% elif data.moisture > 70 %}status-warn
        {% else %}status-good{% endif %}">
        {{data.moisture}}<span class="metric-unit">%</span>
      </span>
    </div>
    <div class="chart-container">
      <canvas id="healthChart"></canvas>
    </div>
  </div>

  <!-- Environment & Irrigation Card -->
  <div class="card">
    <h2>🌤️ Env & Irrigation</h2>
    <div class="metric">
      <span class="metric-label">Temperature</span>
      <span class="metric-value status-good">{{data.temp}}<span class="metric-unit">°C</span></span>
    </div>
    <div class="metric">
      <span class="metric-label">Humidity</span>
      <span class="metric-value status-good">{{data.humidity}}<span class="metric-unit">%</span></span>
    </div>
    <div class="metric">
      <span class="metric-label">NH₃ Ammonia</span>
      <span class="metric-value {% if data.mq135 > 600 %}status-bad{% else %}status-good{% endif %}">
        {% if data.mq135 > 600 %}Alert ⚠️{% else %}Normal{% endif %}
      </span>
    </div>
    <div class="metric">
      <span class="metric-label">Rain / Pump</span>
      <span class="metric-value">
        {% if data.raining %}Rain 🌧️{% else %}Clear ☀️{% endif %}
        &nbsp;/&nbsp;
        <span class="{% if data.pump %}pump-on{% else %}pump-off{% endif %}">
          {% if data.pump %}PUMP ON{% else %}OFF{% endif %}
        </span>
      </span>
    </div>
  </div>

  <!-- Crop Suitability Section (Full Width) -->
  <div class="card" style="grid-column: 1 / -1;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; border-bottom: 1px solid #1a3a1a; padding-bottom: 0.75rem; margin-bottom: 1rem;">
      <div>
        <h2>🌾 Season & Crop Suitability Index</h2>
      </div>
      
      <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
        <!-- Region Selector -->
        <div>
          <span style="font-size: 0.75rem; color: #558b2f; margin-right: 0.25rem; font-weight: bold; text-transform: uppercase;">Region:</span>
          <select id="regionSelect" onchange="loadRecommendations()" class="filter-select">
            <option value="North" selected>North India</option>
            <option value="South">South India</option>
            <option value="East">East India</option>
            <option value="West">West India</option>
          </select>
        </div>
        
        <!-- Season Selector -->
        <div>
          <span style="font-size: 0.75rem; color: #558b2f; margin-right: 0.25rem; font-weight: bold; text-transform: uppercase;">Season:</span>
          <select id="seasonSelect" onchange="loadRecommendations()" class="filter-select">
            <option value="Kharif">Kharif</option>
            <option value="Rabi" selected>Rabi</option>
            <option value="Zaid">Zaid</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Crop Buttons Grid -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 0.75rem; margin-bottom: 1rem;">
      <button class="crop-btn" onclick="selectCrop('Wheat')" id="btn-Wheat">
        <span class="crop-title">Wheat<br></span>
        <span class="crop-badge" id="badge-Wheat">0%</span>
      </button>
      <button class="crop-btn" onclick="selectCrop('Paddy')" id="btn-Paddy">
        <span class="crop-title">Paddy / Rice<br></span>
        <span class="crop-badge" id="badge-Paddy">0%</span>
      </button>
      <button class="crop-btn" onclick="selectCrop('Cotton')" id="btn-Cotton">
        <span class="crop-title">Cotton<br></span>
        <span class="crop-badge" id="badge-Cotton">0%</span>
      </button>
      <button class="crop-btn" onclick="selectCrop('Mustard')" id="btn-Mustard">
        <span class="crop-title">Mustard<br></span>
        <span class="crop-badge" id="badge-Mustard">0%</span>
      </button>
      <button class="crop-btn" onclick="selectCrop('Maize')" id="btn-Maize">
        <span class="crop-title">Maize<br></span>
        <span class="crop-badge" id="badge-Maize">0%</span>
      </button>
      <button class="crop-btn" onclick="selectCrop('Potato')" id="btn-Potato">
        <span class="crop-title">Potato<br></span>
        <span class="crop-badge" id="badge-Potato">0%</span>
      </button>
    </div>

    <!-- Suitability Details -->
    <div id="cropDetailCard" style="background: #0a140a; border: 1px dashed #2d5a2d; border-radius: 12px; padding: 1rem; display: none;">
      <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
        <div>
          <h3 id="detailCropName" style="color: #4caf50; font-size: 1.1rem; font-weight: 700;">Crop Name</h3>
          <span style="font-size: 0.75rem; color: #558b2f;" id="detailCropSeason">Season Info</span>
        </div>
        <span class="crop-badge" style="font-size: 0.95rem; padding: 0.35rem 0.75rem;" id="detailCropScore">0% Match</span>
      </div>
      
      <div style="margin: 0.5rem 0; font-size: 0.9rem; line-height: 1.4; color: #c8e6c9;">
        <p id="detailCropFeedback"></p>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 0.5rem; font-size: 0.75rem; background: #111f11; padding: 0.5rem; border-radius: 6px;">
        <div><strong style="color: #558b2f;">Ideal pH:</strong> <span id="detailPreferredPh"></span></div>
        <div><strong style="color: #558b2f;">Ideal Moisture:</strong> <span id="detailPreferredMoisture"></span></div>
      </div>
    </div>
  </div>

  <!-- Advisory Panel -->
  <div class="advisory">
    <h2>📞 Weekly Action Advisory</h2>
    <ul class="advisory-list">
      {% for item in advisories %}
        <li class="advisory-item">{{item}}</li>
      {% endfor %}
    </ul>
    <div class="advisory-english">Issues detected: {{english}}</div>
    <a href="/call" class="call-btn">📞 Call Farmer Now</a>
  </div>

  <!-- Traditional Wisdom Panel -->
  <div class="wisdom">
    <span class="wisdom-label">🏺 ANCESTRAL WISDOM — 5,000 years of knowledge</span>
    <p>{{wisdom}}</p>
  </div>

</div>

<div class="timestamp">
  Last updated: {{timestamp}} &nbsp;|&nbsp; Mitti v2.5 — Samsung Solve for Tomorrow 2025
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
  // NPK Chart
  const ctxNpk = document.getElementById('npkChart').getContext('2d');
  new Chart(ctxNpk, {
    type: 'bar',
    data: {
      labels: ['N', 'P', 'K'],
      datasets: [{
        data: [{{data.n}}, {{data.p}}, {{data.k}}],
        backgroundColor: [
          'rgba(76, 175, 80, 0.4)',
          'rgba(255, 152, 0, 0.4)',
          'rgba(33, 150, 243, 0.4)'
        ],
        borderColor: [
          '#4caf50',
          '#ff9800',
          '#2196f3'
        ],
        borderWidth: 1.5,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#81c784', font: { size: 10 } }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#81c784', font: { size: 11, weight: 'bold' } }
        }
      }
    }
  });

  // Health Radar Chart
  const ctxHealth = document.getElementById('healthChart').getContext('2d');
  new Chart(ctxHealth, {
    type: 'radar',
    data: {
      labels: ['pH (x10)', 'EC (x20)', 'Moisture %'],
      datasets: [{
        data: [{{data.ph}} * 10, {{data.ec}} * 20, {{data.moisture}}],
        backgroundColor: 'rgba(76, 175, 80, 0.15)',
        borderColor: '#4caf50',
        pointBackgroundColor: '#81c784',
        borderWidth: 1.5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        r: {
          angleLines: { color: 'rgba(255, 255, 255, 0.08)' },
          grid: { color: 'rgba(255, 255, 255, 0.08)' },
          pointLabels: { color: '#81c784', font: { size: 10 } },
          ticks: { display: false },
          suggestedMin: 0,
          suggestedMax: 100
        }
      }
    }
  });

  // Recommendation engine client loader
  let currentRecommendations = {};

  function loadRecommendations() {
    const season = document.getElementById('seasonSelect').value;
    const region = document.getElementById('regionSelect').value;
    
    fetch(`/recommend?season=${season}&region=${region}`)
      .then(res => res.json())
      .then(data => {
        currentRecommendations = data;
        for (const [crop, details] of Object.entries(data)) {
          const badge = document.getElementById(`badge-${crop}`);
          if (badge) {
            badge.innerText = `${details.score}%`;
            badge.className = 'crop-badge';
            if (details.score >= 80) {
              badge.classList.add('suitability-high');
            } else if (details.score >= 50) {
              badge.classList.add('suitability-medium');
            } else {
              badge.classList.add('suitability-low');
            }
          }
        }
        
        const activeBtn = document.querySelector('.crop-btn.active');
        if (activeBtn) {
          const cropId = activeBtn.id.replace('btn-', '');
          displayCropDetails(cropId);
        } else {
          selectCrop('Wheat');
        }
      });
  }

  function selectCrop(cropId) {
    document.querySelectorAll('.crop-btn').forEach(btn => btn.classList.remove('active'));
    const btn = document.getElementById(`btn-${cropId}`);
    if (btn) btn.classList.add('active');
    displayCropDetails(cropId);
  }

  function displayCropDetails(cropId) {
    const details = currentRecommendations[cropId];
    if (!details) return;
    
    document.getElementById('cropDetailCard').style.display = 'block';
    document.getElementById('detailCropName').innerHTML = `${details.name_en}`;
    document.getElementById('detailCropSeason').innerText = `Preferred Season: ${details.season} | Traditional Regions: ${details.regions}`;
    
    const scoreBadge = document.getElementById('detailCropScore');
    scoreBadge.innerText = `${details.score}% Match`;
    scoreBadge.className = 'crop-badge';
    if (details.score >= 80) {
      scoreBadge.classList.add('suitability-high');
    } else if (details.score >= 50) {
      scoreBadge.classList.add('suitability-medium');
    } else {
      scoreBadge.classList.add('suitability-low');
    }
    
    document.getElementById('detailCropFeedback').innerText = details.feedback;
    document.getElementById('detailPreferredPh').innerText = details.ph_range;
    document.getElementById('detailPreferredMoisture').innerText = details.moisture_range;
  }

  window.onload = () => {
    loadRecommendations();
  };
</script>

<!-- Google Translate Widget -->
<script type="text/javascript">
function googleTranslateElementInit() {
  new google.translate.TranslateElement({
    pageLanguage: 'en',
    includedLanguages: 'hi,pa,te,ta,bn,mr,gu,kn,ml,or,as,ur',
    layout: google.translate.TranslateElement.InlineLayout.SIMPLE
  }, 'google_translate_element');
}
</script>
<script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>

</body>
</html>
"""

# ─── Routes ───────────────────────────────────────────

@app.route("/data", methods=["POST"])
def receive_data():
    """Receive sensor data from ESP32."""
    global latest, last_call_time
    data = request.get_json()
    if not data:
        return jsonify({"error": "no data"}), 400

    latest.update(data)
    latest["timestamp"] = datetime.now().strftime("%d %b %Y, %I:%M %p")
    print(f"[{latest['timestamp']}] Data received: {data}")

    # Auto call trigger logic when critical issues are found
    english_list, hindi_list, english_issues = get_advisory(latest)
    current_time = time.time()
    
    # Trigger call if soil health issues exist and 5-min cooldown has elapsed
    if english_issues and (current_time - last_call_time > 300):
        hindi_text = " ".join(hindi_list)
        print(f"[{latest['timestamp']}] Auto-call check: issues found: {english_issues}")
        if TWILIO_SID != "YOUR_TWILIO_ACCOUNT_SID" and TWILIO_TOKEN != "YOUR_TWILIO_AUTH_TOKEN":
            print(f"Initiating automatic Twilio call...")
            sid = make_call(hindi_text)
            if sid:
                last_call_time = current_time
                print(f"Auto-call triggered successfully. SID: {sid}")
            else:
                print("Auto-call failed.")
        else:
            print("Twilio credentials not configured. Skipping auto-call trigger.")

    return jsonify({"status": "ok"}), 200


@app.route("/")
def dashboard():
    """Serve the live dashboard."""
    english_list, hindi_list, english_issues = get_advisory(latest)
    english_text = ", ".join(english_issues) if english_issues else "Soil health good"
    
    # Dynamic random wisdom fact selection
    wisdom = generate_wisdom()
    
    # Dynamic greeting
    greeting = get_greeting()
    
    return render_template_string(
        DASHBOARD_HTML,
        data=latest,
        advisories=english_list,
        english=english_text,
        wisdom=wisdom,
        greeting=greeting,
        timestamp=latest.get("timestamp", "Not yet received")
    )


@app.route("/recommend")
def recommend_crops():
    """Return crop suitability calculations based on season & region."""
    season = request.args.get("season", "Rabi")
    region = request.args.get("region", "North")
    
    crops = ["Wheat", "Paddy", "Cotton", "Mustard", "Maize", "Potato"]
    results = {}
    for crop in crops:
        score, details = calculate_suitability(crop, latest, season, region)
        results[crop] = details
        
    return jsonify(results)


@app.route("/advisory")
def advisory_json():
    """Return advisory as JSON."""
    english_list, hindi_list, english_issues = get_advisory(latest)
    english_text = ", ".join(english_issues) if english_issues else "Soil health good"
    wisdom = generate_wisdom()
    return jsonify({
        "hindi": " ".join(hindi_list),
        "english": " ".join(english_list),
        "wisdom": wisdom,
        "data": latest
    })


@app.route("/call")
def call_farmer():
    """Trigger voice call to farmer."""
    _, hindi_list, _ = get_advisory(latest)
    hindi_text = " ".join(hindi_list)
    sid = make_call(hindi_text)
    if sid:
        return jsonify({"status": "call initiated", "sid": sid})
    return jsonify({"status": "call failed"}), 500


@app.route("/demo")
def demo_data():
    """Load demo data for testing without hardware."""
    global latest
    latest = {
        "n": 120, "p": 8, "k": 95,
        "moisture": 22, "ec": 1.2, "ph": 5.8,
        "temp": 34, "humidity": 65,
        "mq135": 720, "raining": False,
        "pump": True,
        "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }
    return jsonify({"status": "demo data loaded", "data": latest})


if __name__ == "__main__":
    print("=" * 50)
    print("  MITTI Backend Server")
    print("  Dashboard -> http://localhost:5000")
    print("  Demo data -> http://localhost:5000/demo")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)

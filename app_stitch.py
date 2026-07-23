"""
MITTI — Backend Server
Flask + Crop Suitability Engine + Twilio Voice Call + Dynamic Wisdom
Samsung Solve for Tomorrow 2025
"""

from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from twilio.rest import Client
import json, os, time, random
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "mitti_secret_key_987"

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

# ─── State-Specific Climate Mappings ──────────────────
STATE_TO_REGION = {
    "Punjab": "North", "Haryana": "North", "Himachal Pradesh": "North", "Uttarakhand": "North",
    "Uttar Pradesh": "North", "Delhi": "North", "Jammu & Kashmir": "North", "Ladakh": "North",
    "Chandigarh": "North",
    "Tamil Nadu": "South", "Kerala": "South", "Karnataka": "South", "Andhra Pradesh": "South",
    "Telangana": "South", "Puducherry": "South", "Lakshadweep": "South",
    "Andaman & Nicobar Islands": "South",
    "West Bengal": "East", "Bihar": "East", "Jharkhand": "East", "Odisha": "East",
    "Sikkim": "East", "Assam": "East", "Meghalaya": "East", "Tripura": "East",
    "Mizoram": "East", "Manipur": "East", "Nagaland": "East", "Arunachal Pradesh": "East",
    "Rajasthan": "West", "Gujarat": "West", "Maharashtra": "West", "Goa": "West",
    "Madhya Pradesh": "West", "Chhattisgarh": "West",
    "Dadra & Nagar Haveli and Daman & Diu": "West"
}

STATE_PHENOMENA = {
    "Rajasthan": {
        "Kharif": {"icon": "☀️⚠️", "title": "Arid Heat & Dry Spell", "desc": "High evaporation rates. Protect crops like Bajra and Soybean with mulching and optimal sprinkler irrigation. Focus on rainwater harvesting."},
        "Rabi": {"icon": "🌾🌧️", "title": "Mawat Winter Showers", "desc": "Precious winter rains beneficial for mustard, cumin, and gram. Minimizes irrigation requirements for early winter crops."},
        "Zaid": {"icon": "🌡️🌬️", "title": "Severe Loo Winds", "desc": "Hot, dry desert winds. Searing heat dries soil instantly. Protect summer pulses and melons with deep mulching."}
    },
    "Punjab": {
        "Kharif": {"icon": "🌧️", "title": "Southwest Monsoon", "desc": "Heavy rains support paddy transplantation. Manage tubewell operation based on rainfall patterns."},
        "Rabi": {"icon": "🌨️🌾", "title": "Western Disturbances (Mahawat)", "desc": "Mediterranean winds bring winter rain, highly beneficial for wheat development. Keep checking for rust diseases."},
        "Zaid": {"icon": "🌡️", "title": "Dry Summer Loo", "desc": "Hot winds. Irrigate early morning. Straw mulching helps conserve moisture in vegetable beds."}
    },
    "Haryana": {
        "Kharif": {"icon": "🌧️", "title": "Southwest Monsoon Sowing", "desc": "Sowing season for paddy, maize, and cotton. Ensure field bunds are high to retain rainwater."},
        "Rabi": {"icon": "🌨️🌾", "title": "Western Disturbances", "desc": "Winter rain reduces wheat irrigation needs. Avoid excessive fertilizer spray during foggy days."},
        "Zaid": {"icon": "🌡️", "title": "Summer Heatwave & Loo", "desc": "Dry summer winds. Sowing of summer pulses requires light and frequent irrigations."}
    },
    "Uttar Pradesh": {
        "Kharif": {"icon": "🌧️", "title": "Southwest Monsoon", "desc": "Crucial for paddy and sugarcane growing. Watch for water logging in low-lying eastern UP fields."},
        "Rabi": {"icon": "🌨️", "title": "Winter Fog & Mahawat Rain", "desc": "Dense winter fog. Mild showers aid potato, mustard, and wheat. Monitor crops for early blight disease."},
        "Zaid": {"icon": "🌡️", "title": "Dry Summer Loo", "desc": "Dry winds. Good for summer mung and vegetables with adequate drip irrigation."}
    },
    "Tamil Nadu": {
        "Kharif": {"icon": "☀️🌧️", "title": "Southwest Monsoon Shadow & Kuruvai Sowing", "desc": "Mild rain. Kuruvai paddy sowing is active. Rely on canal/well irrigation. Good for coconut gardens."},
        "Rabi": {"icon": "🌧️⚠️", "title": "Northeast Monsoon (Peak Rain)", "desc": "Returning monsoon brings heavy rainfall and cyclone risks. Essential for Samba paddy. Ensure drainage channels are clear."},
        "Zaid": {"icon": "🥭🌧️", "title": "Pre-Monsoon Mango Showers", "desc": "Summer showers benefit mango orchards and coffee plantations. Excellent time for field preparation."}
    },
    "Kerala": {
        "Kharif": {"icon": "🌧️⚠️", "title": "Edavappathy (Southwest Monsoon)", "desc": "Torrential monsoon rains. Landslides and waterlogging risks. Ensure excellent drainage for rubber, black pepper, and tea plantations."},
        "Rabi": {"icon": "🌧️", "title": "Thulavarsham (Northeast Monsoon)", "desc": "Afternoon thunderstorms. Vital for plantation crops like cardamom, pepper, coffee, and coconut."},
        "Zaid": {"icon": "🥭🌧️", "title": "Mango Showers & Blossom Showers", "desc": "Pre-monsoon rains trigger coffee blossom blooming and support early cardamom growth."}
    },
    "Karnataka": {
        "Kharif": {"icon": "🌧️", "title": "Southwest Monsoon", "desc": "Abundant rain in coastal/hilly regions. Perfect for coffee, pepper, and rice sowing. Manage drainage."},
        "Rabi": {"icon": "☀️🌧️", "title": "Northeast Monsoon Transition", "desc": "Mild winter rains. Good for Rabi Paddy, ragi, and cardamoms in southern hills."},
        "Zaid": {"icon": "☕🥭", "title": "Blossom Showers (Pre-Monsoon)", "desc": "March-April showers trigger coffee buds opening and support cardamom. Sowing of summer pulses is optimal."}
    },
    "Andhra Pradesh": {
        "Kharif": {"icon": "🌧️", "title": "Southwest Monsoon", "desc": "Brings major rain. Sowing of paddy, groundnut, and cotton. Watch for pest infestations due to humidity."},
        "Rabi": {"icon": "🌧️⚠️", "title": "Northeast Monsoon Rain", "desc": "Coastal Andhra receives heavy showers. High risk of cyclone damage. Clear drainage canals in paddy fields."},
        "Zaid": {"icon": "☀️🌡️", "title": "Tropical Summer Heat", "desc": "High tropical heat. Protect groundnut and coconut trees with light evening irrigations."}
    },
    "Telangana": {
        "Kharif": {"icon": "🌧️", "title": "Southwest Monsoon Sowing", "desc": "Monsoon rain is crucial for cotton and paddy. Sowing cotton in black soils is highly active."},
        "Rabi": {"icon": "☀️", "title": "Dry Winter Rabi", "desc": "Dry and cool winter. Rabi paddy and maize rely on borewells. Keep check on water levels."},
        "Zaid": {"icon": "☀️🌡️", "title": "Severe Summer Heat", "desc": "High summer temperatures. Mulch vegetable crops to conserve moisture."}
    },
    "West Bengal": {
        "Kharif": {"icon": "🌧️⚠️", "title": "Southwest Monsoon & Flood Risk", "desc": "High monsoon rainfall. Sowing of Aman paddy. Watch out for inundation in Gangetic delta."},
        "Rabi": {"icon": "🌾", "title": "Cool Winter Residual Moisture", "desc": "Cool dry winters. Ideal for mustard, potato, and Boro paddy nursery sowing using river irrigation."},
        "Zaid": {"icon": "⛈️", "title": "Kalbaishakhi Nor'westers", "desc": "Sudden severe thunderstorms. Heavy rain helps jute sowing and supports tea leaves plucking."}
    },
    "Assam": {
        "Kharif": {"icon": "🌧️⚠️", "title": "Heavy Monsoon Floods", "desc": "Brahmaputra basin floods are common. Cultivate flood-tolerant paddy and protect tea gardens from waterlogging."},
        "Rabi": {"icon": "🌾", "title": "Mild Dry Winter", "desc": "Cool and dry winter. Good for mustard and winter vegetables. Tea bushes go into dormancy."},
        "Zaid": {"icon": "⛈️🌬️", "title": "Bordoisila Storms", "desc": "Pre-monsoon thunderstorms with strong winds. High rainfall helps tea flushes and jute sowing."}
    },
    "Gujarat": {
        "Kharif": {"icon": "🌧️", "title": "Southwest Monsoon", "desc": "Highly variable rainfall. Crucial for cotton, groundnut, and sesame. Ensure rainwater harvesting is active."},
        "Rabi": {"icon": "☀️", "title": "Dry Rabi Winter", "desc": "Cool, dry winter. Ideal for cumin (jeera), fennel (saunf), and castor under canal irrigation."},
        "Zaid": {"icon": "🌡️🌬️", "title": "Hot Summer Loo", "desc": "Dry summer winds. Sowing of summer moong and bajra requires frequent light watering."}
    },
    "Maharashtra": {
        "Kharif": {"icon": "🌧️", "title": "Southwest Monsoon Sowing", "desc": "Crucial for cotton, soybean, and sugarcane in Vidarbha and Marathwada. Keep track of dry spells."},
        "Rabi": {"icon": "☀️", "title": "Mild Rabi Sowing", "desc": "Dry winter. Great for Rabi sorghum (jowar), wheat, and gram under drip irrigation."},
        "Zaid": {"icon": "🥭🌊", "title": "Elephanta Showers (Konkan Coast)", "desc": "Pre-monsoon coastal rains benefit Alphonso mango orchards. High humidity increases pest risk."}
    },
    "Madhya Pradesh": {
        "Kharif": {"icon": "🌧️", "title": "Southwest Monsoon", "desc": "Sowing of soybean, maize, and pulses. Ensure fields do not puddle in clayey black soils."},
        "Rabi": {"icon": "🌾", "title": "Dry Winter Rabi Sowing", "desc": "Cool dry winter. Excellent for wheat and gram. Use sprinkler irrigation for gram to save water."},
        "Zaid": {"icon": "🌡️", "title": "Dry Summer Loo", "desc": "Intense summer heat. Protect soybean soils and summer vegetables with high mulching."}
    },
    "Bihar": {
        "Kharif": {"icon": "🌧️⚠️", "title": "Monsoon Flooding Risk", "desc": "North Bihar rivers commonly flood. Select flood-resistant rice varieties. Keep drainage channels open."},
        "Rabi": {"icon": "🌨️🌾", "title": "Winter Cold & Fog", "desc": "Cold winter winds. Perfect for wheat, maize, and potato. Monitor potato crop for late blight."},
        "Zaid": {"icon": "⛈️🌡️", "title": "Pre-Monsoon Showers & Loo", "desc": "Hot summer winds mixed with occasional nor'westers. Useful for summer maize and vegetables."}
    },
    "Odisha": {
        "Kharif": {"icon": "🌧️🌀", "title": "Monsoon Cyclones Risk", "desc": "Coastal cyclones common. Sowing of paddy, coconut, and jute. Select lodging-resistant paddy varieties."},
        "Rabi": {"icon": "☀️", "title": "Mild Rabi Winter", "desc": "Dry winter. Sowing of groundnut, mustard, and pulses. Utilize pond irrigation systems."},
        "Zaid": {"icon": "⛈️", "title": "Pre-Monsoon Nor'westers", "desc": "Violent summer storms. High rainfall helps summer vegetables and coconut trees."}
    }
}

# ─── Soil Science Fingerprint Database ────────────────
# Each soil type has characteristic sensor ranges based on ICAR / NBSS&LUP research.
# The classifier scores sensor readings against these profiles to identify soil type.
SOIL_TYPE_PROFILES = {
    "Alluvial Soil (Khadar - New)": {
        "ph": (6.5, 7.5), "ec": (0.2, 1.5), "moisture": (40, 65),
        "n": (120, 280), "k": (120, 220),
        "desc": "New alluvium found in active floodplains. Light, loamy, extremely fertile. Ideal for intensive agriculture like paddy and sugarcane."
    },
    "Alluvial Soil (Bhangar - Old)": {
        "ph": (7.0, 8.2), "ec": (0.5, 2.5), "moisture": (25, 50),
        "n": (90, 220), "k": (100, 180),
        "desc": "Older alluvium with calcareous 'kankar' nodules. Less porous and less fertile than Khadar. Needs good irrigation management."
    },
    "Black Soil (Regur)": {
        "ph": (7.0, 8.5), "ec": (0.5, 3.0), "moisture": (40, 70),
        "n": (80, 200), "k": (180, 350),
        "desc": "Derived from basalt lava. Very high clay & potassium. Excellent moisture retention. Deccan Plateau, Malwa, Saurashtra."
    },
    "Red & Yellow Soil": {
        "ph": (5.5, 6.8), "ec": (0.0, 1.0), "moisture": (20, 45),
        "n": (30, 110), "k": (60, 160),
        "desc": "Formed by weathering of crystalline rocks. Rich in iron, deficient in nitrogen & humus. Eastern/Southern Peninsular India."
    },
    "Laterite Soil": {
        "ph": (4.5, 5.5), "ec": (0.0, 1.0), "moisture": (50, 80),
        "n": (50, 150), "k": (40, 130),
        "desc": "Heavy leaching in high rainfall zones. Acidic, iron/aluminium-rich. Western Ghats, NE hills, parts of Odisha & Jharkhand."
    },
    "Arid / Desert Soil": {
        "ph": (7.5, 9.0), "ec": (1.5, 4.0), "moisture": (5, 25),
        "n": (15, 70), "k": (80, 200),
        "desc": "Sandy, saline, highly alkaline, very poor in nitrogen & humus. Thar Desert, Kutch, parts of Haryana & Punjab borderlands."
    },
    "Forest/Mountain Soil": {
        "ph": (5.0, 6.5), "ec": (0.0, 0.6), "moisture": (40, 70),
        "n": (140, 320), "k": (100, 200),
        "desc": "High humus & organic nitrogen from leaf litter. Acidic. Himalayan foothills, Western Ghats highlands, NE hills."
    },
    "Terai Soil": {
        "ph": (5.5, 6.8), "ec": (0.2, 1.2), "moisture": (50, 75),
        "n": (180, 350), "k": (80, 150),
        "desc": "Himalayan foothill soil. Extremely high in nitrogen and organic matter but poor in phosphate. Great for tall grasses and specific rice."
    },
    "Karewa Soil": {
        "ph": (6.5, 7.5), "ec": (0.3, 1.5), "moisture": (30, 55),
        "n": (100, 200), "k": (120, 220),
        "desc": "Unique lacustrine (lake) deposits found in the Kashmir valley. Highly fertile, crucial for cultivating Saffron, Almonds, and Walnuts."
    },
    "Saline/Alkaline Soil": {
        "ph": (8.0, 10.5), "ec": (4.0, 15.0), "moisture": (15, 55),
        "n": (40, 160), "k": (80, 220),
        "desc": "Excessive salts from poor drainage or seawater intrusion. Rann of Kutch, coastal belts, canal-irrigated arid zones."
    },
    "Peaty/Marshy Soil": {
        "ph": (3.5, 5.0), "ec": (0.0, 1.0), "moisture": (75, 98),
        "n": (150, 400), "k": (30, 110),
        "desc": "Waterlogged, highly acidic, extremely rich in organic matter. Kerala backwaters, Sundarbans, NE wetlands, Almora."
    },
    "Coastal Sandy Soil": {
        "ph": (6.5, 7.8), "ec": (1.5, 3.8), "moisture": (10, 40),
        "n": (20, 90), "k": (30, 130),
        "desc": "Sandy, moderately saline from sea spray. Low fertility. Coastal strips of Kerala, TN, AP, Odisha, Maharashtra, Gujarat."
    }
}

# ─── State-Level Soil Type Distribution (NBSS&LUP / ICAR data) ──
# Lists the soil types found in each state, ordered by prevalence.
# Used as a tiebreaker when sensor readings are ambiguous between 2+ types.
STATE_SOIL_TYPES = {
    "Punjab": ["Alluvial Soil (Bhangar - Old)", "Alluvial Soil (Khadar - New)", "Arid / Desert Soil", "Saline/Alkaline Soil"],
    "Haryana": ["Alluvial Soil (Bhangar - Old)", "Arid / Desert Soil", "Saline/Alkaline Soil"],
    "Uttar Pradesh": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Terai Soil"],
    "Uttarakhand": ["Forest/Mountain Soil", "Terai Soil"],
    "Bihar": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Terai Soil"],
    "West Bengal": ["Alluvial Soil (Khadar - New)", "Laterite Soil", "Peaty/Marshy Soil", "Coastal Sandy Soil"],
    "Assam": ["Alluvial Soil (Khadar - New)", "Laterite Soil", "Forest/Mountain Soil", "Peaty/Marshy Soil"],
    "Jammu & Kashmir": ["Forest/Mountain Soil", "Karewa Soil"],
    "Ladakh": ["Forest/Mountain Soil", "Arid / Desert Soil"],
    "Himachal Pradesh": ["Forest/Mountain Soil", "Terai Soil"],
    "Rajasthan": ["Arid / Desert Soil", "Alluvial Soil (Bhangar - Old)", "Saline/Alkaline Soil", "Black Soil (Regur)"],
    "Gujarat": ["Black Soil (Regur)", "Alluvial Soil (Bhangar - Old)", "Arid / Desert Soil", "Coastal Sandy Soil", "Saline/Alkaline Soil"],
    "Maharashtra": ["Black Soil (Regur)", "Laterite Soil", "Coastal Sandy Soil"],
    "Madhya Pradesh": ["Black Soil (Regur)", "Red & Yellow Soil", "Alluvial Soil (Bhangar - Old)", "Forest/Mountain Soil"],
    "Chhattisgarh": ["Red & Yellow Soil", "Laterite Soil", "Forest/Mountain Soil"],
    "Odisha": ["Red & Yellow Soil", "Laterite Soil", "Alluvial Soil (Khadar - New)", "Coastal Sandy Soil"],
    "Jharkhand": ["Red & Yellow Soil", "Laterite Soil"],
    "Andhra Pradesh": ["Red & Yellow Soil", "Black Soil (Regur)", "Alluvial Soil (Khadar - New)", "Coastal Sandy Soil"],
    "Telangana": ["Red & Yellow Soil", "Black Soil (Regur)"],
    "Karnataka": ["Red & Yellow Soil", "Laterite Soil", "Black Soil (Regur)", "Coastal Sandy Soil"],
    "Tamil Nadu": ["Red & Yellow Soil", "Laterite Soil", "Coastal Sandy Soil", "Alluvial Soil (Khadar - New)", "Peaty/Marshy Soil"],
    "Kerala": ["Laterite Soil", "Peaty/Marshy Soil", "Coastal Sandy Soil", "Forest/Mountain Soil"],
    "Sikkim": ["Forest/Mountain Soil", "Red & Yellow Soil"],
    "Meghalaya": ["Laterite Soil", "Forest/Mountain Soil", "Red & Yellow Soil"],
    "Tripura": ["Red & Yellow Soil", "Laterite Soil"],
    "Mizoram": ["Forest/Mountain Soil", "Red & Yellow Soil"],
    "Manipur": ["Red & Yellow Soil", "Forest/Mountain Soil"],
    "Nagaland": ["Forest/Mountain Soil", "Red & Yellow Soil"],
    "Arunachal Pradesh": ["Forest/Mountain Soil", "Red & Yellow Soil"],
    "Goa": ["Laterite Soil", "Coastal Sandy Soil"],
    "Delhi": ["Alluvial Soil (Bhangar - Old)"],
    "Chandigarh": ["Alluvial Soil (Bhangar - Old)"],
    "Dadra & Nagar Haveli and Daman & Diu": ["Coastal Sandy Soil", "Black Soil (Regur)"],
    "Lakshadweep": ["Coastal Sandy Soil"],
    "Puducherry": ["Coastal Sandy Soil", "Alluvial Soil (Khadar - New)"],
    "Andaman & Nicobar Islands": ["Forest/Mountain Soil", "Coastal Sandy Soil"]
}

# ─── Local Agricultural & Climate Phenomenon Engine ──
def get_local_phenomenon(region, season):
    """Return local weather/agricultural phenomena based on region and season."""
    if region == "North":
        if season == "Rabi":
            return {
                "icon": "🌨️",
                "title": "Western Disturbances (Mahawat)",
                "desc": "Winter showers caused by Mediterranean winds. Highly vital for Rabi wheat and mustard. Reduces irrigation needs."
            }
        elif season == "Zaid":
            return {
                "icon": "🌡️",
                "title": "Loo Winds Active",
                "desc": "Strong, dry, hot summer winds. Searing heat dries soil. Protect summer melons and gourds with high mulching and early morning irrigation."
            }
        else: # Kharif
            return {
                "icon": "🌧️",
                "title": "Southwest Monsoon Sowing",
                "desc": "Main rainy season. Optimal sowing window for Rice, Maize, and Cotton. Avoid stagnant water in clay soil fields."
            }
    elif region == "South":
        if season == "Kharif":
            return {
                "icon": "🌧️",
                "title": "Southwest Monsoon Sowing",
                "desc": "Main rainy season starting in June. Vital for sowing paddy nurseries, cotton, and long-duration sugarcane. Keep water drainage channels clear."
            }
        elif season == "Rabi":
            return {
                "icon": "🌧️",
                "title": "Northeast Monsoon (Returning Monsoon)",
                "desc": "Tamil Nadu and Andhra Pradesh receive peak rainfall. Prime season for Rabi Paddy and Groundnut. Ensure drainage is clear."
            }
        else: # Zaid
            return {
                "icon": "🥭🌧️",
                "title": "Mango Showers & Blossom Showers",
                "desc": "Pre-monsoon summer showers (March to May). Ripens mango crops early and prevents blossom drop. Essential for coffee buds blooming."
            }
    elif region == "East":
        if season == "Kharif":
            return {
                "icon": "🌧️⚠️",
                "title": "Monsoon Flooding Risk",
                "desc": "High intensity rainfall. Risk of waterlogging. Select flood-tolerant paddy varieties (e.g. Swarna Sub1) and keep drain trenches open."
            }
        elif season == "Zaid":
            return {
                "icon": "⛈️",
                "title": "Kalbaishakhi / Bordoisila Storms",
                "desc": "Severe localized pre-monsoon thunderstorms. Sudden heavy rains help jute germination and Boro paddy growth."
            }
        else: # Rabi
            return {
                "icon": "🌾",
                "title": "Cool Winter Residual Moisture",
                "desc": "Residual river basin moisture supports excellent winter pulse and mustard growth with minimal watering."
            }
    else: # West
        if season == "Kharif":
            return {
                "icon": "🌧️",
                "title": "Southwest Monsoon Active",
                "desc": "Crucial for cotton and soybean sowing. Highly variable rainfall requires efficient rainwater harvesting structures."
            }
        elif season == "Zaid":
            return {
                "icon": "🥭",
                "title": "Mango Showers & Coastal Humidity",
                "desc": "Pre-monsoon showers benefit mango orchards along the Konkan coast. High humidity requires close monitoring for crop pests."
            }
        else: # Rabi
            return {
                "icon": "☀️",
                "title": "Dry Winter Rabi Sowing",
                "desc": "Mild, dry winters. Crops rely heavily on drip/sprinkler irrigation. Great season for mustard and chickpea."
            }

# ─── Crop Suitability Engine ────────────────────────
def calculate_suitability(crop_name, soil_data, season, region, state=None):
    crop_profiles = {
        "Wheat": {
            "name_en": "Wheat", "name_hi": "Wheat / गेहूं",
            "season": "Rabi", "regions": ["North", "West"],
            "ph": (6.0, 7.5), "moisture": (30, 55), "ec": (0, 2.0),
            "n": (120, 250), "p": (15, 40), "k": (120, 250),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Black Soil (Regur)"]
        },
        "Paddy": {
            "name_en": "Paddy / Rice", "name_hi": "Paddy / धान",
            "season": "Kharif", "regions": ["East", "South", "North"],
            "ph": (5.5, 7.0), "moisture": (60, 90), "ec": (0, 3.0),
            "n": (100, 200), "p": (12, 35), "k": (100, 200),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Black Soil (Regur)", "Red & Yellow Soil", "Peaty/Marshy Soil"]
        },
        "Cotton": {
            "name_en": "Cotton", "name_hi": "Cotton / कपास",
            "season": "Kharif", "regions": ["West", "South"],
            "ph": (6.0, 8.0), "moisture": (35, 60), "ec": (0, 4.0),
            "n": (90, 160), "p": (10, 25), "k": (150, 300),
            "soils": ["Black Soil (Regur)", "Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)"]
        },
        "Mustard": {
            "name_en": "Mustard", "name_hi": "Mustard / सरसों",
            "season": "Rabi", "regions": ["North", "West"],
            "ph": (6.0, 7.5), "moisture": (25, 45), "ec": (0, 3.0),
            "n": (80, 150), "p": (12, 30), "k": (100, 180),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Red & Yellow Soil", "Saline/Alkaline Soil"]
        },
        "Maize": {
            "name_en": "Maize", "name_hi": "Maize / मक्का",
            "season": "Kharif", "regions": ["North", "South", "East", "West"],
            "ph": (5.8, 7.2), "moisture": (45, 65), "ec": (0, 2.0),
            "n": (120, 250), "p": (15, 30), "k": (120, 220),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Red & Yellow Soil", "Forest/Mountain Soil"]
        },
        "Potato": {
            "name_en": "Potato", "name_hi": "Potato / आलू",
            "season": "Rabi", "regions": ["North", "East"],
            "ph": (5.0, 6.5), "moisture": (50, 70), "ec": (0, 1.8),
            "n": (120, 250), "p": (20, 45), "k": (180, 300),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Red & Yellow Soil"]
        },
        "Tomato": {
            "name_en": "Tomato", "name_hi": "Tomato / टमाटर",
            "season": "Rabi", "regions": ["North", "South", "East", "West"],
            "ph": (6.0, 7.0), "moisture": (45, 65), "ec": (0, 2.5),
            "n": (100, 180), "p": (20, 40), "k": (150, 250),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Red & Yellow Soil", "Black Soil (Regur)"]
        },
        "Onion": {
            "name_en": "Onion", "name_hi": "Onion / प्याज",
            "season": "Rabi", "regions": ["West", "South", "North"],
            "ph": (6.0, 7.5), "moisture": (40, 60), "ec": (0, 2.0),
            "n": (100, 160), "p": (15, 25), "k": (150, 220),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Red & Yellow Soil", "Black Soil (Regur)"]
        },
        "Sugarcane": {
            "name_en": "Sugarcane", "name_hi": "Sugarcane / गन्ना",
            "season": "Kharif", "regions": ["North", "West", "South"],
            "ph": (6.0, 7.5), "moisture": (60, 80), "ec": (0, 3.0),
            "n": (150, 250), "p": (15, 30), "k": (150, 250),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Black Soil (Regur)", "Red & Yellow Soil"]
        },
        "Gram": {
            "name_en": "Gram / Chickpea", "name_hi": "Gram / चना",
            "season": "Rabi", "regions": ["North", "West", "South"],
            "ph": (6.0, 8.0), "moisture": (25, 45), "ec": (0, 1.5),
            "n": (40, 100), "p": (15, 25), "k": (100, 180),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Red & Yellow Soil", "Black Soil (Regur)"]
        },
        "Groundnut": {
            "name_en": "Groundnut", "name_hi": "Groundnut / मूंगफली",
            "season": "Kharif", "regions": ["West", "South"],
            "ph": (6.0, 7.0), "moisture": (30, 50), "ec": (0, 2.0),
            "n": (40, 100), "p": (12, 20), "k": (100, 150),
            "soils": ["Red & Yellow Soil", "Black Soil (Regur)", "Arid / Desert Soil", "Coastal Sandy Soil"]
        },
        "Bajra": {
            "name_en": "Bajra / Pearl Millet", "name_hi": "Bajra / बाजरा",
            "season": "Kharif", "regions": ["West", "North"],
            "ph": (6.5, 8.5), "moisture": (20, 40), "ec": (0, 4.0),
            "n": (60, 120), "p": (10, 20), "k": (100, 150),
            "soils": ["Arid / Desert Soil", "Red & Yellow Soil", "Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)"]
        },
        "Peas": {
            "name_en": "Peas", "name_hi": "Peas / मटर",
            "season": "Rabi", "regions": ["North", "East"],
            "ph": (6.0, 7.5), "moisture": (35, 55), "ec": (0, 1.8),
            "n": (40, 100), "p": (15, 25), "k": (100, 180),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Red & Yellow Soil", "Forest/Mountain Soil"]
        },
        "Garlic": {
            "name_en": "Garlic", "name_hi": "Garlic / लहसुन",
            "season": "Rabi", "regions": ["North", "West", "South"],
            "ph": (6.0, 7.0), "moisture": (40, 60), "ec": (0, 2.0),
            "n": (100, 180), "p": (15, 30), "k": (150, 250),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Red & Yellow Soil", "Black Soil (Regur)"]
        },
        "Ginger": {
            "name_en": "Ginger", "name_hi": "Ginger / अदरक",
            "season": "Kharif", "regions": ["South", "East", "North"],
            "ph": (5.5, 6.5), "moisture": (55, 75), "ec": (0, 1.5),
            "n": (120, 200), "p": (15, 25), "k": (180, 280),
            "soils": ["Red & Yellow Soil", "Forest/Mountain Soil", "Laterite Soil"]
        },
        "Turmeric": {
            "name_en": "Turmeric", "name_hi": "Turmeric / हल्दी",
            "season": "Kharif", "regions": ["South", "East", "West"],
            "ph": (5.5, 7.0), "moisture": (60, 80), "ec": (0, 2.0),
            "n": (120, 200), "p": (15, 25), "k": (180, 300),
            "soils": ["Red & Yellow Soil", "Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Forest/Mountain Soil"]
        },
        "Barley": {
            "name_en": "Barley", "name_hi": "Barley / जौ",
            "season": "Rabi", "regions": ["North", "West"],
            "ph": (6.0, 8.0), "moisture": (25, 45), "ec": (0, 3.0),
            "n": (80, 150), "p": (15, 25), "k": (100, 180),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Arid / Desert Soil", "Saline/Alkaline Soil"]
        },
        "Moong": {
            "name_en": "Moong Dal", "name_hi": "Moong / मूंग",
            "season": "Zaid", "regions": ["North", "West", "South", "East"],
            "ph": (6.0, 7.5), "moisture": (25, 45), "ec": (0, 1.8),
            "n": (45, 90), "p": (12, 22), "k": (100, 150),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Red & Yellow Soil", "Arid / Desert Soil"]
        },
        "Jowar": {
            "name_en": "Jowar / Sorghum", "name_hi": "Jowar / ज्वार",
            "season": "Kharif", "regions": ["West", "South", "North"],
            "ph": (6.0, 8.5), "moisture": (20, 45), "ec": (0, 3.0),
            "n": (80, 140), "p": (10, 20), "k": (100, 180),
            "soils": ["Black Soil (Regur)", "Red & Yellow Soil", "Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)"]
        },
        "Ragi": {
            "name_en": "Ragi / Finger Millet", "name_hi": "Ragi / रागी",
            "season": "Kharif", "regions": ["South", "East"],
            "ph": (5.0, 8.0), "moisture": (25, 50), "ec": (0, 2.5),
            "n": (60, 120), "p": (10, 20), "k": (100, 150),
            "soils": ["Red & Yellow Soil", "Laterite Soil", "Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)"]
        },
        "Coriander": {
            "name_en": "Coriander", "name_hi": "Coriander / धनिया",
            "season": "Rabi", "regions": ["West", "North", "South"],
            "ph": (6.0, 8.0), "moisture": (30, 50), "ec": (0, 1.5),
            "n": (80, 140), "p": (12, 22), "k": (100, 160),
            "soils": ["Black Soil (Regur)", "Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)"]
        },
        "Fenugreek": {
            "name_en": "Fenugreek", "name_hi": "Fenugreek / मेथी",
            "season": "Rabi", "regions": ["North", "West"],
            "ph": (6.0, 7.0), "moisture": (30, 50), "ec": (0, 1.5),
            "n": (40, 100), "p": (12, 20), "k": (100, 150),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Red & Yellow Soil"]
        },
        "Chili": {
            "name_en": "Chili", "name_hi": "Chili / मिर्च",
            "season": "Kharif", "regions": ["South", "West", "North", "East"],
            "ph": (6.0, 7.0), "moisture": (40, 60), "ec": (0, 2.0),
            "n": (120, 180), "p": (20, 35), "k": (150, 250),
            "soils": ["Black Soil (Regur)", "Red & Yellow Soil", "Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)"]
        },
        "Brinjal": {
            "name_en": "Brinjal / Eggplant", "name_hi": "Brinjal / बैंगन",
            "season": "Kharif", "regions": ["East", "South", "North", "West"],
            "ph": (5.5, 6.8), "moisture": (45, 65), "ec": (0, 2.5),
            "n": (120, 180), "p": (15, 25), "k": (150, 220),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Red & Yellow Soil", "Black Soil (Regur)"]
        },
        "Tea": {
            "name_en": "Tea", "name_hi": "Tea / चाय",
            "season": "Kharif", "regions": ["East", "South"],
            "ph": (4.5, 5.5), "moisture": (65, 85), "ec": (0, 1.2),
            "n": (120, 200), "p": (15, 30), "k": (120, 200),
            "soils": ["Laterite Soil", "Forest/Mountain Soil"]
        },
        "Coffee": {
            "name_en": "Coffee", "name_hi": "Coffee / कॉफी",
            "season": "Rabi", "regions": ["South"],
            "ph": (6.0, 6.5), "moisture": (50, 70), "ec": (0, 1.5),
            "n": (100, 180), "p": (15, 25), "k": (150, 250),
            "soils": ["Laterite Soil", "Forest/Mountain Soil"]
        },
        "Cardamom": {
            "name_en": "Cardamom", "name_hi": "Cardamom / इलायची",
            "season": "Kharif", "regions": ["South"],
            "ph": (5.0, 6.0), "moisture": (60, 80), "ec": (0, 1.2),
            "n": (80, 150), "p": (15, 25), "k": (120, 200),
            "soils": ["Forest/Mountain Soil", "Laterite Soil"]
        },
        "BlackPepper": {
            "name_en": "Black Pepper", "name_hi": "Black Pepper / काली मिर्च",
            "season": "Kharif", "regions": ["South"],
            "ph": (5.5, 6.5), "moisture": (60, 80), "ec": (0, 1.5),
            "n": (80, 160), "p": (10, 20), "k": (120, 220),
            "soils": ["Forest/Mountain Soil", "Laterite Soil"]
        },
        "Cumin": {
            "name_en": "Cumin / Jeera", "name_hi": "Cumin / जीरा",
            "season": "Rabi", "regions": ["West"],
            "ph": (6.5, 7.5), "moisture": (20, 35), "ec": (0, 1.5),
            "n": (40, 80), "p": (10, 20), "k": (60, 120),
            "soils": ["Arid / Desert Soil", "Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)"]
        },
        "Fennel": {
            "name_en": "Fennel / Saunf", "name_hi": "Fennel / सौंफ",
            "season": "Rabi", "regions": ["West", "North"],
            "ph": (6.5, 7.5), "moisture": (30, 50), "ec": (0, 1.8),
            "n": (60, 120), "p": (12, 22), "k": (80, 150),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Arid / Desert Soil"]
        },
        "Saffron": {
            "name_en": "Saffron / Kesar", "name_hi": "Saffron / केसर",
            "season": "Rabi", "regions": ["North"],
            "ph": (6.5, 8.0), "moisture": (35, 55), "ec": (0, 1.2),
            "n": (60, 100), "p": (15, 30), "k": (80, 160),
            "soils": ["Karewa Soil"]
        },
        "Jute": {
            "name_en": "Jute", "name_hi": "Jute / पटसन",
            "season": "Kharif", "regions": ["East"],
            "ph": (6.0, 7.5), "moisture": (65, 85), "ec": (0, 2.0),
            "n": (80, 150), "p": (15, 25), "k": (100, 180),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Peaty/Marshy Soil"]
        },
        "Coconut": {
            "name_en": "Coconut", "name_hi": "Coconut / नारियल",
            "season": "Kharif", "regions": ["South", "East"],
            "ph": (5.2, 8.0), "moisture": (60, 80), "ec": (0, 3.0),
            "n": (80, 160), "p": (12, 25), "k": (150, 250),
            "soils": ["Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)", "Laterite Soil", "Red & Yellow Soil", "Coastal Sandy Soil"]
        },
        "Soybean": {
            "name_en": "Soybean", "name_hi": "Soybean / सोयाबीन",
            "season": "Kharif", "regions": ["West", "North"],
            "ph": (6.0, 7.5), "moisture": (40, 60), "ec": (0, 2.0),
            "n": (60, 120), "p": (15, 30), "k": (100, 180),
            "soils": ["Black Soil (Regur)", "Alluvial Soil (Khadar - New)", "Alluvial Soil (Bhangar - Old)"]
        },
        "Cloves": {
            "name_en": "Cloves / Laung", "name_hi": "Cloves / लौंग",
            "season": "Kharif", "regions": ["South"],
            "ph": (5.0, 6.0), "moisture": (60, 80), "ec": (0, 1.5),
            "n": (80, 140), "p": (12, 22), "k": (100, 180),
            "soils": ["Laterite Soil", "Forest/Mountain Soil"]
        },
        "Cinnamon": {
            "name_en": "Cinnamon", "name_hi": "Cinnamon / दालचीनी",
            "season": "Kharif", "regions": ["South"],
            "ph": (5.5, 6.5), "moisture": (60, 80), "ec": (0, 1.5),
            "n": (80, 140), "p": (12, 22), "k": (100, 180),
            "soils": ["Laterite Soil", "Forest/Mountain Soil"]
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
        
    # 3. Soil Profile Check (uses state for tiebreaker if available)
    active_profile = detect_soil_profile(soil_data, state=state)
    soil_match = (active_profile in profile.get("soils", []))
    if not soil_match:
        penalties += 20
        
    # 4. pH Check
    ph = soil_data.get("ph", 7.0)
    ph_min, ph_max = profile["ph"]
    if ph < ph_min:
        penalties += min(20, (ph_min - ph) * 15)
    elif ph > ph_max:
        penalties += min(20, (ph - ph_max) * 15)
        
    # 5. Moisture Check
    moist = soil_data.get("moisture", 0)
    m_min, m_max = profile["moisture"]
    if moist < m_min:
        penalties += min(20, (m_min - moist) * 0.8)
    elif moist > m_max:
        penalties += min(20, (moist - m_max) * 0.8)
        
    # 6. EC Check
    ec = soil_data.get("ec", 0)
    ec_min, ec_max = profile["ec"]
    if ec > ec_max:
        penalties += min(15, (ec - ec_max) * 10)
        
    # 7. Nutrients (NPK) Check
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
    if not soil_match:
        preferred_soils_str = ", ".join(profile.get("soils", []))
        feedback.append(f"Soil profile ({active_profile}) is not optimal. Prefers: {preferred_soils_str}.")
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
        "regions_list": profile["regions"],
        "season_match": season_match,
        "region_match": region_match,
        "soil_match": soil_match,
        "feedback": " ".join(feedback),
        "ph_range": f"{ph_min} - {ph_max}",
        "moisture_range": f"{m_min}% - {m_max}%",
        "preferred_soils": ", ".join(profile.get("soils", []))
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
LAYOUT_HTML = """
\n<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Mitti | Farmer Dashboard</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=Geist:wght@400;500&amp;family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@100..900&amp;family=Inter:wght@100..900&amp;display=swap" rel="stylesheet"/>
<script id="tailwind-config">
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    "colors": {
                        "on-primary-fixed": "#002204",
                        "on-surface": "#e2e3df",
                        "on-error-container": "#ffdad6",
                        "primary-fixed": "#94f990",
                        "error-container": "#93000a",
                        "on-surface-variant": "#becab9",
                        "on-secondary-container": "#d5b1a4",
                        "surface-tint": "#78dc77",
                        "background": "#121412",
                        "on-secondary": "#422b22",
                        "inverse-on-surface": "#2f312e",
                        "on-tertiary-fixed-variant": "#005312",
                        "outline-variant": "#3f4a3c",
                        "on-background": "#e2e3df",
                        "on-primary-fixed-variant": "#005313",
                        "tertiary-fixed-dim": "#88d982",
                        "secondary-fixed-dim": "#e4beb2",
                        "on-tertiary": "#003909",
                        "surface-container-highest": "#333533",
                        "primary": "#78dc77",
                        "primary-container": "#4caf50",
                        "tertiary-fixed": "#a3f69c",
                        "inverse-surface": "#e2e3df",
                        "tertiary-container": "#5dac5b",
                        "on-tertiary-fixed": "#002204",
                        "secondary": "#e4beb2",
                        "primary-fixed-dim": "#78dc77",
                        "inverse-primary": "#006e1c",
                        "surface": "#121412",
                        "surface-bright": "#383a37",
                        "secondary-fixed": "#ffdbce",
                        "on-secondary-fixed-variant": "#5b4137",
                        "secondary-container": "#5d4339",
                        "surface-dim": "#121412",
                        "outline": "#899484",
                        "surface-container-lowest": "#0d0f0d",
                        "on-secondary-fixed": "#2b160f",
                        "surface-container-high": "#292a28",
                        "tertiary": "#88d982",
                        "on-tertiary-container": "#003c0a",
                        "error": "#ffb4ab",
                        "on-error": "#690005",
                        "surface-variant": "#333533",
                        "on-primary-container": "#003c0b",
                        "on-primary": "#00390a",
                        "surface-container": "#1e201e",
                        "surface-container-low": "#1a1c1a"
                    },
                    "borderRadius": {
                        "DEFAULT": "0.25rem",
                        "lg": "0.5rem",
                        "xl": "0.75rem",
                        "full": "9999px"
                    },
                    "spacing": {
                        "card-padding": "20px",
                        "stack-gap": "12px",
                        "gutter": "24px",
                        "margin-page": "32px",
                        "unit": "4px"
                    },
                    "fontFamily": {
                        "body-md": ["Inter"],
                        "mono-data": ["Geist"],
                        "title-md": ["Inter"],
                        "headline-lg-mobile": ["Inter"],
                        "display-lg": ["Inter"],
                        "label-sm": ["Geist"],
                        "headline-lg": ["Inter"]
                    },
                    "fontSize": {
                        "body-md": ["16px", {"lineHeight": "24px", "fontWeight": "400"}],
                        "mono-data": ["14px", {"lineHeight": "20px", "fontWeight": "400"}],
                        "title-md": ["18px", {"lineHeight": "24px", "fontWeight": "500"}],
                        "headline-lg-mobile": ["24px", {"lineHeight": "32px", "fontWeight": "600"}],
                        "display-lg": ["48px", {"lineHeight": "56px", "letterSpacing": "-0.02em", "fontWeight": "700"}],
                        "label-sm": ["12px", {"lineHeight": "16px", "letterSpacing": "0.05em", "fontWeight": "500"}],
                        "headline-lg": ["32px", {"lineHeight": "40px", "letterSpacing": "-0.01em", "fontWeight": "600"}]
                    }
                },
            },
        }
    </script>
<style>
        .glass-card {
            background: rgba(18, 20, 18, 0.4);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            transition: all 0.3s ease;
        }
        .glass-card:hover {
            backdrop-filter: blur(40px);
            border: 1px solid rgba(255, 255, 255, 0.30);
        }
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }
        .glow-line {
            box-shadow: 0 0 10px rgba(120, 220, 119, 0.4);
        }
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(120, 220, 119, 0.2);
            border-radius: 10px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
    </style>

    <script type="text/javascript">
      function googleTranslateElementInit() {
        new google.translate.TranslateElement({
            pageLanguage: 'en', 
            includedLanguages: 'en,hi,bn,te,mr,ta,gu,ur,kn,or,pa', 
            layout: google.translate.TranslateElement.InlineLayout.SIMPLE
        }, 'google_translate_element');
      }
    </script>
    <script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
</head>
<body class="bg-background text-on-surface font-body-md overflow-x-hidden">
<!-- Background Atmospheric Effect -->

<!-- SideNavBar (Shared Component) -->
<aside class="h-screen w-64 fixed left-0 top-0 bg-surface/40 dark:bg-surface/40 font-body-md text-body-md backdrop-blur-[20px] border-r border-white/15 shadow-none flex flex-col h-full py-8 px-4 z-50">
<div class="mb-12 px-2">
<h1 class="font-headline-lg text-headline-lg text-primary font-bold">Mitti</h1>
<p class="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-widest mt-1">Agronomy Insights</p>
</div>
<nav class="flex-1 space-y-2">
<!-- Active State: Dashboard -->
<a class="flex items-center gap-4 py-3 px-4 rounded-xl {{ 'text-primary font-bold border-r-2 border-primary bg-white/5' if active_page == 'dashboard' else 'text-on-surface-variant hover:bg-white/10 hover:backdrop-blur-md' }} transition-all" href="/">
<span class="material-symbols-outlined">dashboard</span>
                Dashboard
            </a>
<a class="flex items-center gap-4 py-3 px-4 rounded-xl {{ 'text-primary font-bold border-r-2 border-primary bg-white/5' if active_page == 'sensors' else 'text-on-surface-variant hover:bg-white/10 hover:backdrop-blur-md' }} transition-all active:scale-95 duration-200" href="/sensors">
<span class="material-symbols-outlined">sensors</span>
                Sensors
            </a>
<a class="flex items-center gap-4 py-3 px-4 rounded-xl {{ 'text-primary font-bold border-r-2 border-primary bg-white/5' if active_page == 'history' else 'text-on-surface-variant hover:bg-white/10 hover:backdrop-blur-md' }} transition-all active:scale-95 duration-200" href="/history">
<span class="material-symbols-outlined">history</span>
                Crop History
            </a>
<a class="flex items-center gap-4 py-3 px-4 rounded-xl {{ 'text-primary font-bold border-r-2 border-primary bg-white/5' if active_page == 'settings' else 'text-on-surface-variant hover:bg-white/10 hover:backdrop-blur-md' }} transition-all active:scale-95 duration-200" href="/settings">
<span class="material-symbols-outlined">settings</span>
                Settings
            </a>
</nav>
<div class="mt-auto pt-8 border-t border-white/10">
<a class="flex items-center gap-4 py-3 px-4 rounded-xl text-on-surface-variant hover:bg-error/10 hover:text-error transition-all active:scale-95 duration-200" href="/logout">
<span class="material-symbols-outlined">logout</span>
                Logout
            </a>
</div>
</aside>
<!-- TopAppBar (Shared Component) -->
<header class="fixed top-0 right-0 w-[calc(100%-16rem)] bg-surface/40 dark:bg-surface/40 font-title-md text-title-md backdrop-blur-[20px] border-b border-white/15 shadow-none flex justify-between items-center h-20 px-gutter z-40">
<div class="flex items-center gap-8">
<h2 class="font-headline-lg text-headline-lg text-primary font-bold">Mitti</h2>
<nav class="hidden md:flex items-center gap-6">
<a class="text-primary border-b-2 border-primary pb-1 font-medium" href="#">Dashboard</a>
<a class="text-on-surface-variant hover:text-primary transition-colors" href="#">Sensors</a>
</nav>
</div>
<div class="flex items-center gap-6">
<form action="/demo" method="GET" class="flex items-center gap-2 bg-white/5 py-1 px-3 rounded-xl border border-white/10">
   <select name="profile" onchange="this.form.submit()" class="bg-transparent text-sm text-primary outline-none cursor-pointer" style="appearance: none;">
     <option value="" disabled selected>Simulation Mode</option>
     <option value="alluvial">Khadar Soil (New Alluvial)</option>
     <option value="bhangar">Bhangar Soil (Old Alluvial)</option>
     <option value="black">Black Soil (Regur)</option>
     <option value="red">Red & Yellow Soil</option>
     <option value="laterite">Laterite Soil</option>
     <option value="arid">Arid / Desert Soil</option>
     <option value="forest">Forest / Mountain Soil</option>
     <option value="saline">Saline / Alkaline Soil</option>
     <option value="peaty">Peaty / Marshy Soil</option>
     <option value="coastal">Coastal Sandy Soil</option>
     <option value="terai">Terai Soil</option>
     <option value="karewa">Karewa Soil</option>
   </select>
</form>
<div class="hidden lg:flex items-center gap-2 bg-white/5 py-2 px-4 rounded-full border border-white/10">
<span class="material-symbols-outlined text-primary text-sm">cloudy_filled</span>
<span class="font-mono-data text-mono-data">Weather: {{ data.temp }}°C | {{ data.humidity }}% Humidity</span>
</div>
<div class="flex items-center gap-4">
<div id="google_translate_element" class="mr-4"></div>
<div class="text-on-surface-variant text-sm font-medium hidden md:block">
  <span class="material-symbols-outlined text-sm align-middle mr-1">location_on</span>{{ city }}, {{ state }}
</div>
<div class="h-10 w-10 rounded-full border border-primary/40 p-0.5 overflow-hidden">
<img class="w-full h-full object-cover rounded-full" data-alt="A professional close-up portrait of a South Asian agronomist wearing modern outdoor field gear, standing against a blurred background of a lush green field at golden hour. The lighting is soft and warm, highlighting intelligence and expertise, with a high-end cinematic photography style consistent with a premium agricultural technology platform." src="https://lh3.googleusercontent.com/aida-public/AB6AXuC8vNFjU3KTicd8ICulsPSijkBia-3iuvPjGMTq_2Lay_g38XroRyBK2M7b6zPOktoqrhpp9cJodEmmJXuA1mlkW8SP7GaqrCnNXfwc5u9srXlaaN4laNQCpP1iqVWrgBuUa_ggOuLtsVtkHS3oFKpP1bJMW43TbebIV1JQh--Z6RXgf0yBmr1YrPJw23NKxPbJXtjhTiFCq2xmAj4KzmHwf22zhxJDbF0GNEwwovyhbGKUSUmlXLd4AffdmxL78GPF2KxhtDEZgpx2"/>
</div>
</div>
</div>
</header>
<!-- Main Content -->
<main class="ml-64 mt-20 p-margin-page">
  {{ content | safe }}
</main>
<!-- Footer Meta -->
<footer class="ml-64 p-margin-page pt-0 pb-8 flex justify-between items-center border-t border-white/5 mt-gutter">
<p class="text-xs text-on-surface-variant">Mitti Agronomy System v2.4.0 • Secured by EarthSync Encryption</p>
<div class="flex gap-4">
<a class="text-xs text-on-surface-variant hover:text-primary" href="#">Documentation</a>
<a class="text-xs text-on-surface-variant hover:text-primary" href="#">Support</a>
</div>
</footer>
<script>
        // Simple micro-interactions for sensor cards
        document.querySelectorAll('.glass-card').forEach(card => {
            card.addEventListener('mousedown', () => {
                card.style.transform = 'scale(0.98)';
            });
            card.addEventListener('mouseup', () => {
                card.style.transform = 'scale(1)';
            });
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'scale(1)';
            });
        });

        // Simulating some live data fluctuations
        setInterval(() => {
            const dataPills = document.querySelectorAll('.font-display-lg');
            dataPills.forEach(pill => {
                if(Math.random() > 0.8) {
                    pill.classList.add('opacity-50');
                    setTimeout(() => pill.classList.remove('opacity-50'), 100);
                }
            });
        }, 3000);
    </script>

<script>
  let currentRecommendations = {};

  async function loadRecommendations() {
    const season = document.getElementById('seasonSelect') ? document.getElementById('seasonSelect').value : 'Kharif';
    try {
      const res = await fetch(`/recommend?season=${season}`);
      const data = await res.json();
      currentRecommendations = data.crops;
      
      const container = document.getElementById('cropCardsContainer');
      container.innerHTML = '';
      
      const sortedCrops = Object.entries(data.crops).sort((a,b) => b[1].score - a[1].score);
      
      sortedCrops.forEach(([cropId, details]) => {
        let matchClass = 'text-primary';
        if (details.score < 40) matchClass = 'text-error';
        else if (details.score < 75) matchClass = 'text-yellow-400';

        const card = `
        <div class="min-w-[280px] glass-card rounded-xl p-card-padding snap-start relative group cursor-pointer hover:-translate-y-1">
          <div class="flex justify-between items-start mb-6">
            <div class="bg-primary/10 p-3 rounded-2xl border border-primary/20 group-hover:scale-110 transition-transform">
              <span class="material-symbols-outlined text-primary text-3xl">psychology</span>
            </div>
            <div class="text-right">
              <span class="${matchClass} font-bold text-xl block">${details.score}%</span>
              <span class="text-xs text-on-surface-variant font-medium">Match</span>
            </div>
          </div>
          <h4 class="font-title-md text-title-md font-bold mb-2">${details.name_hi}</h4>
          <p class="text-sm text-on-surface-variant mb-4">${details.feedback}</p>
          <div class="flex gap-2 flex-wrap">
            <span class="px-2 py-1 bg-white/5 rounded-md text-[10px] border border-white/5">${details.season}</span>
            <span class="px-2 py-1 bg-white/5 rounded-md text-[10px] border border-white/5">pH ${details.ph_range}</span>
          </div>
        </div>
        `;
        container.innerHTML += card;
      });
      
      if (data.phenomenon) {
         document.getElementById('phenomenonTitle').innerText = data.phenomenon.icon + " " + data.phenomenon.title;
         document.getElementById('phenomenonDesc').innerText = data.phenomenon.desc;
      }

    } catch (e) {
      console.error(e);
    }
  }

  window.onload = loadRecommendations;
</script>
\n</body></html>\n
"""

DASHBOARD_CONTENT = """
<!-- Welcome Section -->
<div class="mb-gutter flex justify-between items-end">
<div>
<p class="font-label-sm text-label-sm text-primary mb-1 uppercase tracking-widest">System Operational</p>
<h1 class="font-headline-lg text-headline-lg text-on-surface">{{ greeting }}</h1>
</div>
<div class="flex gap-stack-gap">
<button onclick="alert('Detailed Report generation is currently being finalized. Please check back soon.')" class="bg-primary text-on-primary-fixed px-6 py-2 rounded-xl font-bold hover:scale-105 active:scale-95 transition-all shadow-lg shadow-primary/20">Generate Report</button>
</div>
</div>
<div class="grid grid-cols-12 gap-gutter">
<!-- {{ phenomenon.title if phenomenon else 'Local Climate Alert' }} (Banner) -->
<div class="col-span-12 glass-card rounded-xl p-card-padding relative overflow-hidden group">
<div class="absolute inset-0 bg-gradient-to-r from-error/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
<div class="flex items-center gap-6 relative z-10">
<div class="bg-error/20 p-4 rounded-full border border-error/30 text-error animate-pulse">
<span class="material-symbols-outlined text-3xl">warning</span>
</div>
<div>
<h3 id="phenomenonTitle" class="font-title-md text-title-md text-error font-bold mb-1">{{ phenomenon.title if phenomenon else 'Local Climate Alert' }}</h3>
<p id="phenomenonDesc" class="font-body-md text-body-md text-on-surface-variant">{{ phenomenon.desc if phenomenon else 'No specific alerts for your region at this time.' }}</p>
</div>
<button onclick="this.closest('.glass-card').style.display='none'" class="ml-auto bg-white/10 hover:bg-white/20 border border-white/20 px-6 py-2 rounded-lg font-medium transition-all">Dismiss</button>
</div>
</div>
<!-- Card 1: Soil Sensor Readings -->
<div class="col-span-12 lg:col-span-8 glass-card rounded-xl p-card-padding flex flex-col">
<div class="flex justify-between items-center mb-6">
<div class="flex items-center gap-3">
<span class="material-symbols-outlined text-primary">analytics</span>
<h3 class="font-title-md text-title-md font-bold">Soil Sensor Readings</h3>
</div>
<div class="flex gap-2">
<span class="bg-primary/10 text-primary px-3 py-1 rounded-full text-xs font-bold border border-primary/20">LIVE DATA</span>
</div>
</div>
<div class="grid grid-cols-2 md:grid-cols-3 gap-6 flex-1">
<!-- N -->
<div class="space-y-3">
<div class="flex justify-between font-label-sm text-label-sm text-on-surface-variant">
<span>Nitrogen (N)</span>
<span class="text-primary">{{ data.n }} mg/kg</span>
</div>
<div class="h-2 w-full bg-white/5 rounded-full overflow-hidden border border-white/5">
<div class="h-full bg-primary glow-line" style="width: {{ (data.n / 320 * 100)|round|int }}%"></div>
</div>
</div>
<!-- P -->
<div class="space-y-3">
<div class="flex justify-between font-label-sm text-label-sm text-on-surface-variant">
<span>Phosphorus (P)</span>
<span class="text-primary">{{ data.p }} mg/kg</span>
</div>
<div class="h-2 w-full bg-white/5 rounded-full overflow-hidden border border-white/5">
<div class="h-full bg-primary glow-line" style="width: {{ (data.p / 45 * 100)|round|int }}%"></div>
</div>
</div>
<!-- K -->
<div class="space-y-3">
<div class="flex justify-between font-label-sm text-label-sm text-on-surface-variant">
<span>Potassium (K)</span>
<span class="text-primary">{{ data.k }} mg/kg</span>
</div>
<div class="h-2 w-full bg-white/5 rounded-full overflow-hidden border border-white/5">
<div class="h-full bg-primary glow-line" style="width: {{ (data.k / 350 * 100)|round|int }}%"></div>
</div>
</div>
<!-- pH -->
<div class="bg-white/5 p-4 rounded-xl border border-white/10 flex flex-col justify-center items-center group hover:bg-white/10 transition-all">
<span class="font-label-sm text-label-sm text-on-surface-variant mb-1">Soil pH</span>
<span class="font-display-lg text-4xl text-primary font-bold">{{ data.ph }}</span>
<span class="text-xs text-primary/60 mt-1 uppercase tracking-tighter">Optimal</span>
</div>
<!-- Moisture -->
<div class="bg-white/5 p-4 rounded-xl border border-white/10 flex flex-col justify-center items-center group hover:bg-white/10 transition-all">
<span class="font-label-sm text-label-sm text-on-surface-variant mb-1">Moisture</span>
<span class="font-display-lg text-4xl text-primary font-bold">{{ data.moisture }}%</span>
<span class="text-xs text-primary/60 mt-1 uppercase tracking-tighter">Adequate</span>
</div>
<!-- EC -->
<div class="bg-white/5 p-4 rounded-xl border border-white/10 flex flex-col justify-center items-center group hover:bg-white/10 transition-all">
<span class="font-label-sm text-label-sm text-on-surface-variant mb-1">Conductivity</span>
<span class="font-display-lg text-4xl text-primary font-bold">{{ data.ec }}</span>
<span class="text-xs text-primary/60 mt-1 uppercase tracking-tighter">dS/m</span>
</div>
</div>
</div>
<!-- Card 2: Soil Type Profile -->
<div class="col-span-12 lg:col-span-4 glass-card rounded-xl overflow-hidden flex flex-col">
<div class="h-32 w-full relative">
<div class="absolute inset-0 bg-cover bg-center" data-alt="Macro photography of fertile alluvial soil with rich dark brown textures and small grains, interspersed with tiny organic roots. The lighting is earthy and natural, highlighting the moist, high-density structure of healthy farmland soil. Cinematic depth of field, 8k resolution, organic and scientific aesthetic." style="background-image: url('https://lh3.googleusercontent.com/aida-public/AB6AXuC9rF8ULLNDLpw37HSFh-ME8YJISmNu9vcPFcBVut5FGju7oy8T3aWHZ-u1Lqde7Xf1Tw1r_Ojt1AcrpxPbdA5G4cxtQ-R_7MBUadVBiGVlDVIUBsi5JDSW15Qt7B-Re14UBV9qXwUJleYZOZbcWa-9uGZrMQ1F6e-bzbAIlkrmD82uX2yo4-5AlZXdpMzC6J03C7xBVXnYDWhNKkCBqSsIySL_Cz9ttbjnP1Q5xjIj7ihrDCwjflE1kAr158F_-nVMU_wU9fP_nL1u')"></div>
<div class="absolute inset-0 bg-gradient-to-t from-[#121412] to-transparent"></div>
<div class="absolute bottom-4 left-6 flex items-center gap-3">
<div class="bg-primary/20 backdrop-blur-md p-2 rounded-lg border border-primary/30">
<span class="material-symbols-outlined text-primary">layers</span>
</div>
<h3 class="font-title-md text-title-md font-bold">{{ soil_profile }}</h3>
</div>
</div>
<div class="p-card-padding flex-1 space-y-4">
<p class="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                        {{ soil_desc }}
                    </p>

<div class="pt-4 mt-auto">
<button onclick="alert('This soil profile is automatically managed by Mitti. Detailed PDF profiles will be available in the next update.')" class="w-full py-2 border border-white/10 rounded-lg hover:bg-white/5 transition-all text-sm font-medium">View Detailed Profile</button>
</div>
</div>
</div>

<!-- Wisdom Fact Glass Card -->
<div class="col-span-12 glass-card rounded-xl p-card-padding flex items-center gap-4 relative overflow-hidden group">
  <div class="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
  <div class="bg-primary/20 p-3 rounded-full border border-primary/30 text-primary relative z-10">
    <span class="material-symbols-outlined text-3xl">lightbulb</span>
  </div>
  <div class="relative z-10">
    <h3 class="font-title-md text-title-md font-bold mb-1">Mitti Wisdom</h3>
    <p class="font-body-md text-body-md text-on-surface-variant italic">"{{ wisdom }}"</p>
  </div>
</div>

<!-- Section: Crop Recommendations -->
<div class="col-span-12 space-y-4">
<div class="flex justify-between items-center">
<h3 class="font-headline-lg text-2xl font-bold flex items-center gap-3">
<span class="material-symbols-outlined text-primary">eco</span>
                        Crop Recommendations
                    </h3>
<div class="flex gap-2">
<button onclick="document.getElementById('cropCardsContainer').scrollBy({left:-300, behavior:'smooth'})" class="p-2 glass-card rounded-full hover:text-primary transition-all active:scale-90"><span class="material-symbols-outlined">chevron_left</span></button>
<button onclick="document.getElementById('cropCardsContainer').scrollBy({left:300, behavior:'smooth'})" class="p-2 glass-card rounded-full hover:text-primary transition-all active:scale-90"><span class="material-symbols-outlined">chevron_right</span></button>
</div>
</div>
<div class="mb-4 flex justify-end">
  <select id="seasonSelect" onchange="loadRecommendations()" class="bg-surface/50 border border-white/20 text-on-surface rounded-lg px-4 py-2 outline-none">
    <option value="Kharif">Kharif Season</option>
    <option value="Rabi">Rabi Season</option>
    <option value="Zaid">Zaid Season</option>
  </select>
</div>

<div id="cropCardsContainer" class="flex overflow-x-auto pb-4 gap-gutter snap-x no-scrollbar">
    <div class="text-on-surface-variant italic">Loading crop recommendations...</div>
</div>
</div> <!-- Closing Crop Recommendations -->
<!-- Action Area / Map Integration -->
<div class="col-span-12 glass-card rounded-xl p-card-padding overflow-hidden h-[300px] relative">
<div class="absolute inset-0 z-0">
<img class="w-full h-full object-cover grayscale brightness-50 contrast-125" data-alt="A top-down satellite view of segmented lush green farmland in Karnataka, India, with detailed irrigation canals and vibrant foliage. The image uses a high-contrast cinematic style with deep blacks in the shadows and vibrant, life-filled greens in the crops. Professional, scientific, and atmospheric agricultural mapping aesthetic." data-location="Karnataka, India" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBz83OyweJNMkYuFq_aUiijJGRUPQQFnHSuZWKebxOOY3nIXxB-KeoS9KdY1lTn8Bj8qyvVeetPsWq8_UgnLY3t9_E0NM-91l7Ujsxg5uRINjWSfCIBkHDaOXPA-0LEjUWd2nesfGlaPjxA9QqexxSYzBr3InousFU-uMfFNQKzZua6v1SGchSA89fbUqiQUvKE1oeDd6O-gCJGSYPqOD1Gtv_C_a-5aAgZnWP6EK6EN16SQhjjT1S-cMtOnEYrIktbE6BPcygrFM-x"/>
<div class="absolute inset-0 bg-gradient-to-t from-background/80 via-background/20 to-transparent"></div>
</div>
<div class="relative z-10 flex flex-col h-full">
<div class="flex items-center gap-3">
<span class="material-symbols-outlined text-primary">map</span>
<h3 class="font-title-md text-title-md font-bold">Field View - South Block</h3>
</div>
<div class="mt-auto flex justify-between items-end">
<div class="space-y-1">
<p class="text-xs text-on-surface-variant">Last Survey: 2 hours ago</p>
<p class="text-primary font-bold">14 active sensors tracking</p>
</div>
<button onclick="alert('Full-screen GIS map viewer is currently down for maintenance.')" class="bg-primary text-on-primary-fixed px-6 py-2 rounded-xl font-bold flex items-center gap-2 hover:scale-105 active:scale-95 transition-all">
<span class="material-symbols-outlined">zoom_in</span>
                            Expand Map
                        </button>
</div>
</div>
</div>
</div>
"""

SENSORS_CONTENT = """

<div class="mb-gutter">
    <h1 class="font-headline-lg text-headline-lg text-on-surface">Sensor Diagnostics</h1>
    <p class="text-on-surface-variant">Real-time telemetry and historical tracking for your IoT hardware.</p>
</div>
<div class="glass-card rounded-xl p-card-padding flex flex-col items-center justify-center min-h-[400px]">
    <span class="material-symbols-outlined text-6xl text-primary/50 mb-4">query_stats</span>
    <h3 class="font-title-md text-title-md font-bold mb-2">Detailed Charts Coming Soon</h3>
    <p class="text-on-surface-variant text-center max-w-md">The historical sensor charting module is currently being calibrated. Please rely on the dashboard for real-time readings.</p>
</div>

"""

HISTORY_CONTENT = """

<div class="mb-gutter">
    <h1 class="font-headline-lg text-headline-lg text-on-surface">Crop History</h1>
    <p class="text-on-surface-variant">Past yield cycles and performance analysis.</p>
</div>
<div class="glass-card rounded-xl p-card-padding">
    <table class="w-full text-left">
        <thead>
            <tr class="border-b border-white/10 text-on-surface-variant text-sm">
                <th class="pb-3 font-medium">Season</th>
                <th class="pb-3 font-medium">Crop Planted</th>
                <th class="pb-3 font-medium">Yield</th>
                <th class="pb-3 font-medium">Soil Health Impact</th>
            </tr>
        </thead>
        <tbody class="text-sm">
            <tr class="border-b border-white/5">
                <td class="py-4">Kharif 2024</td>
                <td class="py-4 font-bold text-primary">Paddy</td>
                <td class="py-4">4.2 Tons/Acre</td>
                <td class="py-4 text-warning">Depleted Nitrogen</td>
            </tr>
            <tr class="border-b border-white/5">
                <td class="py-4">Rabi 2024</td>
                <td class="py-4 font-bold text-primary">Wheat</td>
                <td class="py-4">3.8 Tons/Acre</td>
                <td class="py-4 text-primary">Stable</td>
            </tr>
            <tr>
                <td class="py-4">Zaid 2024</td>
                <td class="py-4 font-bold text-primary">Moong Dal</td>
                <td class="py-4">1.1 Tons/Acre</td>
                <td class="py-4 text-primary">+ Nitrogen Fixed</td>
            </tr>
        </tbody>
    </table>
</div>

"""

SETTINGS_CONTENT = """

<div class="mb-gutter">
    <h1 class="font-headline-lg text-headline-lg text-on-surface">Settings</h1>
    <p class="text-on-surface-variant">Update your farm profile and notification preferences.</p>
</div>
<div class="glass-card rounded-xl p-card-padding max-w-2xl">
    <div class="space-y-6">
        <div>
            <label class="block text-sm font-medium text-on-surface-variant mb-2">Full Name</label>
            <input type="text" value="{{ session.get('name', '') }}" disabled class="w-full bg-surface/50 border border-white/10 rounded-lg px-4 py-2 text-on-surface opacity-50 cursor-not-allowed">
        </div>
        <div>
            <label class="block text-sm font-medium text-on-surface-variant mb-2">State</label>
            <input type="text" value="{{ session.get('state', '') }}" disabled class="w-full bg-surface/50 border border-white/10 rounded-lg px-4 py-2 text-on-surface opacity-50 cursor-not-allowed">
        </div>
        <div>
            <label class="block text-sm font-medium text-on-surface-variant mb-2">City/District</label>
            <input type="text" value="{{ session.get('city', '') }}" disabled class="w-full bg-surface/50 border border-white/10 rounded-lg px-4 py-2 text-on-surface opacity-50 cursor-not-allowed">
        </div>
        <button class="bg-primary/20 text-primary px-6 py-2 rounded-xl font-bold border border-primary/30 mt-4">Save Changes</button>
    </div>
</div>

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


def detect_soil_profile(soil_data, state=None):
    """
    Scientific Soil Classification Engine.
    Scores sensor readings against ICAR/NBSS&LUP fingerprint profiles for all 9 Indian
    soil types. Uses a weighted distance-from-center approach. The farmer's state acts
    as a 15% tiebreaker when sensor readings are ambiguous between 2+ types.
    """
    reading = {
        "ph": soil_data.get("ph", 7.0),
        "ec": soil_data.get("ec", 0.0),
        "moisture": soil_data.get("moisture", 0),
        "n": soil_data.get("n", 0),
        "k": soil_data.get("k", 0)
    }

    scores = {}
    for soil_type, profile in SOIL_TYPE_PROFILES.items():
        score = 0.0
        params_checked = 0
        for param in ["ph", "ec", "moisture", "n", "k"]:
            if param not in profile:
                continue
            low, high = profile[param]
            val = reading[param]
            params_checked += 1
            rng = high - low if high > low else 1
            mid = (low + high) / 2.0

            if low <= val <= high:
                # Inside range — score 0.5 to 1.0, best at center
                dist = abs(val - mid) / (rng / 2.0)
                score += 1.0 - dist * 0.5
            else:
                # Outside range — negative score scaled by overshoot
                if val < low:
                    overshoot = (low - val) / max(rng, 1)
                else:
                    overshoot = (val - high) / max(rng, 1)
                score -= min(1.0, overshoot)

        if params_checked > 0:
            scores[soil_type] = score / params_checked
        else:
            scores[soil_type] = 0.0

        # State-geography tiebreaker: 15% bonus if this soil is known in the state
        if state and state in STATE_SOIL_TYPES:
            if soil_type in STATE_SOIL_TYPES[state]:
                scores[soil_type] += 0.15

    # Return the soil type with the highest match score
    return max(scores, key=scores.get)


@app.route("/")
def dashboard():
    """Serve the live dashboard."""
    if "phone" not in session:
        return redirect(url_for("login_page"))
        
    english_list, hindi_list, english_issues = get_advisory(latest)
    english_text = ", ".join(english_issues) if english_issues else "Soil health good"
    
    # Dynamic random wisdom fact selection
    wisdom = generate_wisdom()
    
    # Dynamic greeting with name
    greeting = f"Namaste, {session.get('name', 'Farmer')}! {get_greeting()}"
    
    # Detect soil profile category (use farmer's state for tiebreaker)
    user_state = session.get("state", "Rajasthan")
    soil_profile = detect_soil_profile(latest, state=user_state)
    
    from flask import render_template_string
    # Render the dashboard content first
    content_html = render_template_string(
        DASHBOARD_CONTENT,
        data=latest,
        advisories=english_list,
        english=english_text,
        wisdom=wisdom,
        greeting=greeting,
        timestamp=latest.get("timestamp", "Not yet received"),
        state=session.get("state", "Rajasthan"),
        city=session.get("city", "Jaipur"),
        soil_profile=soil_profile
    )
    # Wrap it in layout
    return render_template_string(LAYOUT_HTML, content=content_html, active_page='dashboard', data=latest)




@app.route("/sensors")
def sensors():
    if "phone" not in session: return redirect(url_for("login_page"))
    content_html = render_template_string(SENSORS_CONTENT)
    return render_template_string(LAYOUT_HTML, content=content_html, active_page='sensors', data=latest)

@app.route("/history")
def history():
    if "phone" not in session: return redirect(url_for("login_page"))
    content_html = render_template_string(HISTORY_CONTENT)
    return render_template_string(LAYOUT_HTML, content=content_html, active_page='history', data=latest)

@app.route("/settings")
def settings():
    if "phone" not in session: return redirect(url_for("login_page"))
    content_html = render_template_string(SETTINGS_CONTENT, session=session)
    return render_template_string(LAYOUT_HTML, content=content_html, active_page='settings', data=latest)

@app.route("/recommend")
def recommend_crops():
    """Return crop suitability calculations based on season & state."""
    season = request.args.get("season", "Rabi")
    state = request.args.get("state", session.get("state", "Rajasthan"))
    
    # Map state to region
    region = STATE_TO_REGION.get(state, "West")
    
    crops = ["Wheat", "Paddy", "Cotton", "Mustard", "Maize", "Potato", "Tomato", "Onion", "Sugarcane", "Gram", "Groundnut", "Bajra", "Peas", "Garlic", "Ginger", "Turmeric", "Barley", "Moong", "Jowar", "Ragi", "Coriander", "Fenugreek", "Chili", "Brinjal", "Tea", "Coffee", "Cardamom", "BlackPepper", "Cumin", "Fennel", "Saffron", "Jute", "Coconut", "Soybean", "Cloves", "Cinnamon"]
    results = {}
    for crop in crops:
        score, details = calculate_suitability(crop, latest, season, region, state=state)
        results[crop] = details
        
    # Get state-specific phenomenon
    phenomenon = STATE_PHENOMENA.get(state, {}).get(season)
    if not phenomenon:
        # Fallback to region-based
        phenomenon = get_local_phenomenon(region, season)
        
    return jsonify({
        "crops": results,
        "phenomenon": phenomenon
    })
# ─── Login HTML ───────────────────────────────────────
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mitti — Portal Login</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
  *{margin:0;padding:0;box-sizing:border-box;}
  body{font-family:'Inter',sans-serif;background:#0a0f0a;color:#e8f5e9;min-height:100vh;display:flex;justify-content:center;align-items:center;padding:1rem;}
  
  .login-card {
    background: rgba(17, 31, 17, 0.8);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(76, 175, 80, 0.3);
    border-radius: 16px;
    padding: 2.2rem;
    width: 100%;
    max-width: 420px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
  }
  
  .logo {
    text-align: center;
    font-size: 2.2rem;
    font-weight: 900;
    color: #4caf50;
    margin-bottom: 0.25rem;
    letter-spacing: -1px;
  }
  
  .tagline {
    text-align: center;
    font-size: 0.8rem;
    color: #81c784;
    margin-bottom: 2rem;
    font-style: italic;
  }
  
  .tabs {
    display: flex;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid rgba(76, 175, 80, 0.15);
  }
  
  .tab {
    flex: 1;
    text-align: center;
    padding: 0.75rem;
    cursor: pointer;
    font-weight: 600;
    color: #81c784;
    transition: all 0.2s;
  }
  
  .tab.active {
    color: #4caf50;
    border-bottom: 2px solid #4caf50;
  }
  
  .form-group {
    margin-bottom: 1.25rem;
  }
  
  .form-group label {
    display: block;
    font-size: 0.75rem;
    color: #558b2f;
    font-weight: bold;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
    letter-spacing: 0.5px;
  }
  
  .form-group input, .form-group select {
    width: 100%;
    background: #111f11;
    border: 1px solid #2d5a2d;
    color: #e8f5e9;
    padding: 0.75rem;
    border-radius: 8px;
    font-size: 0.9rem;
    outline: none;
    font-family: 'Inter', sans-serif;
    transition: border-color 0.2s;
  }
  
  .form-group input:focus, .form-group select:focus {
    border-color: #4caf50;
  }
  
  .btn {
    width: 100%;
    background: #4caf50;
    color: #000;
    font-weight: 700;
    border: none;
    padding: 0.75rem;
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    transition: background 0.2s, transform 0.1s;
    margin-top: 0.5rem;
  }
  
  .btn:hover {
    background: #66bb6a;
  }
  
  .btn:active {
    transform: scale(0.98);
  }
  
  .error-msg {
    background: rgba(244, 67, 54, 0.1);
    border: 1px solid #f44336;
    color: #f44336;
    padding: 0.75rem;
    border-radius: 8px;
    font-size: 0.85rem;
    margin-bottom: 1.25rem;
    text-align: center;
  }
</style>

    <script type="text/javascript">
      function googleTranslateElementInit() {
        new google.translate.TranslateElement({
            pageLanguage: 'en', 
            includedLanguages: 'en,hi,bn,te,mr,ta,gu,ur,kn,or,pa', 
            layout: google.translate.TranslateElement.InlineLayout.SIMPLE
        }, 'google_translate_element');
      }
    </script>
    <script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
</head>
<body>

<div class="login-card">
  <div class="logo">🌱 Mitti</div>
  <div class="tagline">"The farmer who stayed."</div>
  
  {% if error %}
    <div class="error-msg">{{error}}</div>
  {% endif %}
  
  <div class="tabs">
    <div class="tab active" id="tab-login" onclick="switchTab('login')">Sign In</div>
    <div class="tab" id="tab-signup" onclick="switchTab('signup')">Sign Up</div>
  </div>
  
  <form method="POST" action="/login" id="authForm">
    <input type="hidden" name="action" id="actionField" value="login">
    
    <div class="form-group" id="group-name" style="display: none;">
      <label>Full Name</label>
      <input type="text" name="name" placeholder="Enter your name">
    </div>
    
    <div class="form-group">
      <label>Phone Number</label>
      <input type="text" name="phone" placeholder="e.g. 9876543210" required>
    </div>
    
    <div class="form-group" id="group-state" style="display: none;">
      <label>State</label>
      <select name="state">
        <option value="" disabled selected>Select your state</option>
        <option value="Andhra Pradesh">Andhra Pradesh</option>
        <option value="Arunachal Pradesh">Arunachal Pradesh</option>
        <option value="Assam">Assam</option>
        <option value="Bihar">Bihar</option>
        <option value="Chhattisgarh">Chhattisgarh</option>
        <option value="Delhi">Delhi</option>
        <option value="Goa">Goa</option>
        <option value="Gujarat">Gujarat</option>
        <option value="Haryana">Haryana</option>
        <option value="Himachal Pradesh">Himachal Pradesh</option>
        <option value="Jammu & Kashmir">Jammu & Kashmir</option>
        <option value="Jharkhand">Jharkhand</option>
        <option value="Karnataka">Karnataka</option>
        <option value="Kerala">Kerala</option>
        <option value="Madhya Pradesh">Madhya Pradesh</option>
        <option value="Maharashtra">Maharashtra</option>
        <option value="Manipur">Manipur</option>
        <option value="Meghalaya">Meghalaya</option>
        <option value="Mizoram">Mizoram</option>
        <option value="Nagaland">Nagaland</option>
        <option value="Odisha">Odisha</option>
        <option value="Punjab">Punjab</option>
        <option value="Rajasthan">Rajasthan</option>
        <option value="Sikkim">Sikkim</option>
        <option value="Tamil Nadu">Tamil Nadu</option>
        <option value="Telangana">Telangana</option>
        <option value="Tripura">Tripura</option>
        <option value="Uttar Pradesh">Uttar Pradesh</option>
        <option value="Uttarakhand">Uttarakhand</option>
        <option value="West Bengal">West Bengal</option>
        <optgroup label="─── Union Territories ───">
        <option value="Andaman & Nicobar Islands">Andaman & Nicobar Islands</option>
        <option value="Chandigarh">Chandigarh</option>
        <option value="Dadra & Nagar Haveli and Daman & Diu">Dadra & Nagar Haveli and Daman & Diu</option>
        <option value="Ladakh">Ladakh</option>
        <option value="Lakshadweep">Lakshadweep</option>
        <option value="Puducherry">Puducherry</option>
        </optgroup>
      </select>
    </div>
    
    <div class="form-group" id="group-city" style="display: none;">
      <label>City / District</label>
      <input type="text" name="city" placeholder="Enter your city/district">
    </div>
    
    <button type="submit" class="btn" id="submitBtn">Sign In</button>
  </form>
</div>

<script>
  function switchTab(mode) {
    document.getElementById('tab-login').classList.remove('active');
    document.getElementById('tab-signup').classList.remove('active');
    document.getElementById('tab-' + mode).classList.add('active');
    
    document.getElementById('actionField').value = mode;
    
    const nameGroup = document.getElementById('group-name');
    const stateGroup = document.getElementById('group-state');
    const cityGroup = document.getElementById('group-city');
    const nameInput = nameGroup.querySelector('input');
    const stateSelect = stateGroup.querySelector('select');
    const cityInput = cityGroup.querySelector('input');
    
    if (mode === 'signup') {
      nameGroup.style.display = 'block';
      stateGroup.style.display = 'block';
      cityGroup.style.display = 'block';
      nameInput.required = true;
      stateSelect.required = true;
      cityInput.required = true;
      document.getElementById('submitBtn').innerText = 'Register & Enter';
    } else {
      nameGroup.style.display = 'none';
      stateGroup.style.display = 'none';
      cityGroup.style.display = 'none';
      nameInput.required = false;
      stateSelect.required = false;
      cityInput.required = false;
      document.getElementById('submitBtn').innerText = 'Sign In';
    }
  }
</script>
</body>
</html>
"""

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if "phone" in session:
        return redirect(url_for("dashboard"))
        
    error = None
    if request.method == "POST":
        action = request.form.get("action")
        phone = request.form.get("phone", "").strip()
        
        if not phone:
            error = "Phone number is required."
        else:
            users_file = "users.json"
            users = {}
            if os.path.exists(users_file):
                try:
                    with open(users_file, "r", encoding="utf-8") as f:
                        users = json.load(f)
                except Exception:
                    users = {}
            
            if action == "login":
                if phone in users:
                    session["phone"] = phone
                    session["name"] = users[phone]["name"]
                    session["state"] = users[phone]["state"]
                    session["city"] = users[phone].get("city", "Unknown")
                    return redirect(url_for("dashboard"))
                else:
                    error = "Phone number not registered. Please sign up!"
            elif action == "signup":
                name = request.form.get("name", "").strip()
                state = request.form.get("state", "").strip()
                city = request.form.get("city", "").strip()
                
                if not name or not state or not city:
                    error = "All fields (Name, Phone, State, City) are required for sign up."
                elif phone in users:
                    error = "Phone number already registered. Please login!"
                else:
                    users[phone] = {
                        "name": name,
                        "phone": phone,
                        "state": state,
                        "city": city
                    }
                    with open(users_file, "w", encoding="utf-8") as f:
                        json.dump(users, f, indent=4, ensure_ascii=False)
                        
                    session["phone"] = phone
                    session["name"] = name
                    session["state"] = state
                    session["city"] = city
                    return redirect(url_for("dashboard"))
                    
    return render_template_string(LOGIN_HTML, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


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
    profile = request.args.get("profile", "alluvial")
    
    if profile == "black":
        latest = {
            "n": 140, "p": 18, "k": 220,
            "moisture": 55, "ec": 0.5, "ph": 7.4,
            "temp": 28, "humidity": 70,
            "mq135": 280, "raining": False,
            "pump": False,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
    elif profile == "red":
        latest = {
            "n": 80, "p": 12, "k": 110,
            "moisture": 30, "ec": 0.3, "ph": 6.2,
            "temp": 30, "humidity": 50,
            "mq135": 310, "raining": False,
            "pump": False,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
    elif profile == "laterite":
        latest = {
            "n": 90, "p": 10, "k": 90,
            "moisture": 65, "ec": 0.4, "ph": 4.8,
            "temp": 24, "humidity": 85,
            "mq135": 180, "raining": True,
            "pump": False,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
    elif profile == "arid":
        latest = {
            "n": 50, "p": 8, "k": 130,
            "moisture": 15, "ec": 2.1, "ph": 7.8,
            "temp": 42, "humidity": 30,
            "mq135": 150, "raining": False,
            "pump": True,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
    elif profile == "forest":
        latest = {
            "n": 160, "p": 15, "k": 140,
            "moisture": 55, "ec": 0.3, "ph": 5.6,
            "temp": 20, "humidity": 80,
            "mq135": 120, "raining": False,
            "pump": False,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
    elif profile == "saline":
        latest = {
            "n": 100, "p": 14, "k": 120,
            "moisture": 35, "ec": 4.5, "ph": 8.2,
            "temp": 33, "humidity": 45,
            "mq135": 420, "raining": False,
            "pump": False,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
    elif profile == "peaty":
        latest = {
            "n": 250, "p": 18, "k": 60,
            "moisture": 85, "ec": 0.5, "ph": 4.2,
            "temp": 27, "humidity": 90,
            "mq135": 100, "raining": True,
            "pump": False,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
    elif profile == "coastal":
        latest = {
            "n": 55, "p": 7, "k": 80,
            "moisture": 25, "ec": 2.8, "ph": 7.2,
            "temp": 32, "humidity": 75,
            "mq135": 250, "raining": False,
            "pump": True,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
    elif profile == "terai":
        latest = {
            "n": 300, "p": 12, "k": 100,
            "moisture": 60, "ec": 0.5, "ph": 6.2,
            "temp": 22, "humidity": 80,
            "mq135": 110, "raining": False,
            "pump": False,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
    elif profile == "karewa":
        latest = {
            "n": 150, "p": 25, "k": 180,
            "moisture": 40, "ec": 0.8, "ph": 7.0,
            "temp": 15, "humidity": 65,
            "mq135": 90, "raining": False,
            "pump": False,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
    elif profile == "bhangar":
        latest = {
            "n": 150, "p": 18, "k": 130,
            "moisture": 35, "ec": 1.2, "ph": 7.8,
            "temp": 30, "humidity": 50,
            "mq135": 200, "raining": False,
            "pump": True,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
    else: # alluvial / default
        latest = {
            "n": 180, "p": 25, "k": 150,
            "moisture": 45, "ec": 0.8, "ph": 6.8,
            "temp": 31, "humidity": 60,
            "mq135": 210, "raining": False,
            "pump": False,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    print("=" * 50)
    print("  MITTI Backend Server")
    print("  Dashboard -> http://localhost:5000")
    print("  Demo data -> http://localhost:5000/demo")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)

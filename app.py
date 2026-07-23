"""
MITTI — Backend Server
Flask + Crop Suitability Engine + Twilio Voice Call + Dynamic Wisdom
Samsung Solve for Tomorrow 2025
"""
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from flask_cors import CORS
from twilio.rest import Client
import json, os, time, random, threading
from datetime import datetime
from ml_service import CropDiseaseClassifier
from crop_journey import crop_journeys, get_generic_journey

app = Flask(__name__)
CORS(app)
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

def generate_wisdom(lang="en"):
    """Generates a unique farming fact or ancient wisdom."""
    if lang == "hi":
        wisdoms = [
            "कृषि पाराशर: 'श्रावण मास में वर्षा भरपूर फसल लाती है।'",
            "वृक्षायुर्वेद: 'नीम की खली मिट्टी को समृद्ध करती है और प्राकृतिक कीट निवारक का काम करती है।'",
            "पारंपरिक ज्ञान: 'गर्मियों में गहरी जोती गई खेत मानसून की बारिश को पूरी तरह से पी लेती है।'",
            "प्राचीन ज्ञान: 'अनाज के साथ फलीदार फसलों को उगाने से पृथ्वी की जीवन शक्ति बहाल होती है।'",
            "चाणक्य नीति: 'कृषि सभी धन का मूल है।' अपनी ऊपरी मिट्टी की सोने की तरह रक्षा करें।"
        ]
        return random.choice(wisdoms)
        
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
    # NORTH
    "Jammu and Kashmir": "North", "Ladakh": "North", "Himachal Pradesh": "North", 
    "Punjab": "North", "Chandigarh": "North", "Uttarakhand": "North", 
    "Haryana": "North", "Delhi": "North", "Uttar Pradesh": "North", 
    "Madhya Pradesh": "North", "Chhattisgarh": "North",
    # WEST
    "Rajasthan": "West", "Gujarat": "West", "Maharashtra": "West", 
    "Goa": "West", "Dadra and Nagar Haveli and Daman and Diu": "West",
    # SOUTH
    "Karnataka": "South", "Kerala": "South", "Lakshadweep": "South", 
    "Tamil Nadu": "South", "Puducherry": "South", "Andhra Pradesh": "South", 
    "Telangana": "South", "Andaman and Nicobar Islands": "South",
    # EAST
    "Bihar": "East", "Jharkhand": "East", "Odisha": "East", "West Bengal": "East", 
    "Sikkim": "East", "Assam": "East", "Arunachal Pradesh": "East", 
    "Nagaland": "East", "Manipur": "East", "Mizoram": "East", 
    "Tripura": "East", "Meghalaya": "East"
}

STATE_SOIL_TYPES = {
    # ── 28 States ──
    "Andhra Pradesh": ["Black Soil (Regur)", "Red & Yellow Soil", "Alluvial Soil (Fertile)", "Coastal Sandy Soil", "Laterite Soil"],
    "Arunachal Pradesh": ["Forest/Mountain Soil", "Laterite Soil", "Alluvial Soil (Fertile)"],
    "Assam": ["Alluvial Soil (Fertile)", "Laterite Soil", "Forest/Mountain Soil", "Peaty/Marshy Soil"],
    "Bihar": ["Alluvial Soil (Fertile)", "Red & Yellow Soil", "Forest/Mountain Soil"],
    "Chhattisgarh": ["Red & Yellow Soil", "Laterite Soil", "Black Soil (Regur)", "Alluvial Soil (Fertile)"],
    "Goa": ["Laterite Soil", "Coastal Sandy Soil", "Alluvial Soil (Fertile)"],
    "Gujarat": ["Black Soil (Regur)", "Alluvial Soil (Fertile)", "Arid / Desert Soil", "Saline/Alkaline Soil", "Coastal Sandy Soil"],
    "Haryana": ["Alluvial Soil (Fertile)", "Arid / Desert Soil", "Saline/Alkaline Soil"],
    "Himachal Pradesh": ["Forest/Mountain Soil", "Alluvial Soil (Fertile)", "Red & Yellow Soil"],
    "Jharkhand": ["Red & Yellow Soil", "Laterite Soil", "Alluvial Soil (Fertile)", "Forest/Mountain Soil"],
    "Karnataka": ["Red & Yellow Soil", "Black Soil (Regur)", "Laterite Soil", "Coastal Sandy Soil", "Forest/Mountain Soil", "Alluvial Soil (Fertile)"],
    "Kerala": ["Laterite Soil", "Coastal Sandy Soil", "Alluvial Soil (Fertile)", "Forest/Mountain Soil", "Peaty/Marshy Soil"],
    "Madhya Pradesh": ["Black Soil (Regur)", "Red & Yellow Soil", "Alluvial Soil (Fertile)", "Laterite Soil"],
    "Maharashtra": ["Black Soil (Regur)", "Laterite Soil", "Red & Yellow Soil", "Alluvial Soil (Fertile)", "Coastal Sandy Soil"],
    "Manipur": ["Forest/Mountain Soil", "Laterite Soil", "Alluvial Soil (Fertile)"],
    "Meghalaya": ["Forest/Mountain Soil", "Laterite Soil", "Red & Yellow Soil"],
    "Mizoram": ["Forest/Mountain Soil", "Laterite Soil"],
    "Nagaland": ["Forest/Mountain Soil", "Laterite Soil", "Red & Yellow Soil"],
    "Odisha": ["Red & Yellow Soil", "Laterite Soil", "Alluvial Soil (Fertile)", "Coastal Sandy Soil", "Black Soil (Regur)"],
    "Punjab": ["Alluvial Soil (Fertile)", "Arid / Desert Soil", "Saline/Alkaline Soil"],
    "Rajasthan": ["Arid / Desert Soil", "Alluvial Soil (Fertile)", "Red & Yellow Soil", "Saline/Alkaline Soil", "Black Soil (Regur)", "Forest/Mountain Soil"],
    "Sikkim": ["Forest/Mountain Soil", "Laterite Soil", "Alluvial Soil (Fertile)"],
    "Tamil Nadu": ["Red & Yellow Soil", "Black Soil (Regur)", "Alluvial Soil (Fertile)", "Laterite Soil", "Coastal Sandy Soil"],
    "Telangana": ["Black Soil (Regur)", "Red & Yellow Soil", "Alluvial Soil (Fertile)", "Laterite Soil"],
    "Tripura": ["Laterite Soil", "Alluvial Soil (Fertile)", "Red & Yellow Soil"],
    "Uttar Pradesh": ["Alluvial Soil (Fertile)", "Red & Yellow Soil", "Saline/Alkaline Soil", "Forest/Mountain Soil"],
    "Uttarakhand": ["Forest/Mountain Soil", "Alluvial Soil (Fertile)", "Red & Yellow Soil"],
    "West Bengal": ["Alluvial Soil (Fertile)", "Red & Yellow Soil", "Laterite Soil", "Peaty/Marshy Soil", "Coastal Sandy Soil", "Forest/Mountain Soil"],
    # ── 8 Union Territories ──
    "Delhi": ["Alluvial Soil (Fertile)", "Arid / Desert Soil"],
    "Chandigarh": ["Alluvial Soil (Fertile)"],
    "Jammu and Kashmir": ["Forest/Mountain Soil", "Alluvial Soil (Fertile)", "Peaty/Marshy Soil"],
    "Ladakh": ["Arid / Desert Soil", "Forest/Mountain Soil", "Saline/Alkaline Soil"],
    "Puducherry": ["Alluvial Soil (Fertile)", "Coastal Sandy Soil", "Red & Yellow Soil"],
    "Andaman and Nicobar Islands": ["Laterite Soil", "Coastal Sandy Soil", "Alluvial Soil (Fertile)", "Forest/Mountain Soil"],
    "Lakshadweep": ["Coastal Sandy Soil", "Saline/Alkaline Soil"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Red & Yellow Soil", "Laterite Soil", "Coastal Sandy Soil", "Alluvial Soil (Fertile)"]
}

# ─── Crop Suitability Engine ────────────────────────
crop_profiles = {   'Mango': {   'name_en': 'Mango',
                 'name_hi': 'Mango / आम',
                 'season': 'Zaid',
                 'regions': ['North', 'South', 'East', 'West'],
                 'ph': (5.5, 7.5),
                 'moisture': (40, 70),
                 'ec': (0, 1.5),
                 'n': (80, 150),
                 'p': (20, 40),
                 'k': (100, 200),
                 'soils': [   'Alluvial Soil (Fertile)',
                              'Red & Yellow Soil',
                              'Laterite Soil'],
                 'water_needs': 'Medium',
                 'crop_type': 'Plantation',
                 'sowing_months': ['Jul', 'Aug'],
                 'harvest_months': ['Apr', 'May', 'Jun'],
                 'farm_school': {   'steps': [   {   'title': 'Pit Preparation',
                                                     'desc': 'Dig 1x1x1m pits '
                                                             'and expose to '
                                                             'sun.',
                                                     'why': 'Sun exposure '
                                                            'kills harmful '
                                                            'soil-borne '
                                                            'pathogens and '
                                                            'pests before '
                                                            'planting.'},
                                                 {   'title': 'Planting',
                                                     'desc': 'Plant grafts in '
                                                             'the center of '
                                                             'the pit.',
                                                     'why': 'Grafts ensure the '
                                                            'plant inherits '
                                                            'the exact fruit '
                                                            'quality of the '
                                                            'parent tree, '
                                                            'unlike seeds.'},
                                                 {   'title': 'Irrigation',
                                                     'desc': 'Water regularly '
                                                             'for first 3 '
                                                             'years.',
                                                     'why': 'Young saplings '
                                                            'have shallow '
                                                            'roots and cannot '
                                                            'survive dry '
                                                            'spells without '
                                                            'consistent '
                                                            'moisture.'},
                                                 {   'title': 'Harvesting',
                                                     'desc': 'Pluck fruits '
                                                             'with a stalk to '
                                                             'avoid sap burn.',
                                                     'why': 'Mango sap is '
                                                            'highly acidic; if '
                                                            'it drips onto the '
                                                            'skin of the '
                                                            'fruit, it causes '
                                                            'black lesions '
                                                            'that cause '
                                                            'rotting.'}],
                                    'challenges': [   {   'issue': 'Fruit '
                                                                   'flies',
                                                          'solution': 'Use '
                                                                      'pheromone '
                                                                      'traps '
                                                                      'and '
                                                                      'apply '
                                                                      'neem '
                                                                      'oil '
                                                                      'spray '
                                                                      'as a '
                                                                      'natural '
                                                                      'deterrent.'},
                                                      {   'issue': 'Powdery '
                                                                   'mildew '
                                                                   'fungus',
                                                          'solution': 'Spray '
                                                                      'wettable '
                                                                      'sulfur '
                                                                      'at the '
                                                                      'first '
                                                                      'sign of '
                                                                      'white '
                                                                      'powdery '
                                                                      'spots '
                                                                      'on '
                                                                      'leaves.'},
                                                      {   'issue': 'Alternate '
                                                                   'bearing',
                                                          'solution': 'Apply '
                                                                      'Paclobutrazol '
                                                                      '(a '
                                                                      'plant '
                                                                      'growth '
                                                                      'regulator) '
                                                                      'to the '
                                                                      'soil to '
                                                                      'encourage '
                                                                      'regular '
                                                                      'flowering.'}],
                                    'soil_tips': 'Grow leguminous intercrops '
                                                 '(like cowpea) between rows '
                                                 'for the first 4 years to '
                                                 'naturally fix nitrogen into '
                                                 'the soil.'}},
    'Wheat': {   'name_en': 'Wheat',
                 'name_hi': 'Wheat / गेहूँ',
                 'season': 'Rabi',
                 'regions': ['East', 'North', 'West'],
                 'ph': (6.0, 7.5),
                 'moisture': (50, 70),
                 'ec': (0, 2.0),
                 'n': (120, 250),
                 'p': (15, 40),
                 'k': (120, 250),
                 'soils': [   'Alluvial Soil (Fertile)',
                              'Black Soil (Regur)',
                              'Red & Yellow Soil',
                              'Peaty/Marshy Soil'],
                 'water_needs': 'Medium',
                 'crop_type': 'Cereal',
                 'sowing_months': ['Oct', 'Nov'],
                 'harvest_months': ['Mar', 'Apr'],
                 'farm_school': {   'steps': [   {   'title': 'Field Prep',
                                                     'desc': 'Plough the field '
                                                             '2-3 times to get '
                                                             'fine tilth.',
                                                     'why': 'A fine seedbed '
                                                            'ensures maximum '
                                                            'seed-to-soil '
                                                            'contact for '
                                                            'uniform '
                                                            'germination.'},
                                                 {   'title': 'Sowing',
                                                     'desc': 'Drill seeds at a '
                                                             'depth of 4-5 cm.',
                                                     'why': 'Sowing too deep '
                                                            'prevents the '
                                                            'shoot from '
                                                            'reaching the '
                                                            'surface; too '
                                                            'shallow exposes '
                                                            'seeds to birds.'},
                                                 {   'title': 'Irrigation',
                                                     'desc': 'Provide 4-6 '
                                                             'irrigations at '
                                                             'critical stages.',
                                                     'why': 'The Crown Root '
                                                            'Initiation (CRI) '
                                                            'stage is highly '
                                                            'water-sensitive; '
                                                            'stress here '
                                                            'drastically '
                                                            'reduces yield.'},
                                                 {   'title': 'Harvesting',
                                                     'desc': 'Cut when grains '
                                                             'become hard and '
                                                             'moisture is < '
                                                             '15%.',
                                                     'why': 'Harvesting with '
                                                            'high moisture '
                                                            'leads to fungal '
                                                            'growth during '
                                                            'storage.'}],
                                    'challenges': [   {   'issue': 'Termites',
                                                          'solution': 'Treat '
                                                                      'seeds '
                                                                      'with '
                                                                      'chlorpyrifos '
                                                                      'before '
                                                                      'sowing '
                                                                      'and '
                                                                      'ensure '
                                                                      'the '
                                                                      'field '
                                                                      'is '
                                                                      'well-irrigated.'},
                                                      {   'issue': 'Yellow '
                                                                   'rust '
                                                                   'disease',
                                                          'solution': 'Grow '
                                                                      'rust-resistant '
                                                                      'varieties '
                                                                      'and '
                                                                      'spray '
                                                                      'propiconazole '
                                                                      'if '
                                                                      'yellow '
                                                                      'stripes '
                                                                      'appear '
                                                                      'on '
                                                                      'leaves.'},
                                                      {   'issue': 'Heat '
                                                                   'stress '
                                                                   'during '
                                                                   'grain '
                                                                   'filling',
                                                          'solution': 'Maintain '
                                                                      'adequate '
                                                                      'soil '
                                                                      'moisture '
                                                                      'during '
                                                                      'the '
                                                                      'late '
                                                                      'growth '
                                                                      'stages '
                                                                      'to cool '
                                                                      'the '
                                                                      'microclimate.'}],
                                    'soil_tips': 'Incorporate wheat stubble '
                                                 'back into the soil instead '
                                                 'of burning it; this builds '
                                                 'soil organic carbon.'}},
    'Paddy': {   'name_en': 'Paddy / Rice',
                 'name_hi': 'Paddy / धान',
                 'season': 'Kharif',
                 'regions': ['East', 'North', 'South', 'West'],
                 'ph': (5.5, 7.0),
                 'moisture': (60, 90),
                 'ec': (0, 3.0),
                 'n': (100, 200),
                 'p': (12, 35),
                 'k': (100, 200),
                 'soils': [   'Alluvial Soil (Fertile)',
                              'Black Soil (Regur)',
                              'Red & Yellow Soil',
                              'Peaty/Marshy Soil'],
                 'water_needs': 'High',
                 'crop_type': 'Cereal',
                 'sowing_months': ['Jun', 'Jul'],
                 'harvest_months': ['Nov', 'Dec'],
                 'farm_school': {   'steps': [   {   'title': 'Nursery',
                                                     'desc': 'Grow seedlings '
                                                             'for 20-30 days.',
                                                     'why': 'Raising seedlings '
                                                            'in a controlled '
                                                            'area allows for '
                                                            'rigorous weed and '
                                                            'pest management '
                                                            'early on.'},
                                                 {   'title': 'Transplanting',
                                                     'desc': 'Plant seedlings '
                                                             'in puddled '
                                                             'fields.',
                                                     'why': 'Puddling destroys '
                                                            'soil structure to '
                                                            'create a hardpan, '
                                                            'preventing water '
                                                            'from draining '
                                                            'away.'},
                                                 {   'title': 'Water '
                                                              'Management',
                                                     'desc': 'Maintain 2-5 cm '
                                                             'of standing '
                                                             'water.',
                                                     'why': 'Standing water '
                                                            'suppresses weed '
                                                            'growth because '
                                                            'most terrestrial '
                                                            'weeds cannot '
                                                            'survive '
                                                            'submerged.'},
                                                 {   'title': 'Harvesting',
                                                     'desc': 'Drain water 15 '
                                                             'days before '
                                                             'harvest.',
                                                     'why': 'Drying the field '
                                                            'hardens the soil, '
                                                            'making it easier '
                                                            'for labor or '
                                                            'machinery to '
                                                            'operate.'}],
                                    'challenges': [   {   'issue': 'Stem '
                                                                   'borers',
                                                          'solution': 'Use '
                                                                      'trichogramma '
                                                                      '(a '
                                                                      'beneficial '
                                                                      'wasp) '
                                                                      'egg '
                                                                      'cards '
                                                                      'in the '
                                                                      'field '
                                                                      'as a '
                                                                      'biological '
                                                                      'control.'},
                                                      {   'issue': 'Bacterial '
                                                                   'leaf '
                                                                   'blight',
                                                          'solution': 'Avoid '
                                                                      'excess '
                                                                      'nitrogen '
                                                                      'application '
                                                                      'and '
                                                                      'drain '
                                                                      'the '
                                                                      'field '
                                                                      'temporarily '
                                                                      'to stop '
                                                                      'the '
                                                                      'spread.'},
                                                      {   'issue': 'High '
                                                                   'methane '
                                                                   'emissions',
                                                          'solution': 'Practice '
                                                                      'Alternate '
                                                                      'Wetting '
                                                                      'and '
                                                                      'Drying '
                                                                      '(AWD) '
                                                                      'instead '
                                                                      'of '
                                                                      'continuous '
                                                                      'flooding.'}],
                                    'soil_tips': 'Practice crop rotation with '
                                                 'pulses (like Gram) after '
                                                 'paddy to naturally break the '
                                                 'hardpan and restore '
                                                 'nitrogen.'}},
    'Cotton': {   'name_en': 'Cotton',
                  'name_hi': 'Cotton / कपास',
                  'season': 'Kharif',
                  'regions': ['North', 'South', 'West'],
                  'ph': (6.0, 8.0),
                  'moisture': (35, 60),
                  'ec': (0, 4.0),
                  'n': (90, 160),
                  'p': (10, 25),
                  'k': (150, 300),
                  'soils': [   'Black Soil (Regur)',
                               'Red & Yellow Soil',
                               'Arid / Desert Soil',
                               'Coastal Sandy Soil'],
                  'water_needs': 'Medium',
                  'crop_type': 'Cash Crop',
                  'sowing_months': ['May', 'Jun'],
                  'harvest_months': ['Oct', 'Nov', 'Dec'],
                  'farm_school': {   'steps': [   {   'title': 'Seed/Land Prep',
                                                      'desc': 'Prepare the '
                                                              'land '
                                                              'specifically '
                                                              'for Cotton.',
                                                      'why': 'Proper land '
                                                             'preparation '
                                                             'provides '
                                                             'aeration to the '
                                                             'roots and kills '
                                                             'early weeds.'},
                                                  {   'title': 'Sowing & Care',
                                                      'desc': 'Sow the seeds '
                                                              'at the correct '
                                                              'depth and '
                                                              'spacing.',
                                                      'why': 'Optimal spacing '
                                                             'prevents plants '
                                                             'from competing '
                                                             'with each other '
                                                             'for sunlight and '
                                                             'nutrients.'},
                                                  {   'title': 'Irrigation',
                                                      'desc': 'Water at '
                                                              'critical growth '
                                                              'stages.',
                                                      'why': 'Water acts as '
                                                             'the transport '
                                                             'system carrying '
                                                             'soil nutrients '
                                                             'up into the '
                                                             'plant tissues.'},
                                                  {   'title': 'Harvesting',
                                                      'desc': 'Harvest Cotton '
                                                              'at peak '
                                                              'maturity.',
                                                      'why': 'Harvesting at '
                                                             'the right time '
                                                             'maximizes '
                                                             'nutritional '
                                                             'value and market '
                                                             'shelf-life.'}],
                                     'challenges': [   {   'issue': 'Local '
                                                                    'pests and '
                                                                    'insects',
                                                           'solution': 'Regularly '
                                                                       'scout '
                                                                       'the '
                                                                       'field '
                                                                       'and '
                                                                       'use '
                                                                       'integrated '
                                                                       'pest '
                                                                       'management '
                                                                       '(IPM) '
                                                                       'techniques '
                                                                       'like '
                                                                       'neem '
                                                                       'oil.'},
                                                       {   'issue': 'Unpredictable '
                                                                    'weather '
                                                                    'patterns',
                                                           'solution': 'Ensure '
                                                                       'good '
                                                                       'drainage '
                                                                       'to '
                                                                       'prevent '
                                                                       'waterlogging, '
                                                                       'and '
                                                                       'mulch '
                                                                       'the '
                                                                       'soil '
                                                                       'to '
                                                                       'retain '
                                                                       'moisture '
                                                                       'during '
                                                                       'droughts.'},
                                                       {   'issue': 'Weed '
                                                                    'competition',
                                                           'solution': 'Perform '
                                                                       'manual '
                                                                       'weeding '
                                                                       'during '
                                                                       'the '
                                                                       'first '
                                                                       '30-45 '
                                                                       'days, '
                                                                       'which '
                                                                       'is the '
                                                                       'critical '
                                                                       'weed-free '
                                                                       'period.'}],
                                     'soil_tips': 'Use organic compost and '
                                                  'practice crop rotation to '
                                                  'maintain soil health and '
                                                  'microbiome diversity.'}},
    'Mustard': {   'name_en': 'Mustard',
                   'name_hi': 'Mustard / सरसों',
                   'season': 'Rabi',
                   'regions': ['East', 'North', 'West'],
                   'ph': (6.0, 7.5),
                   'moisture': (25, 45),
                   'ec': (0, 3.0),
                   'n': (80, 150),
                   'p': (12, 30),
                   'k': (100, 180),
                   'soils': ['Alluvial Soil (Fertile)', 'Arid / Desert Soil'],
                   'water_needs': 'Low',
                   'crop_type': 'Oilseed',
                   'sowing_months': ['Oct', 'Nov'],
                   'harvest_months': ['Feb', 'Mar'],
                   'farm_school': {   'steps': [   {   'title': 'Seed/Land '
                                                                'Prep',
                                                       'desc': 'Prepare the '
                                                               'land '
                                                               'specifically '
                                                               'for Mustard.',
                                                       'why': 'Proper land '
                                                              'preparation '
                                                              'provides '
                                                              'aeration to the '
                                                              'roots and kills '
                                                              'early weeds.'},
                                                   {   'title': 'Sowing & Care',
                                                       'desc': 'Sow the seeds '
                                                               'at the correct '
                                                               'depth and '
                                                               'spacing.',
                                                       'why': 'Optimal spacing '
                                                              'prevents plants '
                                                              'from competing '
                                                              'with each other '
                                                              'for sunlight '
                                                              'and nutrients.'},
                                                   {   'title': 'Irrigation',
                                                       'desc': 'Water at '
                                                               'critical '
                                                               'growth stages.',
                                                       'why': 'Water acts as '
                                                              'the transport '
                                                              'system carrying '
                                                              'soil nutrients '
                                                              'up into the '
                                                              'plant tissues.'},
                                                   {   'title': 'Harvesting',
                                                       'desc': 'Harvest '
                                                               'Mustard at '
                                                               'peak maturity.',
                                                       'why': 'Harvesting at '
                                                              'the right time '
                                                              'maximizes '
                                                              'nutritional '
                                                              'value and '
                                                              'market '
                                                              'shelf-life.'}],
                                      'challenges': [   {   'issue': 'Local '
                                                                     'pests '
                                                                     'and '
                                                                     'insects',
                                                            'solution': 'Regularly '
                                                                        'scout '
                                                                        'the '
                                                                        'field '
                                                                        'and '
                                                                        'use '
                                                                        'integrated '
                                                                        'pest '
                                                                        'management '
                                                                        '(IPM) '
                                                                        'techniques '
                                                                        'like '
                                                                        'neem '
                                                                        'oil.'},
                                                        {   'issue': 'Unpredictable '
                                                                     'weather '
                                                                     'patterns',
                                                            'solution': 'Ensure '
                                                                        'good '
                                                                        'drainage '
                                                                        'to '
                                                                        'prevent '
                                                                        'waterlogging, '
                                                                        'and '
                                                                        'mulch '
                                                                        'the '
                                                                        'soil '
                                                                        'to '
                                                                        'retain '
                                                                        'moisture '
                                                                        'during '
                                                                        'droughts.'},
                                                        {   'issue': 'Weed '
                                                                     'competition',
                                                            'solution': 'Perform '
                                                                        'manual '
                                                                        'weeding '
                                                                        'during '
                                                                        'the '
                                                                        'first '
                                                                        '30-45 '
                                                                        'days, '
                                                                        'which '
                                                                        'is '
                                                                        'the '
                                                                        'critical '
                                                                        'weed-free '
                                                                        'period.'}],
                                      'soil_tips': 'Use organic compost and '
                                                   'practice crop rotation to '
                                                   'maintain soil health and '
                                                   'microbiome diversity.'}},
    'Maize': {   'name_en': 'Maize',
                 'name_hi': 'Maize / मक्का',
                 'season': 'Kharif',
                 'regions': ['East', 'North', 'South', 'West'],
                 'ph': (5.8, 7.2),
                 'moisture': (45, 65),
                 'ec': (0, 2.0),
                 'n': (120, 250),
                 'p': (15, 30),
                 'k': (120, 220),
                 'soils': ['Alluvial Soil (Fertile)', 'Red & Yellow Soil'],
                 'water_needs': 'Medium',
                 'crop_type': 'Cereal',
                 'sowing_months': ['Jun', 'Jul'],
                 'harvest_months': ['Sep', 'Oct'],
                 'farm_school': {   'steps': [   {   'title': 'Seed/Land Prep',
                                                     'desc': 'Prepare the land '
                                                             'specifically for '
                                                             'Maize.',
                                                     'why': 'Proper land '
                                                            'preparation '
                                                            'provides aeration '
                                                            'to the roots and '
                                                            'kills early '
                                                            'weeds.'},
                                                 {   'title': 'Sowing & Care',
                                                     'desc': 'Sow the seeds at '
                                                             'the correct '
                                                             'depth and '
                                                             'spacing.',
                                                     'why': 'Optimal spacing '
                                                            'prevents plants '
                                                            'from competing '
                                                            'with each other '
                                                            'for sunlight and '
                                                            'nutrients.'},
                                                 {   'title': 'Irrigation',
                                                     'desc': 'Water at '
                                                             'critical growth '
                                                             'stages.',
                                                     'why': 'Water acts as the '
                                                            'transport system '
                                                            'carrying soil '
                                                            'nutrients up into '
                                                            'the plant '
                                                            'tissues.'},
                                                 {   'title': 'Harvesting',
                                                     'desc': 'Harvest Maize at '
                                                             'peak maturity.',
                                                     'why': 'Harvesting at the '
                                                            'right time '
                                                            'maximizes '
                                                            'nutritional value '
                                                            'and market '
                                                            'shelf-life.'}],
                                    'challenges': [   {   'issue': 'Local '
                                                                   'pests and '
                                                                   'insects',
                                                          'solution': 'Regularly '
                                                                      'scout '
                                                                      'the '
                                                                      'field '
                                                                      'and use '
                                                                      'integrated '
                                                                      'pest '
                                                                      'management '
                                                                      '(IPM) '
                                                                      'techniques '
                                                                      'like '
                                                                      'neem '
                                                                      'oil.'},
                                                      {   'issue': 'Unpredictable '
                                                                   'weather '
                                                                   'patterns',
                                                          'solution': 'Ensure '
                                                                      'good '
                                                                      'drainage '
                                                                      'to '
                                                                      'prevent '
                                                                      'waterlogging, '
                                                                      'and '
                                                                      'mulch '
                                                                      'the '
                                                                      'soil to '
                                                                      'retain '
                                                                      'moisture '
                                                                      'during '
                                                                      'droughts.'},
                                                      {   'issue': 'Weed '
                                                                   'competition',
                                                          'solution': 'Perform '
                                                                      'manual '
                                                                      'weeding '
                                                                      'during '
                                                                      'the '
                                                                      'first '
                                                                      '30-45 '
                                                                      'days, '
                                                                      'which '
                                                                      'is the '
                                                                      'critical '
                                                                      'weed-free '
                                                                      'period.'}],
                                    'soil_tips': 'Use organic compost and '
                                                 'practice crop rotation to '
                                                 'maintain soil health and '
                                                 'microbiome diversity.'}},
    'Potato': {   'name_en': 'Potato',
                  'name_hi': 'Potato / आलू',
                  'season': 'Rabi',
                  'regions': ['East', 'North', 'West'],
                  'ph': (5.0, 6.5),
                  'moisture': (50, 70),
                  'ec': (0, 1.8),
                  'n': (120, 250),
                  'p': (20, 45),
                  'k': (180, 300),
                  'soils': ['Alluvial Soil (Fertile)', 'Red & Yellow Soil'],
                  'water_needs': 'High',
                  'crop_type': 'Vegetable',
                  'sowing_months': ['Oct', 'Nov'],
                  'harvest_months': ['Feb', 'Mar'],
                  'farm_school': {   'steps': [   {   'title': 'Seed/Land Prep',
                                                      'desc': 'Prepare the '
                                                              'land '
                                                              'specifically '
                                                              'for Potato.',
                                                      'why': 'Proper land '
                                                             'preparation '
                                                             'provides '
                                                             'aeration to the '
                                                             'roots and kills '
                                                             'early weeds.'},
                                                  {   'title': 'Sowing & Care',
                                                      'desc': 'Sow the seeds '
                                                              'at the correct '
                                                              'depth and '
                                                              'spacing.',
                                                      'why': 'Optimal spacing '
                                                             'prevents plants '
                                                             'from competing '
                                                             'with each other '
                                                             'for sunlight and '
                                                             'nutrients.'},
                                                  {   'title': 'Irrigation',
                                                      'desc': 'Water at '
                                                              'critical growth '
                                                              'stages.',
                                                      'why': 'Water acts as '
                                                             'the transport '
                                                             'system carrying '
                                                             'soil nutrients '
                                                             'up into the '
                                                             'plant tissues.'},
                                                  {   'title': 'Harvesting',
                                                      'desc': 'Harvest Potato '
                                                              'at peak '
                                                              'maturity.',
                                                      'why': 'Harvesting at '
                                                             'the right time '
                                                             'maximizes '
                                                             'nutritional '
                                                             'value and market '
                                                             'shelf-life.'}],
                                     'challenges': [   {   'issue': 'Local '
                                                                    'pests and '
                                                                    'insects',
                                                           'solution': 'Regularly '
                                                                       'scout '
                                                                       'the '
                                                                       'field '
                                                                       'and '
                                                                       'use '
                                                                       'integrated '
                                                                       'pest '
                                                                       'management '
                                                                       '(IPM) '
                                                                       'techniques '
                                                                       'like '
                                                                       'neem '
                                                                       'oil.'},
                                                       {   'issue': 'Unpredictable '
                                                                    'weather '
                                                                    'patterns',
                                                           'solution': 'Ensure '
                                                                       'good '
                                                                       'drainage '
                                                                       'to '
                                                                       'prevent '
                                                                       'waterlogging, '
                                                                       'and '
                                                                       'mulch '
                                                                       'the '
                                                                       'soil '
                                                                       'to '
                                                                       'retain '
                                                                       'moisture '
                                                                       'during '
                                                                       'droughts.'},
                                                       {   'issue': 'Weed '
                                                                    'competition',
                                                           'solution': 'Perform '
                                                                       'manual '
                                                                       'weeding '
                                                                       'during '
                                                                       'the '
                                                                       'first '
                                                                       '30-45 '
                                                                       'days, '
                                                                       'which '
                                                                       'is the '
                                                                       'critical '
                                                                       'weed-free '
                                                                       'period.'}],
                                     'soil_tips': 'Use organic compost and '
                                                  'practice crop rotation to '
                                                  'maintain soil health and '
                                                  'microbiome diversity.'}},
    'Sugarcane': {   'name_en': 'Sugarcane',
                     'name_hi': 'Sugarcane / गन्ना',
                     'season': 'Kharif',
                     'regions': ['North', 'South', 'West'],
                     'ph': (6.0, 7.5),
                     'moisture': (65, 85),
                     'ec': (0, 2.5),
                     'n': (150, 300),
                     'p': (25, 50),
                     'k': (200, 400),
                     'soils': ['Alluvial Soil (Fertile)', 'Black Soil (Regur)'],
                     'water_needs': 'High',
                     'crop_type': 'Cash Crop',
                     'sowing_months': ['Jan', 'Feb', 'Mar'],
                     'harvest_months': ['Dec', 'Jan', 'Feb'],
                     'farm_school': {   'steps': [   {   'title': 'Seed/Land '
                                                                  'Prep',
                                                         'desc': 'Prepare the '
                                                                 'land '
                                                                 'specifically '
                                                                 'for '
                                                                 'Sugarcane.',
                                                         'why': 'Proper land '
                                                                'preparation '
                                                                'provides '
                                                                'aeration to '
                                                                'the roots and '
                                                                'kills early '
                                                                'weeds.'},
                                                     {   'title': 'Sowing & '
                                                                  'Care',
                                                         'desc': 'Sow the '
                                                                 'seeds at the '
                                                                 'correct '
                                                                 'depth and '
                                                                 'spacing.',
                                                         'why': 'Optimal '
                                                                'spacing '
                                                                'prevents '
                                                                'plants from '
                                                                'competing '
                                                                'with each '
                                                                'other for '
                                                                'sunlight and '
                                                                'nutrients.'},
                                                     {   'title': 'Irrigation',
                                                         'desc': 'Water at '
                                                                 'critical '
                                                                 'growth '
                                                                 'stages.',
                                                         'why': 'Water acts as '
                                                                'the transport '
                                                                'system '
                                                                'carrying soil '
                                                                'nutrients up '
                                                                'into the '
                                                                'plant '
                                                                'tissues.'},
                                                     {   'title': 'Harvesting',
                                                         'desc': 'Harvest '
                                                                 'Sugarcane at '
                                                                 'peak '
                                                                 'maturity.',
                                                         'why': 'Harvesting at '
                                                                'the right '
                                                                'time '
                                                                'maximizes '
                                                                'nutritional '
                                                                'value and '
                                                                'market '
                                                                'shelf-life.'}],
                                        'challenges': [   {   'issue': 'Local '
                                                                       'pests '
                                                                       'and '
                                                                       'insects',
                                                              'solution': 'Regularly '
                                                                          'scout '
                                                                          'the '
                                                                          'field '
                                                                          'and '
                                                                          'use '
                                                                          'integrated '
                                                                          'pest '
                                                                          'management '
                                                                          '(IPM) '
                                                                          'techniques '
                                                                          'like '
                                                                          'neem '
                                                                          'oil.'},
                                                          {   'issue': 'Unpredictable '
                                                                       'weather '
                                                                       'patterns',
                                                              'solution': 'Ensure '
                                                                          'good '
                                                                          'drainage '
                                                                          'to '
                                                                          'prevent '
                                                                          'waterlogging, '
                                                                          'and '
                                                                          'mulch '
                                                                          'the '
                                                                          'soil '
                                                                          'to '
                                                                          'retain '
                                                                          'moisture '
                                                                          'during '
                                                                          'droughts.'},
                                                          {   'issue': 'Weed '
                                                                       'competition',
                                                              'solution': 'Perform '
                                                                          'manual '
                                                                          'weeding '
                                                                          'during '
                                                                          'the '
                                                                          'first '
                                                                          '30-45 '
                                                                          'days, '
                                                                          'which '
                                                                          'is '
                                                                          'the '
                                                                          'critical '
                                                                          'weed-free '
                                                                          'period.'}],
                                        'soil_tips': 'Use organic compost and '
                                                     'practice crop rotation '
                                                     'to maintain soil health '
                                                     'and microbiome '
                                                     'diversity.'}},
    'Jute': {   'name_en': 'Jute',
                'name_hi': 'Jute / जूट',
                'season': 'Kharif',
                'regions': ['East'],
                'ph': (6.0, 7.5),
                'moisture': (70, 90),
                'ec': (0, 1.5),
                'n': (100, 200),
                'p': (15, 30),
                'k': (100, 200),
                'soils': ['Alluvial Soil (Fertile)'],
                'water_needs': 'High',
                'crop_type': 'Cash Crop',
                'sowing_months': ['Feb', 'Mar'],
                'harvest_months': ['Jul', 'Aug'],
                'farm_school': {   'steps': [   {   'title': 'Seed/Land Prep',
                                                    'desc': 'Prepare the land '
                                                            'specifically for '
                                                            'Jute.',
                                                    'why': 'Proper land '
                                                           'preparation '
                                                           'provides aeration '
                                                           'to the roots and '
                                                           'kills early '
                                                           'weeds.'},
                                                {   'title': 'Sowing & Care',
                                                    'desc': 'Sow the seeds at '
                                                            'the correct depth '
                                                            'and spacing.',
                                                    'why': 'Optimal spacing '
                                                           'prevents plants '
                                                           'from competing '
                                                           'with each other '
                                                           'for sunlight and '
                                                           'nutrients.'},
                                                {   'title': 'Irrigation',
                                                    'desc': 'Water at critical '
                                                            'growth stages.',
                                                    'why': 'Water acts as the '
                                                           'transport system '
                                                           'carrying soil '
                                                           'nutrients up into '
                                                           'the plant '
                                                           'tissues.'},
                                                {   'title': 'Harvesting',
                                                    'desc': 'Harvest Jute at '
                                                            'peak maturity.',
                                                    'why': 'Harvesting at the '
                                                           'right time '
                                                           'maximizes '
                                                           'nutritional value '
                                                           'and market '
                                                           'shelf-life.'}],
                                   'challenges': [   {   'issue': 'Local pests '
                                                                  'and insects',
                                                         'solution': 'Regularly '
                                                                     'scout '
                                                                     'the '
                                                                     'field '
                                                                     'and use '
                                                                     'integrated '
                                                                     'pest '
                                                                     'management '
                                                                     '(IPM) '
                                                                     'techniques '
                                                                     'like '
                                                                     'neem '
                                                                     'oil.'},
                                                     {   'issue': 'Unpredictable '
                                                                  'weather '
                                                                  'patterns',
                                                         'solution': 'Ensure '
                                                                     'good '
                                                                     'drainage '
                                                                     'to '
                                                                     'prevent '
                                                                     'waterlogging, '
                                                                     'and '
                                                                     'mulch '
                                                                     'the soil '
                                                                     'to '
                                                                     'retain '
                                                                     'moisture '
                                                                     'during '
                                                                     'droughts.'},
                                                     {   'issue': 'Weed '
                                                                  'competition',
                                                         'solution': 'Perform '
                                                                     'manual '
                                                                     'weeding '
                                                                     'during '
                                                                     'the '
                                                                     'first '
                                                                     '30-45 '
                                                                     'days, '
                                                                     'which is '
                                                                     'the '
                                                                     'critical '
                                                                     'weed-free '
                                                                     'period.'}],
                                   'soil_tips': 'Use organic compost and '
                                                'practice crop rotation to '
                                                'maintain soil health and '
                                                'microbiome diversity.'}},
    'Tea': {   'name_en': 'Tea',
               'name_hi': 'Tea / चाय',
               'season': 'Kharif',
               'regions': ['East', 'South'],
               'ph': (4.5, 5.5),
               'moisture': (70, 95),
               'ec': (0, 1.0),
               'n': (120, 240),
               'p': (10, 20),
               'k': (100, 200),
               'soils': ['Forest/Mountain Soil', 'Laterite Soil'],
               'water_needs': 'High',
               'crop_type': 'Plantation',
               'sowing_months': ['Oct', 'Nov'],
               'harvest_months': ['Mar', 'Apr', 'May', 'Jun', 'Jul'],
               'farm_school': {   'steps': [   {   'title': 'Seed/Land Prep',
                                                   'desc': 'Prepare the land '
                                                           'specifically for '
                                                           'Tea.',
                                                   'why': 'Proper land '
                                                          'preparation '
                                                          'provides aeration '
                                                          'to the roots and '
                                                          'kills early weeds.'},
                                               {   'title': 'Sowing & Care',
                                                   'desc': 'Sow the seeds at '
                                                           'the correct depth '
                                                           'and spacing.',
                                                   'why': 'Optimal spacing '
                                                          'prevents plants '
                                                          'from competing with '
                                                          'each other for '
                                                          'sunlight and '
                                                          'nutrients.'},
                                               {   'title': 'Irrigation',
                                                   'desc': 'Water at critical '
                                                           'growth stages.',
                                                   'why': 'Water acts as the '
                                                          'transport system '
                                                          'carrying soil '
                                                          'nutrients up into '
                                                          'the plant tissues.'},
                                               {   'title': 'Harvesting',
                                                   'desc': 'Harvest Tea at '
                                                           'peak maturity.',
                                                   'why': 'Harvesting at the '
                                                          'right time '
                                                          'maximizes '
                                                          'nutritional value '
                                                          'and market '
                                                          'shelf-life.'}],
                                  'challenges': [   {   'issue': 'Local pests '
                                                                 'and insects',
                                                        'solution': 'Regularly '
                                                                    'scout the '
                                                                    'field and '
                                                                    'use '
                                                                    'integrated '
                                                                    'pest '
                                                                    'management '
                                                                    '(IPM) '
                                                                    'techniques '
                                                                    'like neem '
                                                                    'oil.'},
                                                    {   'issue': 'Unpredictable '
                                                                 'weather '
                                                                 'patterns',
                                                        'solution': 'Ensure '
                                                                    'good '
                                                                    'drainage '
                                                                    'to '
                                                                    'prevent '
                                                                    'waterlogging, '
                                                                    'and mulch '
                                                                    'the soil '
                                                                    'to retain '
                                                                    'moisture '
                                                                    'during '
                                                                    'droughts.'},
                                                    {   'issue': 'Weed '
                                                                 'competition',
                                                        'solution': 'Perform '
                                                                    'manual '
                                                                    'weeding '
                                                                    'during '
                                                                    'the first '
                                                                    '30-45 '
                                                                    'days, '
                                                                    'which is '
                                                                    'the '
                                                                    'critical '
                                                                    'weed-free '
                                                                    'period.'}],
                                  'soil_tips': 'Use organic compost and '
                                               'practice crop rotation to '
                                               'maintain soil health and '
                                               'microbiome diversity.'}},
    'Coffee': {   'name_en': 'Coffee',
                  'name_hi': 'Coffee / कॉफ़ी',
                  'season': 'Kharif',
                  'regions': ['South'],
                  'ph': (5.5, 6.5),
                  'moisture': (60, 85),
                  'ec': (0, 1.0),
                  'n': (100, 200),
                  'p': (10, 25),
                  'k': (150, 250),
                  'soils': ['Forest/Mountain Soil', 'Laterite Soil'],
                  'water_needs': 'Medium',
                  'crop_type': 'Plantation',
                  'sowing_months': ['Aug', 'Sep'],
                  'harvest_months': ['Nov', 'Dec', 'Jan'],
                  'farm_school': {   'steps': [   {   'title': 'Seed/Land Prep',
                                                      'desc': 'Prepare the '
                                                              'land '
                                                              'specifically '
                                                              'for Coffee.',
                                                      'why': 'Proper land '
                                                             'preparation '
                                                             'provides '
                                                             'aeration to the '
                                                             'roots and kills '
                                                             'early weeds.'},
                                                  {   'title': 'Sowing & Care',
                                                      'desc': 'Sow the seeds '
                                                              'at the correct '
                                                              'depth and '
                                                              'spacing.',
                                                      'why': 'Optimal spacing '
                                                             'prevents plants '
                                                             'from competing '
                                                             'with each other '
                                                             'for sunlight and '
                                                             'nutrients.'},
                                                  {   'title': 'Irrigation',
                                                      'desc': 'Water at '
                                                              'critical growth '
                                                              'stages.',
                                                      'why': 'Water acts as '
                                                             'the transport '
                                                             'system carrying '
                                                             'soil nutrients '
                                                             'up into the '
                                                             'plant tissues.'},
                                                  {   'title': 'Harvesting',
                                                      'desc': 'Harvest Coffee '
                                                              'at peak '
                                                              'maturity.',
                                                      'why': 'Harvesting at '
                                                             'the right time '
                                                             'maximizes '
                                                             'nutritional '
                                                             'value and market '
                                                             'shelf-life.'}],
                                     'challenges': [   {   'issue': 'Local '
                                                                    'pests and '
                                                                    'insects',
                                                           'solution': 'Regularly '
                                                                       'scout '
                                                                       'the '
                                                                       'field '
                                                                       'and '
                                                                       'use '
                                                                       'integrated '
                                                                       'pest '
                                                                       'management '
                                                                       '(IPM) '
                                                                       'techniques '
                                                                       'like '
                                                                       'neem '
                                                                       'oil.'},
                                                       {   'issue': 'Unpredictable '
                                                                    'weather '
                                                                    'patterns',
                                                           'solution': 'Ensure '
                                                                       'good '
                                                                       'drainage '
                                                                       'to '
                                                                       'prevent '
                                                                       'waterlogging, '
                                                                       'and '
                                                                       'mulch '
                                                                       'the '
                                                                       'soil '
                                                                       'to '
                                                                       'retain '
                                                                       'moisture '
                                                                       'during '
                                                                       'droughts.'},
                                                       {   'issue': 'Weed '
                                                                    'competition',
                                                           'solution': 'Perform '
                                                                       'manual '
                                                                       'weeding '
                                                                       'during '
                                                                       'the '
                                                                       'first '
                                                                       '30-45 '
                                                                       'days, '
                                                                       'which '
                                                                       'is the '
                                                                       'critical '
                                                                       'weed-free '
                                                                       'period.'}],
                                     'soil_tips': 'Use organic compost and '
                                                  'practice crop rotation to '
                                                  'maintain soil health and '
                                                  'microbiome diversity.'}},
    'Rubber': {   'name_en': 'Rubber',
                  'name_hi': 'Rubber / रबर',
                  'season': 'Kharif',
                  'regions': ['East', 'South'],
                  'ph': (4.5, 6.0),
                  'moisture': (70, 90),
                  'ec': (0, 1.0),
                  'n': (80, 150),
                  'p': (10, 20),
                  'k': (100, 200),
                  'soils': ['Laterite Soil'],
                  'water_needs': 'High',
                  'crop_type': 'Plantation',
                  'sowing_months': ['Jun', 'Jul'],
                  'harvest_months': ['Sep', 'Oct', 'Nov'],
                  'farm_school': {   'steps': [   {   'title': 'Seed/Land Prep',
                                                      'desc': 'Prepare the '
                                                              'land '
                                                              'specifically '
                                                              'for Rubber.',
                                                      'why': 'Proper land '
                                                             'preparation '
                                                             'provides '
                                                             'aeration to the '
                                                             'roots and kills '
                                                             'early weeds.'},
                                                  {   'title': 'Sowing & Care',
                                                      'desc': 'Sow the seeds '
                                                              'at the correct '
                                                              'depth and '
                                                              'spacing.',
                                                      'why': 'Optimal spacing '
                                                             'prevents plants '
                                                             'from competing '
                                                             'with each other '
                                                             'for sunlight and '
                                                             'nutrients.'},
                                                  {   'title': 'Irrigation',
                                                      'desc': 'Water at '
                                                              'critical growth '
                                                              'stages.',
                                                      'why': 'Water acts as '
                                                             'the transport '
                                                             'system carrying '
                                                             'soil nutrients '
                                                             'up into the '
                                                             'plant tissues.'},
                                                  {   'title': 'Harvesting',
                                                      'desc': 'Harvest Rubber '
                                                              'at peak '
                                                              'maturity.',
                                                      'why': 'Harvesting at '
                                                             'the right time '
                                                             'maximizes '
                                                             'nutritional '
                                                             'value and market '
                                                             'shelf-life.'}],
                                     'challenges': [   {   'issue': 'Local '
                                                                    'pests and '
                                                                    'insects',
                                                           'solution': 'Regularly '
                                                                       'scout '
                                                                       'the '
                                                                       'field '
                                                                       'and '
                                                                       'use '
                                                                       'integrated '
                                                                       'pest '
                                                                       'management '
                                                                       '(IPM) '
                                                                       'techniques '
                                                                       'like '
                                                                       'neem '
                                                                       'oil.'},
                                                       {   'issue': 'Unpredictable '
                                                                    'weather '
                                                                    'patterns',
                                                           'solution': 'Ensure '
                                                                       'good '
                                                                       'drainage '
                                                                       'to '
                                                                       'prevent '
                                                                       'waterlogging, '
                                                                       'and '
                                                                       'mulch '
                                                                       'the '
                                                                       'soil '
                                                                       'to '
                                                                       'retain '
                                                                       'moisture '
                                                                       'during '
                                                                       'droughts.'},
                                                       {   'issue': 'Weed '
                                                                    'competition',
                                                           'solution': 'Perform '
                                                                       'manual '
                                                                       'weeding '
                                                                       'during '
                                                                       'the '
                                                                       'first '
                                                                       '30-45 '
                                                                       'days, '
                                                                       'which '
                                                                       'is the '
                                                                       'critical '
                                                                       'weed-free '
                                                                       'period.'}],
                                     'soil_tips': 'Use organic compost and '
                                                  'practice crop rotation to '
                                                  'maintain soil health and '
                                                  'microbiome diversity.'}},
    'Groundnut': {   'name_en': 'Groundnut',
                     'name_hi': 'Groundnut / मूंगफली',
                     'season': 'Kharif',
                     'regions': ['North', 'South', 'West'],
                     'ph': (6.0, 7.0),
                     'moisture': (40, 60),
                     'ec': (0, 2.0),
                     'n': (80, 150),
                     'p': (15, 30),
                     'k': (100, 200),
                     'soils': ['Red & Yellow Soil', 'Arid / Desert Soil'],
                     'water_needs': 'Low',
                     'crop_type': 'Oilseed',
                     'sowing_months': ['Jun', 'Jul'],
                     'harvest_months': ['Oct', 'Nov'],
                     'farm_school': {   'steps': [   {   'title': 'Seed/Land '
                                                                  'Prep',
                                                         'desc': 'Prepare the '
                                                                 'land '
                                                                 'specifically '
                                                                 'for '
                                                                 'Groundnut.',
                                                         'why': 'Proper land '
                                                                'preparation '
                                                                'provides '
                                                                'aeration to '
                                                                'the roots and '
                                                                'kills early '
                                                                'weeds.'},
                                                     {   'title': 'Sowing & '
                                                                  'Care',
                                                         'desc': 'Sow the '
                                                                 'seeds at the '
                                                                 'correct '
                                                                 'depth and '
                                                                 'spacing.',
                                                         'why': 'Optimal '
                                                                'spacing '
                                                                'prevents '
                                                                'plants from '
                                                                'competing '
                                                                'with each '
                                                                'other for '
                                                                'sunlight and '
                                                                'nutrients.'},
                                                     {   'title': 'Irrigation',
                                                         'desc': 'Water at '
                                                                 'critical '
                                                                 'growth '
                                                                 'stages.',
                                                         'why': 'Water acts as '
                                                                'the transport '
                                                                'system '
                                                                'carrying soil '
                                                                'nutrients up '
                                                                'into the '
                                                                'plant '
                                                                'tissues.'},
                                                     {   'title': 'Harvesting',
                                                         'desc': 'Harvest '
                                                                 'Groundnut at '
                                                                 'peak '
                                                                 'maturity.',
                                                         'why': 'Harvesting at '
                                                                'the right '
                                                                'time '
                                                                'maximizes '
                                                                'nutritional '
                                                                'value and '
                                                                'market '
                                                                'shelf-life.'}],
                                        'challenges': [   {   'issue': 'Local '
                                                                       'pests '
                                                                       'and '
                                                                       'insects',
                                                              'solution': 'Regularly '
                                                                          'scout '
                                                                          'the '
                                                                          'field '
                                                                          'and '
                                                                          'use '
                                                                          'integrated '
                                                                          'pest '
                                                                          'management '
                                                                          '(IPM) '
                                                                          'techniques '
                                                                          'like '
                                                                          'neem '
                                                                          'oil.'},
                                                          {   'issue': 'Unpredictable '
                                                                       'weather '
                                                                       'patterns',
                                                              'solution': 'Ensure '
                                                                          'good '
                                                                          'drainage '
                                                                          'to '
                                                                          'prevent '
                                                                          'waterlogging, '
                                                                          'and '
                                                                          'mulch '
                                                                          'the '
                                                                          'soil '
                                                                          'to '
                                                                          'retain '
                                                                          'moisture '
                                                                          'during '
                                                                          'droughts.'},
                                                          {   'issue': 'Weed '
                                                                       'competition',
                                                              'solution': 'Perform '
                                                                          'manual '
                                                                          'weeding '
                                                                          'during '
                                                                          'the '
                                                                          'first '
                                                                          '30-45 '
                                                                          'days, '
                                                                          'which '
                                                                          'is '
                                                                          'the '
                                                                          'critical '
                                                                          'weed-free '
                                                                          'period.'}],
                                        'soil_tips': 'Use organic compost and '
                                                     'practice crop rotation '
                                                     'to maintain soil health '
                                                     'and microbiome '
                                                     'diversity.'}},
    'Soybean': {   'name_en': 'Soybean',
                   'name_hi': 'Soybean / सोयाबीन',
                   'season': 'Kharif',
                   'regions': ['North', 'West'],
                   'ph': (6.0, 7.5),
                   'moisture': (50, 70),
                   'ec': (0, 2.0),
                   'n': (80, 160),
                   'p': (15, 35),
                   'k': (120, 240),
                   'soils': ['Black Soil (Regur)', 'Red & Yellow Soil'],
                   'water_needs': 'Medium',
                   'crop_type': 'Oilseed',
                   'sowing_months': ['Jun', 'Jul'],
                   'harvest_months': ['Sep', 'Oct'],
                   'farm_school': {   'steps': [   {   'title': 'Seed/Land '
                                                                'Prep',
                                                       'desc': 'Prepare the '
                                                               'land '
                                                               'specifically '
                                                               'for Soybean.',
                                                       'why': 'Proper land '
                                                              'preparation '
                                                              'provides '
                                                              'aeration to the '
                                                              'roots and kills '
                                                              'early weeds.'},
                                                   {   'title': 'Sowing & Care',
                                                       'desc': 'Sow the seeds '
                                                               'at the correct '
                                                               'depth and '
                                                               'spacing.',
                                                       'why': 'Optimal spacing '
                                                              'prevents plants '
                                                              'from competing '
                                                              'with each other '
                                                              'for sunlight '
                                                              'and nutrients.'},
                                                   {   'title': 'Irrigation',
                                                       'desc': 'Water at '
                                                               'critical '
                                                               'growth stages.',
                                                       'why': 'Water acts as '
                                                              'the transport '
                                                              'system carrying '
                                                              'soil nutrients '
                                                              'up into the '
                                                              'plant tissues.'},
                                                   {   'title': 'Harvesting',
                                                       'desc': 'Harvest '
                                                               'Soybean at '
                                                               'peak maturity.',
                                                       'why': 'Harvesting at '
                                                              'the right time '
                                                              'maximizes '
                                                              'nutritional '
                                                              'value and '
                                                              'market '
                                                              'shelf-life.'}],
                                      'challenges': [   {   'issue': 'Local '
                                                                     'pests '
                                                                     'and '
                                                                     'insects',
                                                            'solution': 'Regularly '
                                                                        'scout '
                                                                        'the '
                                                                        'field '
                                                                        'and '
                                                                        'use '
                                                                        'integrated '
                                                                        'pest '
                                                                        'management '
                                                                        '(IPM) '
                                                                        'techniques '
                                                                        'like '
                                                                        'neem '
                                                                        'oil.'},
                                                        {   'issue': 'Unpredictable '
                                                                     'weather '
                                                                     'patterns',
                                                            'solution': 'Ensure '
                                                                        'good '
                                                                        'drainage '
                                                                        'to '
                                                                        'prevent '
                                                                        'waterlogging, '
                                                                        'and '
                                                                        'mulch '
                                                                        'the '
                                                                        'soil '
                                                                        'to '
                                                                        'retain '
                                                                        'moisture '
                                                                        'during '
                                                                        'droughts.'},
                                                        {   'issue': 'Weed '
                                                                     'competition',
                                                            'solution': 'Perform '
                                                                        'manual '
                                                                        'weeding '
                                                                        'during '
                                                                        'the '
                                                                        'first '
                                                                        '30-45 '
                                                                        'days, '
                                                                        'which '
                                                                        'is '
                                                                        'the '
                                                                        'critical '
                                                                        'weed-free '
                                                                        'period.'}],
                                      'soil_tips': 'Use organic compost and '
                                                   'practice crop rotation to '
                                                   'maintain soil health and '
                                                   'microbiome diversity.'}},
    'Turmeric': {   'name_en': 'Turmeric',
                    'name_hi': 'Turmeric / हल्दी',
                    'season': 'Kharif',
                    'regions': ['East', 'South', 'West'],
                    'ph': (5.5, 7.5),
                    'moisture': (60, 80),
                    'ec': (0, 1.5),
                    'n': (100, 200),
                    'p': (15, 30),
                    'k': (150, 300),
                    'soils': ['Alluvial Soil (Fertile)', 'Laterite Soil'],
                    'water_needs': 'Medium',
                    'crop_type': 'Spice',
                    'sowing_months': ['May', 'Jun'],
                    'harvest_months': ['Jan', 'Feb', 'Mar'],
                    'farm_school': {   'steps': [   {   'title': 'Seed/Land '
                                                                 'Prep',
                                                        'desc': 'Prepare the '
                                                                'land '
                                                                'specifically '
                                                                'for Turmeric.',
                                                        'why': 'Proper land '
                                                               'preparation '
                                                               'provides '
                                                               'aeration to '
                                                               'the roots and '
                                                               'kills early '
                                                               'weeds.'},
                                                    {   'title': 'Sowing & '
                                                                 'Care',
                                                        'desc': 'Sow the seeds '
                                                                'at the '
                                                                'correct depth '
                                                                'and spacing.',
                                                        'why': 'Optimal '
                                                               'spacing '
                                                               'prevents '
                                                               'plants from '
                                                               'competing with '
                                                               'each other for '
                                                               'sunlight and '
                                                               'nutrients.'},
                                                    {   'title': 'Irrigation',
                                                        'desc': 'Water at '
                                                                'critical '
                                                                'growth '
                                                                'stages.',
                                                        'why': 'Water acts as '
                                                               'the transport '
                                                               'system '
                                                               'carrying soil '
                                                               'nutrients up '
                                                               'into the plant '
                                                               'tissues.'},
                                                    {   'title': 'Harvesting',
                                                        'desc': 'Harvest '
                                                                'Turmeric at '
                                                                'peak '
                                                                'maturity.',
                                                        'why': 'Harvesting at '
                                                               'the right time '
                                                               'maximizes '
                                                               'nutritional '
                                                               'value and '
                                                               'market '
                                                               'shelf-life.'}],
                                       'challenges': [   {   'issue': 'Local '
                                                                      'pests '
                                                                      'and '
                                                                      'insects',
                                                             'solution': 'Regularly '
                                                                         'scout '
                                                                         'the '
                                                                         'field '
                                                                         'and '
                                                                         'use '
                                                                         'integrated '
                                                                         'pest '
                                                                         'management '
                                                                         '(IPM) '
                                                                         'techniques '
                                                                         'like '
                                                                         'neem '
                                                                         'oil.'},
                                                         {   'issue': 'Unpredictable '
                                                                      'weather '
                                                                      'patterns',
                                                             'solution': 'Ensure '
                                                                         'good '
                                                                         'drainage '
                                                                         'to '
                                                                         'prevent '
                                                                         'waterlogging, '
                                                                         'and '
                                                                         'mulch '
                                                                         'the '
                                                                         'soil '
                                                                         'to '
                                                                         'retain '
                                                                         'moisture '
                                                                         'during '
                                                                         'droughts.'},
                                                         {   'issue': 'Weed '
                                                                      'competition',
                                                             'solution': 'Perform '
                                                                         'manual '
                                                                         'weeding '
                                                                         'during '
                                                                         'the '
                                                                         'first '
                                                                         '30-45 '
                                                                         'days, '
                                                                         'which '
                                                                         'is '
                                                                         'the '
                                                                         'critical '
                                                                         'weed-free '
                                                                         'period.'}],
                                       'soil_tips': 'Use organic compost and '
                                                    'practice crop rotation to '
                                                    'maintain soil health and '
                                                    'microbiome diversity.'}},
    'Cumin': {   'name_en': 'Cumin / Jeera',
                 'name_hi': 'Cumin / जीरा',
                 'season': 'Rabi',
                 'regions': ['North', 'West'],
                 'ph': (6.5, 8.0),
                 'moisture': (20, 40),
                 'ec': (0, 2.0),
                 'n': (60, 120),
                 'p': (10, 25),
                 'k': (80, 150),
                 'soils': ['Arid / Desert Soil', 'Red & Yellow Soil'],
                 'water_needs': 'Low',
                 'crop_type': 'Spice',
                 'sowing_months': ['Nov', 'Dec'],
                 'harvest_months': ['Feb', 'Mar'],
                 'farm_school': {   'steps': [   {   'title': 'Seed/Land Prep',
                                                     'desc': 'Prepare the land '
                                                             'specifically for '
                                                             'Cumin.',
                                                     'why': 'Proper land '
                                                            'preparation '
                                                            'provides aeration '
                                                            'to the roots and '
                                                            'kills early '
                                                            'weeds.'},
                                                 {   'title': 'Sowing & Care',
                                                     'desc': 'Sow the seeds at '
                                                             'the correct '
                                                             'depth and '
                                                             'spacing.',
                                                     'why': 'Optimal spacing '
                                                            'prevents plants '
                                                            'from competing '
                                                            'with each other '
                                                            'for sunlight and '
                                                            'nutrients.'},
                                                 {   'title': 'Irrigation',
                                                     'desc': 'Water at '
                                                             'critical growth '
                                                             'stages.',
                                                     'why': 'Water acts as the '
                                                            'transport system '
                                                            'carrying soil '
                                                            'nutrients up into '
                                                            'the plant '
                                                            'tissues.'},
                                                 {   'title': 'Harvesting',
                                                     'desc': 'Harvest Cumin at '
                                                             'peak maturity.',
                                                     'why': 'Harvesting at the '
                                                            'right time '
                                                            'maximizes '
                                                            'nutritional value '
                                                            'and market '
                                                            'shelf-life.'}],
                                    'challenges': [   {   'issue': 'Local '
                                                                   'pests and '
                                                                   'insects',
                                                          'solution': 'Regularly '
                                                                      'scout '
                                                                      'the '
                                                                      'field '
                                                                      'and use '
                                                                      'integrated '
                                                                      'pest '
                                                                      'management '
                                                                      '(IPM) '
                                                                      'techniques '
                                                                      'like '
                                                                      'neem '
                                                                      'oil.'},
                                                      {   'issue': 'Unpredictable '
                                                                   'weather '
                                                                   'patterns',
                                                          'solution': 'Ensure '
                                                                      'good '
                                                                      'drainage '
                                                                      'to '
                                                                      'prevent '
                                                                      'waterlogging, '
                                                                      'and '
                                                                      'mulch '
                                                                      'the '
                                                                      'soil to '
                                                                      'retain '
                                                                      'moisture '
                                                                      'during '
                                                                      'droughts.'},
                                                      {   'issue': 'Weed '
                                                                   'competition',
                                                          'solution': 'Perform '
                                                                      'manual '
                                                                      'weeding '
                                                                      'during '
                                                                      'the '
                                                                      'first '
                                                                      '30-45 '
                                                                      'days, '
                                                                      'which '
                                                                      'is the '
                                                                      'critical '
                                                                      'weed-free '
                                                                      'period.'}],
                                    'soil_tips': 'Use organic compost and '
                                                 'practice crop rotation to '
                                                 'maintain soil health and '
                                                 'microbiome diversity.'}},
    'Coriander': {   'name_en': 'Coriander',
                     'name_hi': 'Coriander / धनिया',
                     'season': 'Rabi',
                     'regions': ['North', 'West'],
                     'ph': (6.0, 7.5),
                     'moisture': (30, 50),
                     'ec': (0, 2.0),
                     'n': (80, 150),
                     'p': (15, 30),
                     'k': (100, 200),
                     'soils': ['Black Soil (Regur)', 'Red & Yellow Soil'],
                     'water_needs': 'Medium',
                     'crop_type': 'Spice',
                     'sowing_months': ['Oct', 'Nov'],
                     'harvest_months': ['Feb', 'Mar'],
                     'farm_school': {   'steps': [   {   'title': 'Seed/Land '
                                                                  'Prep',
                                                         'desc': 'Prepare the '
                                                                 'land '
                                                                 'specifically '
                                                                 'for '
                                                                 'Coriander.',
                                                         'why': 'Proper land '
                                                                'preparation '
                                                                'provides '
                                                                'aeration to '
                                                                'the roots and '
                                                                'kills early '
                                                                'weeds.'},
                                                     {   'title': 'Sowing & '
                                                                  'Care',
                                                         'desc': 'Sow the '
                                                                 'seeds at the '
                                                                 'correct '
                                                                 'depth and '
                                                                 'spacing.',
                                                         'why': 'Optimal '
                                                                'spacing '
                                                                'prevents '
                                                                'plants from '
                                                                'competing '
                                                                'with each '
                                                                'other for '
                                                                'sunlight and '
                                                                'nutrients.'},
                                                     {   'title': 'Irrigation',
                                                         'desc': 'Water at '
                                                                 'critical '
                                                                 'growth '
                                                                 'stages.',
                                                         'why': 'Water acts as '
                                                                'the transport '
                                                                'system '
                                                                'carrying soil '
                                                                'nutrients up '
                                                                'into the '
                                                                'plant '
                                                                'tissues.'},
                                                     {   'title': 'Harvesting',
                                                         'desc': 'Harvest '
                                                                 'Coriander at '
                                                                 'peak '
                                                                 'maturity.',
                                                         'why': 'Harvesting at '
                                                                'the right '
                                                                'time '
                                                                'maximizes '
                                                                'nutritional '
                                                                'value and '
                                                                'market '
                                                                'shelf-life.'}],
                                        'challenges': [   {   'issue': 'Local '
                                                                       'pests '
                                                                       'and '
                                                                       'insects',
                                                              'solution': 'Regularly '
                                                                          'scout '
                                                                          'the '
                                                                          'field '
                                                                          'and '
                                                                          'use '
                                                                          'integrated '
                                                                          'pest '
                                                                          'management '
                                                                          '(IPM) '
                                                                          'techniques '
                                                                          'like '
                                                                          'neem '
                                                                          'oil.'},
                                                          {   'issue': 'Unpredictable '
                                                                       'weather '
                                                                       'patterns',
                                                              'solution': 'Ensure '
                                                                          'good '
                                                                          'drainage '
                                                                          'to '
                                                                          'prevent '
                                                                          'waterlogging, '
                                                                          'and '
                                                                          'mulch '
                                                                          'the '
                                                                          'soil '
                                                                          'to '
                                                                          'retain '
                                                                          'moisture '
                                                                          'during '
                                                                          'droughts.'},
                                                          {   'issue': 'Weed '
                                                                       'competition',
                                                              'solution': 'Perform '
                                                                          'manual '
                                                                          'weeding '
                                                                          'during '
                                                                          'the '
                                                                          'first '
                                                                          '30-45 '
                                                                          'days, '
                                                                          'which '
                                                                          'is '
                                                                          'the '
                                                                          'critical '
                                                                          'weed-free '
                                                                          'period.'}],
                                        'soil_tips': 'Use organic compost and '
                                                     'practice crop rotation '
                                                     'to maintain soil health '
                                                     'and microbiome '
                                                     'diversity.'}},
    'Cardamom': {   'name_en': 'Cardamom',
                    'name_hi': 'Cardamom / इलायची',
                    'season': 'Kharif',
                    'regions': ['East', 'South'],
                    'ph': (5.5, 6.5),
                    'moisture': (70, 95),
                    'ec': (0, 1.0),
                    'n': (100, 200),
                    'p': (10, 25),
                    'k': (150, 300),
                    'soils': ['Forest/Mountain Soil', 'Laterite Soil'],
                    'water_needs': 'High',
                    'crop_type': 'Spice',
                    'sowing_months': ['Jun', 'Jul'],
                    'harvest_months': ['Aug', 'Sep', 'Oct'],
                    'farm_school': {   'steps': [   {   'title': 'Seed/Land '
                                                                 'Prep',
                                                        'desc': 'Prepare the '
                                                                'land '
                                                                'specifically '
                                                                'for Cardamom.',
                                                        'why': 'Proper land '
                                                               'preparation '
                                                               'provides '
                                                               'aeration to '
                                                               'the roots and '
                                                               'kills early '
                                                               'weeds.'},
                                                    {   'title': 'Sowing & '
                                                                 'Care',
                                                        'desc': 'Sow the seeds '
                                                                'at the '
                                                                'correct depth '
                                                                'and spacing.',
                                                        'why': 'Optimal '
                                                               'spacing '
                                                               'prevents '
                                                               'plants from '
                                                               'competing with '
                                                               'each other for '
                                                               'sunlight and '
                                                               'nutrients.'},
                                                    {   'title': 'Irrigation',
                                                        'desc': 'Water at '
                                                                'critical '
                                                                'growth '
                                                                'stages.',
                                                        'why': 'Water acts as '
                                                               'the transport '
                                                               'system '
                                                               'carrying soil '
                                                               'nutrients up '
                                                               'into the plant '
                                                               'tissues.'},
                                                    {   'title': 'Harvesting',
                                                        'desc': 'Harvest '
                                                                'Cardamom at '
                                                                'peak '
                                                                'maturity.',
                                                        'why': 'Harvesting at '
                                                               'the right time '
                                                               'maximizes '
                                                               'nutritional '
                                                               'value and '
                                                               'market '
                                                               'shelf-life.'}],
                                       'challenges': [   {   'issue': 'Local '
                                                                      'pests '
                                                                      'and '
                                                                      'insects',
                                                             'solution': 'Regularly '
                                                                         'scout '
                                                                         'the '
                                                                         'field '
                                                                         'and '
                                                                         'use '
                                                                         'integrated '
                                                                         'pest '
                                                                         'management '
                                                                         '(IPM) '
                                                                         'techniques '
                                                                         'like '
                                                                         'neem '
                                                                         'oil.'},
                                                         {   'issue': 'Unpredictable '
                                                                      'weather '
                                                                      'patterns',
                                                             'solution': 'Ensure '
                                                                         'good '
                                                                         'drainage '
                                                                         'to '
                                                                         'prevent '
                                                                         'waterlogging, '
                                                                         'and '
                                                                         'mulch '
                                                                         'the '
                                                                         'soil '
                                                                         'to '
                                                                         'retain '
                                                                         'moisture '
                                                                         'during '
                                                                         'droughts.'},
                                                         {   'issue': 'Weed '
                                                                      'competition',
                                                             'solution': 'Perform '
                                                                         'manual '
                                                                         'weeding '
                                                                         'during '
                                                                         'the '
                                                                         'first '
                                                                         '30-45 '
                                                                         'days, '
                                                                         'which '
                                                                         'is '
                                                                         'the '
                                                                         'critical '
                                                                         'weed-free '
                                                                         'period.'}],
                                       'soil_tips': 'Use organic compost and '
                                                    'practice crop rotation to '
                                                    'maintain soil health and '
                                                    'microbiome diversity.'}},
    'BlackPepper': {   'name_en': 'Black Pepper',
                       'name_hi': 'Black Pepper / काली मिर्च',
                       'season': 'Kharif',
                       'regions': ['South'],
                       'ph': (5.5, 6.5),
                       'moisture': (70, 90),
                       'ec': (0, 1.0),
                       'n': (120, 250),
                       'p': (15, 30),
                       'k': (150, 300),
                       'soils': ['Forest/Mountain Soil', 'Laterite Soil'],
                       'water_needs': 'High',
                       'crop_type': 'Spice',
                       'sowing_months': ['Jun', 'Jul'],
                       'harvest_months': ['Dec', 'Jan'],
                       'farm_school': {   'steps': [   {   'title': 'Seed/Land '
                                                                    'Prep',
                                                           'desc': 'Prepare '
                                                                   'the land '
                                                                   'specifically '
                                                                   'for '
                                                                   'BlackPepper.',
                                                           'why': 'Proper land '
                                                                  'preparation '
                                                                  'provides '
                                                                  'aeration to '
                                                                  'the roots '
                                                                  'and kills '
                                                                  'early '
                                                                  'weeds.'},
                                                       {   'title': 'Sowing & '
                                                                    'Care',
                                                           'desc': 'Sow the '
                                                                   'seeds at '
                                                                   'the '
                                                                   'correct '
                                                                   'depth and '
                                                                   'spacing.',
                                                           'why': 'Optimal '
                                                                  'spacing '
                                                                  'prevents '
                                                                  'plants from '
                                                                  'competing '
                                                                  'with each '
                                                                  'other for '
                                                                  'sunlight '
                                                                  'and '
                                                                  'nutrients.'},
                                                       {   'title': 'Irrigation',
                                                           'desc': 'Water at '
                                                                   'critical '
                                                                   'growth '
                                                                   'stages.',
                                                           'why': 'Water acts '
                                                                  'as the '
                                                                  'transport '
                                                                  'system '
                                                                  'carrying '
                                                                  'soil '
                                                                  'nutrients '
                                                                  'up into the '
                                                                  'plant '
                                                                  'tissues.'},
                                                       {   'title': 'Harvesting',
                                                           'desc': 'Harvest '
                                                                   'BlackPepper '
                                                                   'at peak '
                                                                   'maturity.',
                                                           'why': 'Harvesting '
                                                                  'at the '
                                                                  'right time '
                                                                  'maximizes '
                                                                  'nutritional '
                                                                  'value and '
                                                                  'market '
                                                                  'shelf-life.'}],
                                          'challenges': [   {   'issue': 'Local '
                                                                         'pests '
                                                                         'and '
                                                                         'insects',
                                                                'solution': 'Regularly '
                                                                            'scout '
                                                                            'the '
                                                                            'field '
                                                                            'and '
                                                                            'use '
                                                                            'integrated '
                                                                            'pest '
                                                                            'management '
                                                                            '(IPM) '
                                                                            'techniques '
                                                                            'like '
                                                                            'neem '
                                                                            'oil.'},
                                                            {   'issue': 'Unpredictable '
                                                                         'weather '
                                                                         'patterns',
                                                                'solution': 'Ensure '
                                                                            'good '
                                                                            'drainage '
                                                                            'to '
                                                                            'prevent '
                                                                            'waterlogging, '
                                                                            'and '
                                                                            'mulch '
                                                                            'the '
                                                                            'soil '
                                                                            'to '
                                                                            'retain '
                                                                            'moisture '
                                                                            'during '
                                                                            'droughts.'},
                                                            {   'issue': 'Weed '
                                                                         'competition',
                                                                'solution': 'Perform '
                                                                            'manual '
                                                                            'weeding '
                                                                            'during '
                                                                            'the '
                                                                            'first '
                                                                            '30-45 '
                                                                            'days, '
                                                                            'which '
                                                                            'is '
                                                                            'the '
                                                                            'critical '
                                                                            'weed-free '
                                                                            'period.'}],
                                          'soil_tips': 'Use organic compost '
                                                       'and practice crop '
                                                       'rotation to maintain '
                                                       'soil health and '
                                                       'microbiome '
                                                       'diversity.'}},
    'Coconut': {   'name_en': 'Coconut',
                   'name_hi': 'Coconut / नारियल',
                   'season': 'Zaid',
                   'regions': ['East', 'South', 'West'],
                   'ph': (5.5, 8.0),
                   'moisture': (60, 85),
                   'ec': (0, 4.0),
                   'n': (100, 250),
                   'p': (10, 30),
                   'k': (200, 400),
                   'soils': ['Coastal Sandy Soil', 'Laterite Soil'],
                   'water_needs': 'Medium',
                   'crop_type': 'Plantation',
                   'sowing_months': ['May', 'Jun'],
                   'harvest_months': [   'Jan',
                                         'Feb',
                                         'Mar',
                                         'Apr',
                                         'May',
                                         'Jun',
                                         'Jul',
                                         'Aug',
                                         'Sep',
                                         'Oct',
                                         'Nov',
                                         'Dec'],
                   'farm_school': {   'steps': [   {   'title': 'Seed/Land '
                                                                'Prep',
                                                       'desc': 'Prepare the '
                                                               'land '
                                                               'specifically '
                                                               'for Coconut.',
                                                       'why': 'Proper land '
                                                              'preparation '
                                                              'provides '
                                                              'aeration to the '
                                                              'roots and kills '
                                                              'early weeds.'},
                                                   {   'title': 'Sowing & Care',
                                                       'desc': 'Sow the seeds '
                                                               'at the correct '
                                                               'depth and '
                                                               'spacing.',
                                                       'why': 'Optimal spacing '
                                                              'prevents plants '
                                                              'from competing '
                                                              'with each other '
                                                              'for sunlight '
                                                              'and nutrients.'},
                                                   {   'title': 'Irrigation',
                                                       'desc': 'Water at '
                                                               'critical '
                                                               'growth stages.',
                                                       'why': 'Water acts as '
                                                              'the transport '
                                                              'system carrying '
                                                              'soil nutrients '
                                                              'up into the '
                                                              'plant tissues.'},
                                                   {   'title': 'Harvesting',
                                                       'desc': 'Harvest '
                                                               'Coconut at '
                                                               'peak maturity.',
                                                       'why': 'Harvesting at '
                                                              'the right time '
                                                              'maximizes '
                                                              'nutritional '
                                                              'value and '
                                                              'market '
                                                              'shelf-life.'}],
                                      'challenges': [   {   'issue': 'Local '
                                                                     'pests '
                                                                     'and '
                                                                     'insects',
                                                            'solution': 'Regularly '
                                                                        'scout '
                                                                        'the '
                                                                        'field '
                                                                        'and '
                                                                        'use '
                                                                        'integrated '
                                                                        'pest '
                                                                        'management '
                                                                        '(IPM) '
                                                                        'techniques '
                                                                        'like '
                                                                        'neem '
                                                                        'oil.'},
                                                        {   'issue': 'Unpredictable '
                                                                     'weather '
                                                                     'patterns',
                                                            'solution': 'Ensure '
                                                                        'good '
                                                                        'drainage '
                                                                        'to '
                                                                        'prevent '
                                                                        'waterlogging, '
                                                                        'and '
                                                                        'mulch '
                                                                        'the '
                                                                        'soil '
                                                                        'to '
                                                                        'retain '
                                                                        'moisture '
                                                                        'during '
                                                                        'droughts.'},
                                                        {   'issue': 'Weed '
                                                                     'competition',
                                                            'solution': 'Perform '
                                                                        'manual '
                                                                        'weeding '
                                                                        'during '
                                                                        'the '
                                                                        'first '
                                                                        '30-45 '
                                                                        'days, '
                                                                        'which '
                                                                        'is '
                                                                        'the '
                                                                        'critical '
                                                                        'weed-free '
                                                                        'period.'}],
                                      'soil_tips': 'Use organic compost and '
                                                   'practice crop rotation to '
                                                   'maintain soil health and '
                                                   'microbiome diversity.'}},
    'Bajra': {   'name_en': 'Bajra / Pearl Millet',
                 'name_hi': 'Bajra / बाजरा',
                 'season': 'Kharif',
                 'regions': ['North', 'South', 'West'],
                 'ph': (5.5, 8.0),
                 'moisture': (20, 40),
                 'ec': (0, 3.0),
                 'n': (60, 120),
                 'p': (10, 25),
                 'k': (80, 150),
                 'soils': [   'Arid / Desert Soil',
                              'Red & Yellow Soil',
                              'Coastal Sandy Soil'],
                 'water_needs': 'Low',
                 'crop_type': 'Cereal',
                 'sowing_months': ['Jun', 'Jul'],
                 'harvest_months': ['Sep', 'Oct'],
                 'farm_school': {   'steps': [   {   'title': 'Seed/Land Prep',
                                                     'desc': 'Prepare the land '
                                                             'specifically for '
                                                             'Bajra.',
                                                     'why': 'Proper land '
                                                            'preparation '
                                                            'provides aeration '
                                                            'to the roots and '
                                                            'kills early '
                                                            'weeds.'},
                                                 {   'title': 'Sowing & Care',
                                                     'desc': 'Sow the seeds at '
                                                             'the correct '
                                                             'depth and '
                                                             'spacing.',
                                                     'why': 'Optimal spacing '
                                                            'prevents plants '
                                                            'from competing '
                                                            'with each other '
                                                            'for sunlight and '
                                                            'nutrients.'},
                                                 {   'title': 'Irrigation',
                                                     'desc': 'Water at '
                                                             'critical growth '
                                                             'stages.',
                                                     'why': 'Water acts as the '
                                                            'transport system '
                                                            'carrying soil '
                                                            'nutrients up into '
                                                            'the plant '
                                                            'tissues.'},
                                                 {   'title': 'Harvesting',
                                                     'desc': 'Harvest Bajra at '
                                                             'peak maturity.',
                                                     'why': 'Harvesting at the '
                                                            'right time '
                                                            'maximizes '
                                                            'nutritional value '
                                                            'and market '
                                                            'shelf-life.'}],
                                    'challenges': [   {   'issue': 'Local '
                                                                   'pests and '
                                                                   'insects',
                                                          'solution': 'Regularly '
                                                                      'scout '
                                                                      'the '
                                                                      'field '
                                                                      'and use '
                                                                      'integrated '
                                                                      'pest '
                                                                      'management '
                                                                      '(IPM) '
                                                                      'techniques '
                                                                      'like '
                                                                      'neem '
                                                                      'oil.'},
                                                      {   'issue': 'Unpredictable '
                                                                   'weather '
                                                                   'patterns',
                                                          'solution': 'Ensure '
                                                                      'good '
                                                                      'drainage '
                                                                      'to '
                                                                      'prevent '
                                                                      'waterlogging, '
                                                                      'and '
                                                                      'mulch '
                                                                      'the '
                                                                      'soil to '
                                                                      'retain '
                                                                      'moisture '
                                                                      'during '
                                                                      'droughts.'},
                                                      {   'issue': 'Weed '
                                                                   'competition',
                                                          'solution': 'Perform '
                                                                      'manual '
                                                                      'weeding '
                                                                      'during '
                                                                      'the '
                                                                      'first '
                                                                      '30-45 '
                                                                      'days, '
                                                                      'which '
                                                                      'is the '
                                                                      'critical '
                                                                      'weed-free '
                                                                      'period.'}],
                                    'soil_tips': 'Use organic compost and '
                                                 'practice crop rotation to '
                                                 'maintain soil health and '
                                                 'microbiome diversity.'}},
    'Jowar': {   'name_en': 'Jowar / Sorghum',
                 'name_hi': 'Jowar / ज्वार',
                 'season': 'Kharif',
                 'regions': ['North', 'South', 'West'],
                 'ph': (6.0, 8.0),
                 'moisture': (30, 50),
                 'ec': (0, 2.5),
                 'n': (80, 150),
                 'p': (12, 30),
                 'k': (100, 200),
                 'soils': ['Black Soil (Regur)', 'Red & Yellow Soil'],
                 'water_needs': 'Low',
                 'crop_type': 'Cereal',
                 'sowing_months': ['Jun', 'Jul'],
                 'harvest_months': ['Oct', 'Nov'],
                 'farm_school': {   'steps': [   {   'title': 'Seed/Land Prep',
                                                     'desc': 'Prepare the land '
                                                             'specifically for '
                                                             'Jowar.',
                                                     'why': 'Proper land '
                                                            'preparation '
                                                            'provides aeration '
                                                            'to the roots and '
                                                            'kills early '
                                                            'weeds.'},
                                                 {   'title': 'Sowing & Care',
                                                     'desc': 'Sow the seeds at '
                                                             'the correct '
                                                             'depth and '
                                                             'spacing.',
                                                     'why': 'Optimal spacing '
                                                            'prevents plants '
                                                            'from competing '
                                                            'with each other '
                                                            'for sunlight and '
                                                            'nutrients.'},
                                                 {   'title': 'Irrigation',
                                                     'desc': 'Water at '
                                                             'critical growth '
                                                             'stages.',
                                                     'why': 'Water acts as the '
                                                            'transport system '
                                                            'carrying soil '
                                                            'nutrients up into '
                                                            'the plant '
                                                            'tissues.'},
                                                 {   'title': 'Harvesting',
                                                     'desc': 'Harvest Jowar at '
                                                             'peak maturity.',
                                                     'why': 'Harvesting at the '
                                                            'right time '
                                                            'maximizes '
                                                            'nutritional value '
                                                            'and market '
                                                            'shelf-life.'}],
                                    'challenges': [   {   'issue': 'Local '
                                                                   'pests and '
                                                                   'insects',
                                                          'solution': 'Regularly '
                                                                      'scout '
                                                                      'the '
                                                                      'field '
                                                                      'and use '
                                                                      'integrated '
                                                                      'pest '
                                                                      'management '
                                                                      '(IPM) '
                                                                      'techniques '
                                                                      'like '
                                                                      'neem '
                                                                      'oil.'},
                                                      {   'issue': 'Unpredictable '
                                                                   'weather '
                                                                   'patterns',
                                                          'solution': 'Ensure '
                                                                      'good '
                                                                      'drainage '
                                                                      'to '
                                                                      'prevent '
                                                                      'waterlogging, '
                                                                      'and '
                                                                      'mulch '
                                                                      'the '
                                                                      'soil to '
                                                                      'retain '
                                                                      'moisture '
                                                                      'during '
                                                                      'droughts.'},
                                                      {   'issue': 'Weed '
                                                                   'competition',
                                                          'solution': 'Perform '
                                                                      'manual '
                                                                      'weeding '
                                                                      'during '
                                                                      'the '
                                                                      'first '
                                                                      '30-45 '
                                                                      'days, '
                                                                      'which '
                                                                      'is the '
                                                                      'critical '
                                                                      'weed-free '
                                                                      'period.'}],
                                    'soil_tips': 'Use organic compost and '
                                                 'practice crop rotation to '
                                                 'maintain soil health and '
                                                 'microbiome diversity.'}},
    'Gram': {   'name_en': 'Gram / Chickpea',
                'name_hi': 'Gram / चना',
                'season': 'Rabi',
                'regions': ['East', 'North', 'South', 'West'],
                'ph': (6.0, 7.5),
                'moisture': (30, 50),
                'ec': (0, 2.0),
                'n': (60, 120),
                'p': (15, 35),
                'k': (80, 160),
                'soils': [   'Alluvial Soil (Fertile)',
                             'Black Soil (Regur)',
                             'Red & Yellow Soil'],
                'water_needs': 'Low',
                'crop_type': 'Pulse',
                'sowing_months': ['Oct', 'Nov'],
                'harvest_months': ['Feb', 'Mar'],
                'farm_school': {   'steps': [   {   'title': 'Seed/Land Prep',
                                                    'desc': 'Prepare the land '
                                                            'specifically for '
                                                            'Gram.',
                                                    'why': 'Proper land '
                                                           'preparation '
                                                           'provides aeration '
                                                           'to the roots and '
                                                           'kills early '
                                                           'weeds.'},
                                                {   'title': 'Sowing & Care',
                                                    'desc': 'Sow the seeds at '
                                                            'the correct depth '
                                                            'and spacing.',
                                                    'why': 'Optimal spacing '
                                                           'prevents plants '
                                                           'from competing '
                                                           'with each other '
                                                           'for sunlight and '
                                                           'nutrients.'},
                                                {   'title': 'Irrigation',
                                                    'desc': 'Water at critical '
                                                            'growth stages.',
                                                    'why': 'Water acts as the '
                                                           'transport system '
                                                           'carrying soil '
                                                           'nutrients up into '
                                                           'the plant '
                                                           'tissues.'},
                                                {   'title': 'Harvesting',
                                                    'desc': 'Harvest Gram at '
                                                            'peak maturity.',
                                                    'why': 'Harvesting at the '
                                                           'right time '
                                                           'maximizes '
                                                           'nutritional value '
                                                           'and market '
                                                           'shelf-life.'}],
                                   'challenges': [   {   'issue': 'Local pests '
                                                                  'and insects',
                                                         'solution': 'Regularly '
                                                                     'scout '
                                                                     'the '
                                                                     'field '
                                                                     'and use '
                                                                     'integrated '
                                                                     'pest '
                                                                     'management '
                                                                     '(IPM) '
                                                                     'techniques '
                                                                     'like '
                                                                     'neem '
                                                                     'oil.'},
                                                     {   'issue': 'Unpredictable '
                                                                  'weather '
                                                                  'patterns',
                                                         'solution': 'Ensure '
                                                                     'good '
                                                                     'drainage '
                                                                     'to '
                                                                     'prevent '
                                                                     'waterlogging, '
                                                                     'and '
                                                                     'mulch '
                                                                     'the soil '
                                                                     'to '
                                                                     'retain '
                                                                     'moisture '
                                                                     'during '
                                                                     'droughts.'},
                                                     {   'issue': 'Weed '
                                                                  'competition',
                                                         'solution': 'Perform '
                                                                     'manual '
                                                                     'weeding '
                                                                     'during '
                                                                     'the '
                                                                     'first '
                                                                     '30-45 '
                                                                     'days, '
                                                                     'which is '
                                                                     'the '
                                                                     'critical '
                                                                     'weed-free '
                                                                     'period.'}],
                                   'soil_tips': 'Use organic compost and '
                                                'practice crop rotation to '
                                                'maintain soil health and '
                                                'microbiome diversity.'}},
    'Tur': {   'name_en': 'Tur / Pigeon Pea',
               'name_hi': 'Tur / अरहर',
               'season': 'Kharif',
               'regions': ['East', 'North', 'South', 'West'],
               'ph': (6.0, 7.5),
               'moisture': (40, 60),
               'ec': (0, 1.8),
               'n': (60, 120),
               'p': (15, 35),
               'k': (80, 160),
               'soils': [   'Black Soil (Regur)',
                            'Red & Yellow Soil',
                            'Alluvial Soil (Fertile)'],
               'water_needs': 'Medium',
               'crop_type': 'Pulse',
               'sowing_months': ['Jun', 'Jul'],
               'harvest_months': ['Dec', 'Jan'],
               'farm_school': {   'steps': [   {   'title': 'Seed/Land Prep',
                                                   'desc': 'Prepare the land '
                                                           'specifically for '
                                                           'Tur.',
                                                   'why': 'Proper land '
                                                          'preparation '
                                                          'provides aeration '
                                                          'to the roots and '
                                                          'kills early weeds.'},
                                               {   'title': 'Sowing & Care',
                                                   'desc': 'Sow the seeds at '
                                                           'the correct depth '
                                                           'and spacing.',
                                                   'why': 'Optimal spacing '
                                                          'prevents plants '
                                                          'from competing with '
                                                          'each other for '
                                                          'sunlight and '
                                                          'nutrients.'},
                                               {   'title': 'Irrigation',
                                                   'desc': 'Water at critical '
                                                           'growth stages.',
                                                   'why': 'Water acts as the '
                                                          'transport system '
                                                          'carrying soil '
                                                          'nutrients up into '
                                                          'the plant tissues.'},
                                               {   'title': 'Harvesting',
                                                   'desc': 'Harvest Tur at '
                                                           'peak maturity.',
                                                   'why': 'Harvesting at the '
                                                          'right time '
                                                          'maximizes '
                                                          'nutritional value '
                                                          'and market '
                                                          'shelf-life.'}],
                                  'challenges': [   {   'issue': 'Local pests '
                                                                 'and insects',
                                                        'solution': 'Regularly '
                                                                    'scout the '
                                                                    'field and '
                                                                    'use '
                                                                    'integrated '
                                                                    'pest '
                                                                    'management '
                                                                    '(IPM) '
                                                                    'techniques '
                                                                    'like neem '
                                                                    'oil.'},
                                                    {   'issue': 'Unpredictable '
                                                                 'weather '
                                                                 'patterns',
                                                        'solution': 'Ensure '
                                                                    'good '
                                                                    'drainage '
                                                                    'to '
                                                                    'prevent '
                                                                    'waterlogging, '
                                                                    'and mulch '
                                                                    'the soil '
                                                                    'to retain '
                                                                    'moisture '
                                                                    'during '
                                                                    'droughts.'},
                                                    {   'issue': 'Weed '
                                                                 'competition',
                                                        'solution': 'Perform '
                                                                    'manual '
                                                                    'weeding '
                                                                    'during '
                                                                    'the first '
                                                                    '30-45 '
                                                                    'days, '
                                                                    'which is '
                                                                    'the '
                                                                    'critical '
                                                                    'weed-free '
                                                                    'period.'}],
                                  'soil_tips': 'Use organic compost and '
                                               'practice crop rotation to '
                                               'maintain soil health and '
                                               'microbiome diversity.'}},
    'Onion': {   'name_en': 'Onion',
                 'name_hi': 'Onion / प्याज',
                 'season': 'Rabi',
                 'regions': ['North', 'South', 'West'],
                 'ph': (6.0, 7.5),
                 'moisture': (50, 70),
                 'ec': (0, 2.0),
                 'n': (100, 200),
                 'p': (20, 45),
                 'k': (120, 250),
                 'soils': ['Alluvial Soil (Fertile)', 'Black Soil (Regur)'],
                 'water_needs': 'Medium',
                 'crop_type': 'Vegetable',
                 'sowing_months': ['Oct', 'Nov'],
                 'harvest_months': ['Feb', 'Mar'],
                 'farm_school': {   'steps': [   {   'title': 'Seed/Land Prep',
                                                     'desc': 'Prepare the land '
                                                             'specifically for '
                                                             'Onion.',
                                                     'why': 'Proper land '
                                                            'preparation '
                                                            'provides aeration '
                                                            'to the roots and '
                                                            'kills early '
                                                            'weeds.'},
                                                 {   'title': 'Sowing & Care',
                                                     'desc': 'Sow the seeds at '
                                                             'the correct '
                                                             'depth and '
                                                             'spacing.',
                                                     'why': 'Optimal spacing '
                                                            'prevents plants '
                                                            'from competing '
                                                            'with each other '
                                                            'for sunlight and '
                                                            'nutrients.'},
                                                 {   'title': 'Irrigation',
                                                     'desc': 'Water at '
                                                             'critical growth '
                                                             'stages.',
                                                     'why': 'Water acts as the '
                                                            'transport system '
                                                            'carrying soil '
                                                            'nutrients up into '
                                                            'the plant '
                                                            'tissues.'},
                                                 {   'title': 'Harvesting',
                                                     'desc': 'Harvest Onion at '
                                                             'peak maturity.',
                                                     'why': 'Harvesting at the '
                                                            'right time '
                                                            'maximizes '
                                                            'nutritional value '
                                                            'and market '
                                                            'shelf-life.'}],
                                    'challenges': [   {   'issue': 'Local '
                                                                   'pests and '
                                                                   'insects',
                                                          'solution': 'Regularly '
                                                                      'scout '
                                                                      'the '
                                                                      'field '
                                                                      'and use '
                                                                      'integrated '
                                                                      'pest '
                                                                      'management '
                                                                      '(IPM) '
                                                                      'techniques '
                                                                      'like '
                                                                      'neem '
                                                                      'oil.'},
                                                      {   'issue': 'Unpredictable '
                                                                   'weather '
                                                                   'patterns',
                                                          'solution': 'Ensure '
                                                                      'good '
                                                                      'drainage '
                                                                      'to '
                                                                      'prevent '
                                                                      'waterlogging, '
                                                                      'and '
                                                                      'mulch '
                                                                      'the '
                                                                      'soil to '
                                                                      'retain '
                                                                      'moisture '
                                                                      'during '
                                                                      'droughts.'},
                                                      {   'issue': 'Weed '
                                                                   'competition',
                                                          'solution': 'Perform '
                                                                      'manual '
                                                                      'weeding '
                                                                      'during '
                                                                      'the '
                                                                      'first '
                                                                      '30-45 '
                                                                      'days, '
                                                                      'which '
                                                                      'is the '
                                                                      'critical '
                                                                      'weed-free '
                                                                      'period.'}],
                                    'soil_tips': 'Use organic compost and '
                                                 'practice crop rotation to '
                                                 'maintain soil health and '
                                                 'microbiome diversity.'}},
    'Tomato': {   'name_en': 'Tomato',
                  'name_hi': 'Tomato / टमाटर',
                  'season': 'Zaid',
                  'regions': ['East', 'North', 'South', 'West'],
                  'ph': (6.0, 7.0),
                  'moisture': (50, 75),
                  'ec': (0, 2.5),
                  'n': (120, 250),
                  'p': (20, 50),
                  'k': (150, 300),
                  'soils': [   'Alluvial Soil (Fertile)',
                               'Red & Yellow Soil',
                               'Black Soil (Regur)'],
                  'water_needs': 'Medium',
                  'crop_type': 'Vegetable',
                  'sowing_months': ['Jun', 'Jul', 'Jan', 'Feb'],
                  'harvest_months': ['Sep', 'Oct', 'Apr', 'May'],
                  'farm_school': {   'steps': [   {   'title': 'Seed/Land Prep',
                                                      'desc': 'Prepare the '
                                                              'land '
                                                              'specifically '
                                                              'for Tomato.',
                                                      'why': 'Proper land '
                                                             'preparation '
                                                             'provides '
                                                             'aeration to the '
                                                             'roots and kills '
                                                             'early weeds.'},
                                                  {   'title': 'Sowing & Care',
                                                      'desc': 'Sow the seeds '
                                                              'at the correct '
                                                              'depth and '
                                                              'spacing.',
                                                      'why': 'Optimal spacing '
                                                             'prevents plants '
                                                             'from competing '
                                                             'with each other '
                                                             'for sunlight and '
                                                             'nutrients.'},
                                                  {   'title': 'Irrigation',
                                                      'desc': 'Water at '
                                                              'critical growth '
                                                              'stages.',
                                                      'why': 'Water acts as '
                                                             'the transport '
                                                             'system carrying '
                                                             'soil nutrients '
                                                             'up into the '
                                                             'plant tissues.'},
                                                  {   'title': 'Harvesting',
                                                      'desc': 'Harvest Tomato '
                                                              'at peak '
                                                              'maturity.',
                                                      'why': 'Harvesting at '
                                                             'the right time '
                                                             'maximizes '
                                                             'nutritional '
                                                             'value and market '
                                                             'shelf-life.'}],
                                     'challenges': [   {   'issue': 'Local '
                                                                    'pests and '
                                                                    'insects',
                                                           'solution': 'Regularly '
                                                                       'scout '
                                                                       'the '
                                                                       'field '
                                                                       'and '
                                                                       'use '
                                                                       'integrated '
                                                                       'pest '
                                                                       'management '
                                                                       '(IPM) '
                                                                       'techniques '
                                                                       'like '
                                                                       'neem '
                                                                       'oil.'},
                                                       {   'issue': 'Unpredictable '
                                                                    'weather '
                                                                    'patterns',
                                                           'solution': 'Ensure '
                                                                       'good '
                                                                       'drainage '
                                                                       'to '
                                                                       'prevent '
                                                                       'waterlogging, '
                                                                       'and '
                                                                       'mulch '
                                                                       'the '
                                                                       'soil '
                                                                       'to '
                                                                       'retain '
                                                                       'moisture '
                                                                       'during '
                                                                       'droughts.'},
                                                       {   'issue': 'Weed '
                                                                    'competition',
                                                           'solution': 'Perform '
                                                                       'manual '
                                                                       'weeding '
                                                                       'during '
                                                                       'the '
                                                                       'first '
                                                                       '30-45 '
                                                                       'days, '
                                                                       'which '
                                                                       'is the '
                                                                       'critical '
                                                                       'weed-free '
                                                                       'period.'}],
                                     'soil_tips': 'Use organic compost and '
                                                  'practice crop rotation to '
                                                  'maintain soil health and '
                                                  'microbiome diversity.'}}}


# ==========================================
# 2D ARRAY: STATE -> SEASON -> CROPS
# ==========================================
STATE_SEASON_CROP_MAP = {}
for _s in STATE_TO_REGION.keys():
    STATE_SEASON_CROP_MAP[_s] = {"Kharif": [], "Rabi": [], "Zaid": []}
    _r = STATE_TO_REGION[_s]
    for _c, _p in crop_profiles.items():
        if _r in _p.get("regions", []):
            _szn = _p.get("season")
            if _szn in STATE_SEASON_CROP_MAP[_s]:
                STATE_SEASON_CROP_MAP[_s][_szn].append(_c)

def calculate_suitability(crop_name, soil_data, season, region, state=None, lang="en"):
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
    return score, profile

def detect_soil_profile(soil_data, state=None, lang="en"):
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
    return profile

def get_greeting(state, lang):
    greetings = {
        "Rajasthan": "Khamma Ghani",
        "Punjab": "Sat Sri Akal",
        "Haryana": "Ram Ram",
        "Uttar Pradesh": "Ram Ram",
        "Maharashtra": "Namaskar",
        "Tamil Nadu": "Vanakkam",
        "Gujarat": "Jai Shri Krishna",
        "West Bengal": "Nomoshkar",
        "Kerala": "Namaskaram",
        "Karnataka": "Namaskara",
        "Andhra Pradesh": "Namaskaram",
        "Telangana": "Namaskaram",
        "Odisha": "Jai Jagannath",
        "Assam": "Nomoskar",
        "Jharkhand": "Johar",
        "Chhattisgarh": "Johar",
        "Sikkim": "Tashi Delek",
        "Ladakh": "Julley",
        "Manipur": "Khurumjari",
        "Mizoram": "Chibai"
    }
    
    if lang == "hi":
        return "नमस्ते किसान भाई!"
    
    return f"{greetings.get(state, 'Namaste')}!"


@app.route("/")
def dashboard():
    """Serve the live dashboard data as JSON."""
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
    season = request.args.get("season", "Rabi")
    state = request.args.get("state", "Rajasthan")
    region = STATE_TO_REGION.get(state, "North")
    lang = request.args.get("lang", "en")
    
    # New Multi-Filters
    water_filter = request.args.get("water", "Any")
    type_filter = request.args.get("type", "Any")
    soil_override = request.args.get("soil", "Auto")
    phenomenon = request.args.get("phenomenon", "None")
        
    results = {}
    for crop, profile in crop_profiles.items():
        # HARD FILTERS: If these don't match, the crop is instantly rejected
        if profile.get("season") != season:
            continue
        if water_filter != "Any" and profile.get("water_needs") != water_filter:
            continue
        if type_filter != "Any" and profile.get("crop_type") != type_filter:
            continue
            
        score, details = calculate_suitability(crop, latest, season, region, state=state, lang=lang)
        
        penalty = 0
        
        # Region penalty
        if region not in profile.get("regions", []):
            penalty += 15
            
        # Moisture penalty
        if latest["moisture"] > 0: 
            if latest["moisture"] < profile["moisture"][0] or latest["moisture"] > profile["moisture"][1]: 
                penalty += 15
            
        # pH penalty
        if latest["ph"] < profile["ph"][0] or latest["ph"] > profile["ph"][1]:
            penalty += 15
            
        # NPK penalties
        if latest["n"] > 0 and latest["n"] < profile["n"][0]: penalty += 10
        if latest["p"] > 0 and latest["p"] < profile["p"][0]: penalty += 10
        if latest["k"] > 0 and latest["k"] < profile["k"][0]: penalty += 10
        
        # Soil Type Check (Override or Auto)
        if soil_override != "Auto":
            active_profile = soil_override
        else:
            active_profile = detect_soil_profile(latest, state=state, lang="en")
            
        if active_profile not in profile.get("soils", []):
            penalty += 40
            
        # Final Priority Score (100 is spot on perfect)
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

        
        details["score"] = max(10, final_score) 
        results[crop] = details
                
    return jsonify(results)


@app.route("/demo")
def demo():
    global latest
    profile = request.args.get("profile", "alluvial")
    if profile == "black":
        latest = {
            "n": 150, "p": 20, "k": 250,
            "moisture": 60, "ec": 1.2, "ph": 7.8,
            "temp": 28, "humidity": 65,
            "mq135": 180, "raining": False,
            "pump": False,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
    else:
        latest = {
            "n": 180, "p": 25, "k": 150,
            "moisture": 45, "ec": 0.8, "ph": 6.8,
            "temp": 31, "humidity": 60,
            "mq135": 210, "raining": False,
            "pump": False,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
    return jsonify({"status": "demo_data_loaded", "profile": profile, "data": latest})


# ─── API Endpoints for New Features ───────────────────
HISTORY_FILE = "yield_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/history", methods=["GET", "POST"])
def history_api():
    if request.method == "POST":
        data = request.json
        history = load_history()
        entry = {
            "id": int(time.time()),
            "crop": data.get("crop", "Unknown"),
            "season": data.get("season", "Kharif"),
            "year": data.get("year", "2026"),
            "yield_quintals": data.get("yield", 0),
            "notes": data.get("notes", "")
        }
        history.append(entry)
        save_history(history)
        return jsonify({"status": "success", "entry": entry})
    return jsonify(load_history())

@app.route("/crops")
def get_all_crops():
    return jsonify(crop_profiles)


# --- IoT Server State ---
iot_state = {
    "moisture": 45,
    "pump_status": False,
    "auto_irrigate": False
}

def irrigation_loop():
    while True:
        # Simulate natural drying over time
        if iot_state["moisture"] > 10 and not iot_state["pump_status"]:
            iot_state["moisture"] -= 1  # soil dries slowly
            
        # Auto-Irrigate logic
        if iot_state["auto_irrigate"]:
            if iot_state["moisture"] < 40 and not iot_state["pump_status"]:
                iot_state["pump_status"] = True
                
        # Pump physics
        if iot_state["pump_status"]:
            iot_state["moisture"] += 5  # pump adds water quickly
            if iot_state["moisture"] >= 75:
                # Reached optimal moisture, shut off pump
                iot_state["pump_status"] = False
                
        time.sleep(2)  # Backend loop runs every 2 seconds

# Start background thread
threading.Thread(target=irrigation_loop, daemon=True).start()

# Initialize ML Service
ml_service = CropDiseaseClassifier()

# --- Government Schemes Database ---
schemes_data = [
    {
        "id": "pm-kisan",
        "title": "PM-KISAN",
        "category": "Financial Aid",
        "description": "Pradhan Mantri Kisan Samman Nidhi provides income support of ₹6,000 per year to all landholding farmer families.",
        "link": "https://pmkisan.gov.in/"
    },
    {
        "id": "pmfby",
        "title": "Pradhan Mantri Fasal Bima Yojana",
        "category": "Insurance",
        "description": "Comprehensive crop insurance scheme providing financial support to farmers suffering crop loss/damage arising out of unforeseen events.",
        "link": "https://pmfby.gov.in/"
    },
    {
        "id": "pm-kusum",
        "title": "PM-KUSUM",
        "category": "Equipment",
        "description": "Subsidies for setting up standalone solar agriculture pumps to ensure energy security for farmers.",
        "link": "https://pmkusum.mnre.gov.in/"
    },
    {
        "id": "soil-health",
        "title": "Soil Health Card Scheme",
        "category": "Soil",
        "description": "Provides farmers with the nutrient status of their soil along with recommendations on appropriate dosage of nutrients.",
        "link": "https://soilhealth.dac.gov.in/"
    }
]

# --- New Endpoints ---

@app.route("/api/sensors", methods=["GET"])
def api_sensors():
    # Return real server state
    return jsonify({
        "moisture": iot_state["moisture"],
        "pump_status": iot_state["pump_status"],
        "auto_irrigate": iot_state["auto_irrigate"],
        "nitrogen": 120, # static or simulated
        "phosphorus": 45,
        "potassium": 210,
        "ph": 6.8
    })

@app.route("/api/irrigation/auto", methods=["POST"])
def toggle_auto_irrigate():
    data = request.json
    iot_state["auto_irrigate"] = data.get("auto_irrigate", False)
    # Turn off pump if auto is disabled and it was running
    if not iot_state["auto_irrigate"]:
         iot_state["pump_status"] = False
    return jsonify({"status": "success", "state": iot_state})

@app.route("/api/scan-image", methods=["POST"])
def scan_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    file = request.files['image']
    crop_name = request.form.get('crop', '')
    
    # Read bytes for the ML service
    image_bytes = file.read()
    
    # Run the solid stub ML pipeline
    prediction = ml_service.predict(image_bytes, crop_name)
    
    # Find the solution from crop_profiles or fallback to ML prediction
    solution = prediction.get("solution", "General care recommended. Consult an expert.")
    if crop_name and crop_name in crop_profiles:
        crop_data = crop_profiles[crop_name]
        challenges = crop_data.get("farm_school", {}).get("challenges", [])
        for c in challenges:
            if c.get("issue") == prediction["disease"]:
                solution = c.get("solution")
                break
                
    return jsonify({
        "disease": prediction["disease"],
        "confidence": prediction["confidence"],
        "solution": solution
    })

@app.route("/api/schemes", methods=["GET"])
def get_schemes():
    return jsonify(schemes_data)

# Crop rotation rules: after crop X, prefer crops Y
rotation_rules = {
    "Paddy": {"next": ["Wheat", "Gram", "Mustard"], "reason": "Paddy depletes nitrogen heavily. Follow with nitrogen-fixing pulses (Gram) or a Rabi cereal (Wheat) that thrives in the residual moisture."},
    "Wheat": {"next": ["Paddy", "Moong", "Soybean"], "reason": "Wheat leaves behind good stubble organic matter. Rotate with a Kharif legume (Moong/Soybean) to fix nitrogen, or Paddy for rice-wheat rotation."},
    "Cotton": {"next": ["Wheat", "Gram", "Sorghum"], "reason": "Cotton is exhausting for the soil. Follow with a Rabi pulse like Gram to restore nitrogen, or Wheat which has lower nutrient demands."},
    "Sugarcane": {"next": ["Paddy", "Moong", "Soybean"], "reason": "Sugarcane occupies the field for 12-18 months and depletes potassium. Follow with short-duration legumes to restore soil health quickly."},
    "Maize": {"next": ["Wheat", "Mustard", "Potato"], "reason": "Maize is a heavy nitrogen feeder. Rotate with Mustard or Wheat in Rabi to break pest cycles and balance nutrients."},
    "Soybean": {"next": ["Wheat", "Gram"], "reason": "Soybean fixes nitrogen in the soil. Take advantage of this enrichment by planting a nitrogen-hungry Rabi crop like Wheat."},
    "Mustard": {"next": ["Paddy", "Maize", "Cotton"], "reason": "Mustard breaks disease cycles for cereals. Follow with a Kharif cereal or cotton."},
    "Gram": {"next": ["Paddy", "Cotton", "Maize"], "reason": "Gram (chickpea) fixes nitrogen. Follow with nitrogen-hungry Kharif crops to utilize the enriched soil."},
    "Groundnut": {"next": ["Wheat", "Sorghum"], "reason": "Groundnut is a legume that enriches the soil. Follow with a cereal crop to exploit the nitrogen-enriched soil."},
    "Potato": {"next": ["Maize", "Paddy", "Soybean"], "reason": "Potato disturbs the soil structure. Follow with a cereal or legume to stabilize the soil."},
    "Mango": {"next": ["Mango"], "reason": "Mango is a perennial tree crop. Continue maintaining the orchard and grow intercrops like legumes between the rows."},
}

@app.route("/api/suggest-next", methods=["GET"])
def suggest_next_crop():
    history = load_history()
    
    if not history:
        return jsonify({"suggestions": [], "message": "No yield history found. Log your first crop yield to get personalized suggestions."})
    
    # Get the most recent crop grown
    last_entry = history[-1]
    last_crop = last_entry.get("crop", "").strip()
    last_season = last_entry.get("season", "")
    
    # Determine upcoming season based on current month
    month = datetime.now().month
    if 3 <= month <= 5:
        upcoming_season = "Kharif"
        season_months = "Jun - Oct"
    elif 6 <= month <= 9:
        upcoming_season = "Rabi"
        season_months = "Oct - Mar"
    else:
        upcoming_season = "Zaid"
        season_months = "Mar - Jun"
    
    suggestions = []
    
    # 1. Crop rotation based suggestion
    rotation = rotation_rules.get(last_crop, None)
    if rotation:
        for next_crop in rotation["next"]:
            if next_crop in crop_profiles:
                crop_data = crop_profiles[next_crop]
                # Check if it fits the upcoming season
                fits_season = (crop_data.get("season") == upcoming_season)
                suggestions.append({
                    "crop": next_crop,
                    "name": crop_data.get("name_en", next_crop),
                    "season": crop_data.get("season", "Unknown"),
                    "sowing_months": crop_data.get("sowing_months", []),
                    "fits_upcoming_season": fits_season,
                    "rotation_reason": rotation["reason"],
                    "source": "crop_rotation"
                })
    
    # 2. Also add seasonal suggestions that weren't already added
    for crop_key, crop_data in crop_profiles.items():
        if crop_data.get("season") == upcoming_season:
            already_suggested = any(s["crop"] == crop_key for s in suggestions)
            if not already_suggested:
                suggestions.append({
                    "crop": crop_key,
                    "name": crop_data.get("name_en", crop_key),
                    "season": crop_data.get("season"),
                    "sowing_months": crop_data.get("sowing_months", []),
                    "fits_upcoming_season": True,
                    "rotation_reason": None,
                    "source": "seasonal_match"
                })
    
    # Sort: rotation-based first, then seasonal
    suggestions.sort(key=lambda s: (0 if s["source"] == "crop_rotation" and s["fits_upcoming_season"] else 1 if s["source"] == "crop_rotation" else 2))
    
    # Count past crops from history for diversity analysis
    past_crops = [h.get("crop", "") for h in history]
    crop_counts = {}
    for c in past_crops:
        crop_counts[c] = crop_counts.get(c, 0) + 1
    
    return jsonify({
        "last_crop": last_crop,
        "last_season": last_season,
        "upcoming_season": upcoming_season,
        "upcoming_months": season_months,
        "suggestions": suggestions[:6],  # Top 6
        "history_analysis": {
            "total_records": len(history),
            "unique_crops": len(crop_counts),
            "crop_frequency": crop_counts,
            "diversity_warning": len(crop_counts) == 1 and len(history) > 2
        }
    })

# --- Crop Journey System ---
JOURNEY_FILE = "active_journey.json"

def load_journey():
    if os.path.exists(JOURNEY_FILE):
        with open(JOURNEY_FILE, "r") as f:
            return json.load(f)
    return None

def save_journey(journey):
    with open(JOURNEY_FILE, "w") as f:
        json.dump(journey, f, indent=2)

@app.route("/api/journey", methods=["GET"])
def get_journey():
    journey = load_journey()
    if not journey:
        return jsonify({"active": False, "message": "No active crop journey. Start one to get daily guidance!"})
    
    # Calculate current day
    from datetime import datetime
    start_date = datetime.strptime(journey["start_date"], "%Y-%m-%d")
    today = datetime.now()
    current_day = (today - start_date).days + 1
    
    crop = journey["crop"]
    soil_type = journey.get("soil_type", "Standard")
    journey_data = crop_journeys.get(crop, get_generic_journey(crop))
    total_days = journey_data["total_days"]
    
    # Soil specific logic dictionary
    soil_tips = {
        "Black": "Black clayey soil holds water well. Avoid over-irrigating to prevent root rot.",
        "Red": "Red sandy soil drains quickly. You may need to irrigate lightly but more frequently.",
        "Laterite": "Laterite is acidic. Ensure you use recommended lime if the crop requires neutral pH.",
        "Alluvial": "Alluvial soil is highly fertile. Standard irrigation and fertilizer practices apply."
    }
    
    # Find today's phase and tasks
    today_phase = None
    today_tasks = []
    upcoming_tasks = []
    completed_task_ids = journey.get("completed_tasks", [])
    
    for phase in journey_data["phases"]:
        for task in phase["tasks"]:
            task_id = f"{phase['name']}_{task['day']}"
            
            # Add dynamic soil advice if the task involves irrigation or fertilizer
            soil_advice = None
            task_text = f"{task['what']} {task['how']} {task['why']}".lower()
            if "irrigate" in task_text or "water" in task_text:
                if soil_type == "Black": soil_advice = "Since you have Black soil, ensure the field is not already waterlogged before this irrigation."
                if soil_type == "Red": soil_advice = "Since you have Red/Sandy soil, water drains fast. Check moisture deeply before skipping irrigation."
            elif "fertilizer" in task_text or "urea" in task_text or "manure" in task_text:
                if soil_type == "Red": soil_advice = "In Red soil, nutrients leach quickly. Consider splitting this fertilizer dose into two smaller applications."
                if soil_type == "Laterite": soil_advice = "In Laterite soil, phosphorus tends to get locked. Ensure you place the fertilizer close to the root zone."
            
            task_info = {
                **task,
                "phase": phase["name"],
                "task_id": task_id,
                "completed": task_id in completed_task_ids,
                "is_today": task["day"] == current_day,
                "is_past": task["day"] < current_day,
                "is_upcoming": task["day"] > current_day,
                "days_until": task["day"] - current_day,
                "soil_advice": soil_advice
            }
            
            if task["day"] == current_day:
                today_tasks.append(task_info)
                today_phase = phase["name"]
            elif task["day"] > current_day and len(upcoming_tasks) < 3:
                upcoming_tasks.append(task_info)
    
    # If no exact day match, find the nearest upcoming task
    if not today_tasks:
        for phase in journey_data["phases"]:
            for task in phase["tasks"]:
                if task["day"] >= current_day:
                    task_id = f"{phase['name']}_{task['day']}"
                    
                    soil_advice = None
                    task_text = f"{task['what']} {task['how']} {task['why']}".lower()
                    if "irrigate" in task_text or "water" in task_text:
                        if soil_type == "Black": soil_advice = "Since you have Black soil, ensure the field is not already waterlogged before this irrigation."
                        if soil_type == "Red": soil_advice = "Since you have Red/Sandy soil, water drains fast. Check moisture deeply before skipping irrigation."
                    elif "fertilizer" in task_text or "urea" in task_text or "manure" in task_text:
                        if soil_type == "Red": soil_advice = "In Red soil, nutrients leach quickly. Consider splitting this fertilizer dose into two smaller applications."
                        if soil_type == "Laterite": soil_advice = "In Laterite soil, phosphorus tends to get locked. Ensure you place the fertilizer close to the root zone."
                    
                    today_tasks.append({
                        **task,
                        "phase": phase["name"],
                        "task_id": task_id,
                        "completed": task_id in completed_task_ids,
                        "is_today": True,
                        "is_past": False,
                        "is_upcoming": False,
                        "days_until": task["day"] - current_day,
                        "soil_advice": soil_advice
                    })
                    today_phase = phase["name"]
                    break
            if today_tasks:
                break
    
    progress = min(round((current_day / total_days) * 100, 1), 100)
    
    return jsonify({
        "active": True,
        "crop": crop,
        "soil_type": soil_type,
        "start_date": journey["start_date"],
        "current_day": current_day,
        "total_days": total_days,
        "progress_pct": progress,
        "current_phase": today_phase,
        "today_tasks": today_tasks,
        "upcoming_tasks": upcoming_tasks,
        "all_phases": journey_data["phases"],
        "completed_tasks": completed_task_ids,
        "is_complete": current_day > total_days
    })

@app.route("/api/journey/start", methods=["POST"])
def start_journey():
    data = request.json
    crop = data.get("crop", "")
    soil_type = data.get("soil_type", "Standard")
    start_date = data.get("start_date", datetime.now().strftime("%Y-%m-%d"))
    
    if not crop:
        return jsonify({"error": "Crop name required"}), 400
    
    journey = {
        "crop": crop,
        "soil_type": soil_type,
        "start_date": start_date,
        "completed_tasks": []
    }
    save_journey(journey)
    return jsonify({"status": "success", "message": f"Crop journey started for {crop}!", "journey": journey})

@app.route("/api/journey/complete-task", methods=["POST"])
def complete_journey_task():
    data = request.json
    task_id = data.get("task_id", "")
    
    journey = load_journey()
    if not journey:
        return jsonify({"error": "No active journey"}), 400
    
    if task_id not in journey.get("completed_tasks", []):
        journey.setdefault("completed_tasks", []).append(task_id)
        save_journey(journey)
    
    return jsonify({"status": "success", "completed_tasks": journey["completed_tasks"]})

@app.route("/api/journey/stop", methods=["POST"])
def stop_journey():
    if os.path.exists(JOURNEY_FILE):
        os.remove(JOURNEY_FILE)
    return jsonify({"status": "success", "message": "Journey ended."})

if __name__ == "__main__":
    print("=" * 50)
    print("  MITTI Backend Server")
    print("  Dashboard -> http://localhost:5000")
    print("  Demo data -> http://localhost:5000/demo")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)

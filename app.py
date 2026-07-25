"""
MITTI — Production Backend Server
Flask + Crop Suitability Engine + Twilio Voice Call + Dynamic Wisdom
Samsung Solve for Tomorrow 2025 - Refactored for Enterprise Security
"""

import os
import sys
import time
import json
import hmac
import random
import hashlib
import uuid
import logging
import threading
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, session, make_response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from dotenv import load_dotenv

# Load secure environment configurations
load_dotenv()

# Setup structured and redacted logging
class RedactingFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', secrets=None):
        super().__init__(fmt, datefmt, style)
        self.secrets = secrets or ["password", "token", "key", "secret", "ssid"]

    def format(self, record):
        message = super().format(record)
        for secret in self.secrets:
            if secret in message.lower():
                # Redact matched lines containing credentials
                message = "[REDACTED LOG ENTRY CONTAINING SECRETS]"
        return message

logger = logging.getLogger("mitti_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = RedactingFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Application Keys configuration
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "mitti_fallback_secure_key_123")
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Talisman Security Headers integration
Talisman(app, 
         force_https=False,  # Set to True when deploying behind Nginx with SSL
         content_security_policy={
             'default-src': '\'self\'',
             'script-src': ['\'self\'', 'https://unpkg.com', 'https://translate.google.com', 'https://translate.googleapis.com'],
             'style-src': ['\'self\'', '\'unsafe-inline\'', 'https://fonts.googleapis.com', 'https://translate.googleapis.com'],
             'font-src': ['\'self\'', 'https://fonts.gstatic.com'],
             'img-src': ['\'self\'', 'data:', 'https://translate.google.com', 'https://translate.googleapis.com', 'https://www.google.com']
         })

# Rate Limiter setup (In-Memory fallback for offline resilience)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Import extracted agronomic profiles data
from crop_profiles import crop_profiles, STATE_TO_REGION, STATE_SOIL_TYPES, rotation_rules
from ml_service import CropDiseaseClassifier

# Thread lock for file operations
db_lock = threading.Lock()

# Load users file safely and initialize credentials if needed
USERS_FILE = "users.json"
DEFAULT_PASS = os.getenv("ADMIN_PASSWORD", "MittiPass123!")

def load_users():
    with db_lock:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                users = json.load(f)
                
            # Enforce password hashes for users
            modified = False
            for phone, data in users.items():
                if "password_hash" not in data:
                    data["password_hash"] = generate_password_hash(DEFAULT_PASS)
                    data["role"] = "admin" if phone in ["8882130424", "7011881299"] else "farmer"
                    modified = True
            if modified:
                with open(USERS_FILE, "w", encoding="utf-8") as f:
                    json.dump(users, f, indent=4)
            return users
        return {}

users_db = load_users()

# ─── Latest sensor data (in-memory state) ─────────────
latest = {
    "n": 120, "p": 45, "k": 210,
    "moisture": 45, "ec": 0.8, "ph": 6.8,
    "temp": 31, "humidity": 60,
    "mq135": 210, "raining": False,
    "pump": False,
    "timestamp": None
}

# ─── Replay Attack sliding cache ──────────────────────
seen_nonces = {}  # nonce -> expiry_time

def is_valid_nonce(nonce, timestamp_str):
    try:
        timestamp = float(timestamp_str)
        now = time.time()
        # Reject if request is older than 30 seconds
        if abs(now - timestamp) > 30.0:
            return False
        
        # Check for replay duplicate
        if nonce in seen_nonces:
            return False
            
        # Cache nonce until expiration window has passed
        seen_nonces[nonce] = now + 30.0
        
        # Prune expired nonces periodically
        expired = [n for n, exp in seen_nonces.items() if now > exp]
        for n in expired:
            del seen_nonces[n]
            
        return True
    except Exception as e:
        logger.error(f"Error validating nonce: {e}")
        return False

# ─── Sensor Validation Module ─────────────────────────
def validate_sensor_payload(data):
    try:
        moisture = float(data.get("moisture", 0))
        ph = float(data.get("ph", 7.0))
        n = float(data.get("n", 0))
        p = float(data.get("p", 0))
        k = float(data.get("k", 0))
        ec = float(data.get("ec", 0.0))
        
        # Physical constraints check
        if not (0.0 <= moisture <= 100.0): return False, "Moisture must be in range 0-100%"
        if not (0.0 <= ph <= 14.0): return False, "pH must be in range 0-14"
        if n < 0 or p < 0 or k < 0: return False, "NPK macronutrients cannot be negative"
        if ec < 0: return False, "Electrical conductivity cannot be negative"
        
        return True, "Valid"
    except Exception as e:
        return False, f"Format conversion error: {str(e)}"

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

def get_greeting(state="Rajasthan", lang="en"):
    hour = datetime.now().hour
    greetings = {
        "Punjab": "Sat Sri Akal",
        "Haryana": "Ram Ram",
        "Uttar Pradesh": "Ram Ram",
        "Rajasthan": "Khamma Ghani",
        "Gujarat": "Kem Cho",
        "Maharashtra": "Ram Ram",
        "West Bengal": "Nomoshkar",
        "Assam": "Namaskar",
        "Bihar": "Pranam",
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

def calculate_suitability(crop, sensor, season, region, state="Rajasthan", lang="en"):
    # Mock details return for recommendation calculations
    return 80, {"score": 80, "feedback_list": ["Optimal crop range matches."]}

def detect_soil_profile(sensor, state="Rajasthan", lang="en"):
    soils = STATE_SOIL_TYPES.get(state, ["Alluvial Soil (Fertile)"])
    return soils[0]

# ─── JWT Authentication decorators ───────────────────
def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            token = request.cookies.get('access_token') or session.get('access_token')
            
        if not token:
            return jsonify({"error": "Authentication token missing"}), 401
            
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            request.user_phone = data["phone"]
            request.user_role = data.get("role", "farmer")
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired. Please login again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid credentials session"}), 401
            
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    @jwt_required
    def decorated(*args, **kwargs):
        if request.user_role != "admin":
            return jsonify({"error": "Admin privileges required"}), 403
        return f(*args, **kwargs)
    return decorated

# ─── Auth Routes ──────────────────────────────────────
@app.route("/api/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.json or {}
    phone = data.get("phone")
    password = data.get("password")
    
    if not phone or not password:
        return jsonify({"error": "Phone number and password required"}), 400
        
    users = load_users()
    user = users.get(phone)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid phone number or password"}), 401
        
    # Generate secure access token (15 mins) and refresh token (30 days)
    access_token = jwt.encode({
        "phone": phone,
        "role": user.get("role", "farmer"),
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }, app.config["SECRET_KEY"], algorithm="HS256")
    
    refresh_token = jwt.encode({
        "phone": phone,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=30)
    }, app.config["SECRET_KEY"], algorithm="HS256")
    
    response = make_response(jsonify({
        "status": "success",
        "user": {"name": user["name"], "role": user.get("role", "farmer")},
        "access_token": access_token
    }))
    
    # Set cookies securely
    response.set_cookie('access_token', access_token, httponly=True, secure=True, samesite='Lax')
    response.set_cookie('refresh_token', refresh_token, httponly=True, secure=True, samesite='Lax')
    
    return response

@app.route("/api/logout", methods=["POST"])
def logout():
    response = make_response(jsonify({"status": "success", "message": "Logged out"}))
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    session.clear()
    return response

# ─── Core API Endpoints ────────────────────────────────
@app.route("/")
@jwt_required
def dashboard():
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
@jwt_required
def recommend():
    season = request.args.get("season", "Rabi")
    state = request.args.get("state", "Rajasthan")
    region = STATE_TO_REGION.get(state, "North")
    lang = request.args.get("lang", "en")
    
    water_filter = request.args.get("water", "Any")
    type_filter = request.args.get("type", "Any")
    soil_override = request.args.get("soil", "Auto")
    phenomenon = request.args.get("phenomenon", "None")
        
    results = {}
    for crop, profile in crop_profiles.items():
        if profile.get("season") != season:
            continue
        if water_filter != "Any" and profile.get("water_needs") != water_filter:
            continue
        if type_filter != "Any" and profile.get("crop_type") != type_filter:
            continue
            
        score, details = calculate_suitability(crop, latest, season, region, state=state, lang=lang)
        
        penalty = 0
        if region not in profile.get("regions", []): penalty += 15
        if latest["moisture"] > 0: 
            if latest["moisture"] < profile["moisture"][0] or latest["moisture"] > profile["moisture"][1]: 
                penalty += 15
        if latest["ph"] < profile["ph"][0] or latest["ph"] > profile["ph"][1]: penalty += 15
        
        if soil_override != "Auto":
            active_profile = soil_override
        else:
            active_profile = detect_soil_profile(latest, state=state, lang="en")
            
        if active_profile not in profile.get("soils", []): penalty += 40
        
        final_score = 100 - penalty
        details = {"score": max(10, final_score), "feedback_list": []}
        results[crop] = details
                
    return jsonify(results)

@app.route("/demo")
@admin_required
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

# --- IoT Server State / Telemetry validation ---
iot_state = {
    "moisture": 45,
    "pump_status": False,
    "auto_irrigate": False
}

@app.route("/api/sensors", methods=["GET", "POST"])
@limiter.limit("60 per minute")
def api_sensors():
    global latest
    if request.method == "POST":
        # Validate ESP8266 HMAC signatures
        signature = request.headers.get("X-Signature")
        nonce = request.headers.get("X-Nonce")
        timestamp = request.headers.get("X-Timestamp")
        
        hmac_secret = os.getenv("ESP8266_HMAC_SECRET", "mitti_esp8266_signing_secret_key_99").encode()
        
        if not signature or not nonce or not timestamp:
            return jsonify({"error": "Missing HMAC security parameters"}), 401
            
        # Prevent replay attacks
        if not is_valid_nonce(nonce, timestamp):
            return jsonify({"error": "Replay attack detected or request timestamp expired"}), 400
            
        data = request.json or {}
        
        # Verify HMAC signature integrity
        message = f"{nonce}:{timestamp}:{request.data.decode()}".encode()
        expected_sig = hmac.new(hmac_secret, message, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, signature):
            return jsonify({"error": "HMAC signature mismatch"}), 401
            
        # Validate range values
        is_valid, err_msg = validate_sensor_payload(data)
        if not is_valid:
            return jsonify({"error": f"Sensor verification failed: {err_msg}"}), 400
            
        # Update state
        latest.update({
            "n": int(data.get("n", latest["n"])),
            "p": int(data.get("p", latest["p"])),
            "k": int(data.get("k", latest["k"])),
            "moisture": int(data.get("moisture", latest["moisture"])),
            "ec": float(data.get("ec", latest["ec"])),
            "ph": float(data.get("ph", latest["ph"])),
            "temp": int(data.get("temp", latest["temp"])),
            "humidity": int(data.get("humidity", latest["humidity"])),
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
        })
        
        # Run auto-irrigation feedback loop
        if iot_state["auto_irrigate"]:
            if latest["moisture"] < 40:
                iot_state["pump_status"] = True
            elif latest["moisture"] >= 75:
                iot_state["pump_status"] = False
                
        return jsonify({"status": "success", "pump": iot_state["pump_status"]})

    return jsonify({
        "moisture": latest["moisture"],
        "pump_status": iot_state["pump_status"],
        "auto_irrigate": iot_state["auto_irrigate"],
        "nitrogen": latest["n"],
        "phosphorus": latest["p"],
        "potassium": latest["k"],
        "ph": latest["ph"]
    })

@app.route("/api/irrigation/auto", methods=["POST"])
@admin_required # Require admin user role & authentication for pump toggle
def toggle_auto_irrigate():
    data = request.json or {}
    confirm = data.get("confirm", False)
    if not confirm:
        return jsonify({"error": "Confirmation required before toggling water pump systems"}), 400
        
    iot_state["auto_irrigate"] = data.get("auto_irrigate", False)
    if not iot_state["auto_irrigate"]:
         iot_state["pump_status"] = False
    return jsonify({"status": "success", "state": iot_state})

# --- ML Scanner Endpoint with upload sanitation ---
ml_service = CropDiseaseClassifier()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/api/scan-image", methods=["POST"])
@limiter.limit("20 per minute")
@jwt_required
def scan_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
        
    # 1. Validate extension
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported image format. Allowed formats: PNG, JPG, JPEG"}), 400
        
    # 2. Check upload sizes (limit to 10 MB)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > 10 * 1024 * 1024:
        return jsonify({"error": "Image size exceeds 10 MB threshold"}), 400
        
    # 3. Read bytes & check magic signatures
    image_bytes = file.read()
    if len(image_bytes) < 4:
         return jsonify({"error": "Corrupt image format"}), 400
         
    # Check for JPEG (\xff\xd8\xff) or PNG (\x89PNG) signatures
    is_jpeg = (image_bytes[:3] == b'\xff\xd8\xff')
    is_png = (image_bytes[:4] == b'\x89PNG')
    if not is_jpeg and not is_png:
        return jsonify({"error": "Malicious upload blocked: Image headers mismatched extension."}), 400
        
    crop_name = request.form.get('crop', '')
    prediction = ml_service.predict(image_bytes, crop_name)
    
    # Crop solution mapping
    solution = prediction.get("solution", "General care recommended. Consult an expert.")
    if crop_name and crop_name in crop_profiles:
        crop_data = crop_profiles[crop_name]
        challenges = crop_data.get("farm_school", {}).get("challenges", [])
        for c in challenges:
            if c.get("issue") == prediction["disease"]:
                solution = c.get("solution")
                break
                
    # Add AI Safety Warning
    safety_disclaimer = "Warning: This is an AI-assisted recommendation. Please verify agricultural guidelines locally before applying treatments."
                
    return jsonify({
        "disease": prediction["disease"],
        "confidence": prediction["confidence"],
        "solution": solution,
        "safety_disclaimer": safety_disclaimer
    })

# --- Crop journey and other utility routes ---
HISTORY_FILE = "yield_history.json"

def load_history():
    with db_lock:
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f: return json.load(f)
            except: return []
        return []

def save_history(data):
    with db_lock:
        with open(HISTORY_FILE, "w") as f: json.dump(data, f, indent=4)

@app.route("/history", methods=["GET", "POST"])
@jwt_required
def history_api():
    if request.method == "POST":
        data = request.json or {}
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
@jwt_required
def get_all_crops():
    return jsonify(crop_profiles)

@app.route("/api/schemes", methods=["GET"])
@jwt_required
def get_schemes():
    return jsonify([
        {"id": "pm-kisan", "title": "PM-KISAN", "category": "Financial Aid", "description": "Support of ₹6,000 per year.", "link": "https://pmkisan.gov.in/"},
        {"id": "pmfby", "title": "PMFBY", "category": "Insurance", "description": "Crop insurance support.", "link": "https://pmfby.gov.in/"}
    ])

@app.route("/api/suggest-next", methods=["GET"])
@jwt_required
def suggest_next_crop():
    history = load_history()
    if not history:
        return jsonify({"suggestions": [], "message": "Log your first yield."})
    
    last_crop = history[-1].get("crop", "").strip()
    upcoming_season = "Rabi"
    
    suggestions = []
    rotation = rotation_rules.get(last_crop, None)
    if rotation:
        for next_crop in rotation["next"]:
            if next_crop in crop_profiles:
                suggestions.append({
                    "crop": next_crop,
                    "name": crop_profiles[next_crop].get("name_en", next_crop),
                    "rotation_reason": rotation["reason"],
                    "source": "crop_rotation"
                })
    return jsonify({"suggestions": suggestions})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

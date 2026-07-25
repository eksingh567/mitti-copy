"""
MITTI — Production Backend Server
Flask + Crop Suitability Engine + Twilio Voice Call + SQLite Storage
Samsung Solve for Tomorrow 2025 - Round 3 Security Upgrades
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
import sqlite3
from collections import deque
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
    default_limits=["200 per day", "120 per hour"],
    storage_uri="memory://"
)

# Custom Rate Limit Exceeded Logger
@app.errorhandler(429)
def ratelimit_handler(e):
    logger.warning(f"Security Alert: Rate limit exceeded by IP: {request.remote_addr} on route: {request.path}")
    return jsonify(error="Rate limit exceeded. Please slow down."), 429

# Import extracted agronomic profiles data
from crop_profiles import crop_profiles, STATE_TO_REGION, STATE_SOIL_TYPES, rotation_rules
from ml_service import CropDiseaseClassifier

# Thread lock for file operations
db_lock = threading.Lock()
DATABASE_FILE = "users.db"

def backup_and_verify_db():
    """
    Runs integrity check on users.db on startup and duplicates it to users_backup.db.
    """
    if os.path.exists(DATABASE_FILE):
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            c = conn.cursor()
            c.execute("PRAGMA integrity_check")
            res = c.fetchone()
            if res and res[0] == "ok":
                # Create backup replica
                backup_conn = sqlite3.connect("users_backup.db")
                conn.backup(backup_conn)
                backup_conn.close()
                print("SQLite Database integrity verified: ok. Backup created successfully.")
            else:
                logger.warning("Security Alert: SQLite database integrity check failed. Corruption detected!")
            conn.close()
        except Exception as e:
            print(f"Failed to backup database on startup: {e}")

def init_db():
    with db_lock:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                phone TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                state TEXT NOT NULL,
                city TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                secret TEXT NOT NULL,
                last_seen TEXT,
                firmware_version TEXT,
                status TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                token_jti TEXT PRIMARY KEY,
                phone TEXT NOT NULL,
                status TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)
        conn.commit()
        
        # Seed default test device
        c.execute("SELECT device_id FROM devices WHERE device_id = ?", ("esp8266_test_node_01",))
        if not c.fetchone():
            c.execute("""
                INSERT INTO devices (device_id, secret, status)
                VALUES (?, ?, ?)
            """, ("esp8266_test_node_01", "mitti_esp8266_signing_secret_key_99", "active"))
            conn.commit()
        
        # Migrate legacy users.json data if present
        if os.path.exists("users.json"):
            try:
                with open("users.json", "r", encoding="utf-8") as f:
                    legacy_users = json.load(f)
                
                default_pass = os.getenv("ADMIN_PASSWORD", "MittiPass123!")
                for phone, u in legacy_users.items():
                    c.execute("SELECT phone FROM users WHERE phone = ?", (phone,))
                    if not c.fetchone():
                        p_hash = u.get("password_hash") or generate_password_hash(default_pass)
                        role = "admin" if phone in ["8882130424", "7011881299"] else "farmer"
                        c.execute("""
                            INSERT INTO users (phone, name, state, city, password_hash, role)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (phone, u["name"], u["state"], u["city"], p_hash, role))
                conn.commit()
                print("Successfully migrated users to SQLite DB.")
                os.rename("users.json", "users.json.bak")
            except Exception as e:
                print(f"Error during SQLite user migration: {e}")
        conn.close()

# Initialize database, integrity verify and back up
init_db()
backup_and_verify_db()

# ─── Latest sensor data (in-memory state) ─────────────
latest = {
    "n": 120, "p": 45, "k": 210,
    "moisture": 45, "ec": 0.8, "ph": 6.8,
    "temp": 31, "humidity": 60,
    "mq135": 210, "raining": False,
    "pump": False,
    "timestamp": None
}

# ─── Fast Nonce cache: set for O(1) checks, deque for eviction ──
seen_nonces = set()
nonce_queue = deque()

def is_valid_nonce(nonce, timestamp_str):
    try:
        timestamp = float(timestamp_str)
        now = time.time()
        
        # Reject if request timestamp is older than 30 seconds
        if abs(now - timestamp) > 30.0:
            logger.warning(f"Security Alert: Replay attack prevention - Expired timestamp {timestamp} from client (current: {now})")
            return False
        
        # Check for replay duplicate in O(1) set lookup
        if nonce in seen_nonces:
            logger.warning(f"Security Alert: Replay attack prevention - Duplicate nonce detected: {nonce}")
            return False
            
        # Add to set and sliding queue cache
        seen_nonces.add(nonce)
        nonce_queue.append((nonce, now + 30.0))
        
        # Evict expired nonces efficiently
        while nonce_queue and now > nonce_queue[0][1]:
            expired_nonce, _ = nonce_queue.popleft()
            seen_nonces.discard(expired_nonce)
            
        return True
    except Exception as e:
        logger.error(f"Error validating nonce: {e}")
        return False

# ─── Sensor Validation with Anomaly Checking ──────────
def validate_sensor_payload(data):
    try:
        moisture = float(data.get("moisture", 0))
        ph = float(data.get("ph", 7.0))
        n = float(data.get("n", 0))
        p = float(data.get("p", 0))
        k = float(data.get("k", 0))
        ec = float(data.get("ec", 0.0))
        temp = float(data.get("temp", 25.0))
        humidity = float(data.get("humidity", 50.0))
        raining = bool(data.get("raining", False))
        
        # Range constraints check
        if not (0.0 <= moisture <= 100.0): return False, "Moisture must be in range 0-100%"
        if not (0.0 <= ph <= 14.0): return False, "pH must be in range 0-14"
        if n < 0 or p < 0 or k < 0: return False, "NPK macronutrients cannot be negative"
        if ec < 0: return False, "Electrical conductivity cannot be negative"
        
        # Cross-sensor physical anomaly checking
        # Anomaly 1: Temp & Humidity high, but Rain is False (Sensor defect / impossible field state)
        if humidity > 95.0 and temp > 40.0 and not raining:
            return False, "Anomaly: Humidity >95% with Temperature >40C but Rain is False represents an invalid physical state."
            
        # Anomaly 2: EC is 0 but Moisture is 100% (Water saturated soil always conducts via natural salts)
        if ec == 0.0 and moisture == 100.0:
            return False, "Anomaly: Fully saturated moisture (100%) cannot have zero electrical conductivity."
            
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
    return 80, {"score": 80, "feedback_list": ["Optimal crop range matches."]}

def detect_soil_profile(sensor, state="Rajasthan", lang="en"):
    soils = STATE_SOIL_TYPES.get(state, ["Alluvial Soil (Fertile)"])
    return soils[0]

# ─── JWT Authentication decorators ───────────────────
def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Enforce Bearer token verification
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        # Cookie session fallback
        if not token:
            token = request.cookies.get('access_token') or session.get('access_token')
            if token:
                # CSRF protection check: require custom X-Requested-With header for cookie-based calls
                csrf_header = request.headers.get("X-Requested-With")
                if not csrf_header or csrf_header.lower() != "xmlhttprequest":
                    logger.warning(f"Security Alert: CSRF block - Missing custom headers from IP: {request.remote_addr}")
                    return jsonify({"error": "CSRF verification failed"}), 403
        
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

# ─── Auth Routes (v1 prefix included) ──────────────────────────────────
@app.route("/api/login", methods=["POST"])
@app.route("/api/v1/login", methods=["POST"])
@limiter.limit("5 per minute")  # Enforce strict 5/min limit on login endpoint
def login():
    data = request.json or {}
    phone = data.get("phone")
    password = data.get("password")
    
    if not phone or not password:
        return jsonify({"error": "Phone number and password required"}), 400
        
    # Read user credentials from SQLite database
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT name, password_hash, role FROM users WHERE phone = ?", (phone,))
    user_row = c.fetchone()
    conn.close()
    
    if not user_row or not check_password_hash(user_row[1], password):
        logger.warning(f"Security Alert: Failed login attempt for phone: {phone} from IP: {request.remote_addr}")
        return jsonify({"error": "Invalid phone number or password"}), 401
        
    # Generate unique JTI for Refresh Token Rotation (RTR) tracking
    refresh_jti = str(uuid.uuid4())
    
    # Save active refresh token JTI to SQLite
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO refresh_tokens (token_jti, phone, status, expires_at)
        VALUES (?, ?, ?, ?)
    """, (refresh_jti, phone, "active", (datetime.utcnow() + timedelta(days=30)).isoformat()))
    conn.commit()
    conn.close()

    # Generate secure access token (15 mins) and refresh token (30 days)
    access_token = jwt.encode({
        "phone": phone,
        "role": user_row[2],
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }, app.config["SECRET_KEY"], algorithm="HS256")
    
    refresh_token = jwt.encode({
        "phone": phone,
        "jti": refresh_jti,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=30)
    }, app.config["SECRET_KEY"], algorithm="HS256")
    
    response = make_response(jsonify({
        "status": "success",
        "user": {"name": user_row[0], "role": user_row[2]},
        "access_token": access_token
    }))
    
    # Store access token in-memory only. Set refresh token in HttpOnly cookie.
    response.set_cookie('refresh_token', refresh_token, httponly=True, secure=False, samesite='Lax')
    
    return response

@app.route("/api/refresh", methods=["POST"])
@app.route("/api/v1/refresh", methods=["POST"])
@limiter.limit("30 per minute")
def refresh_token():
    r_token = request.cookies.get('refresh_token')
    if not r_token:
        # Check JSON body fallback safely
        data = request.get_json(silent=True) or {}
        r_token = data.get("refresh_token")
        
    if not r_token:
        return jsonify({"error": "Refresh token is missing"}), 401
    try:
        payload = jwt.decode(r_token, app.config["SECRET_KEY"], algorithms=["HS256"])
        if payload.get("type") != "refresh":
            return jsonify({"error": "Invalid token type"}), 401
            
        jti = payload.get("jti")
        phone = payload.get("phone")
        
        # Verify refresh token JTI in SQLite for reuse detection (RTR breach verification)
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute("SELECT status FROM refresh_tokens WHERE token_jti = ?", (jti,))
        token_row = c.fetchone()
        
        if not token_row:
            conn.close()
            logger.warning(f"Security Alert: Unknown refresh token JTI {jti} from IP: {request.remote_addr}")
            return jsonify({"error": "Invalid refresh token"}), 401
            
        if token_row[0] == "revoked":
            # Token reuse detected! Invalidate ALL refresh tokens for the user (breach response)
            c.execute("UPDATE refresh_tokens SET status = 'revoked' WHERE phone = ?", (phone,))
            conn.commit()
            conn.close()
            logger.warning(f"Security Alert: Refresh Token Reuse detected (JTI {jti})! Session hijack threat block. All user sessions revoked.")
            return jsonify({"error": "Session hijacked: Token reuse detected. Please re-authenticate."}), 401
            
        # Revoke the used refresh token
        c.execute("UPDATE refresh_tokens SET status = 'revoked' WHERE token_jti = ?", (jti,))
        
        # Issue new JTI for rotated refresh token
        new_refresh_jti = str(uuid.uuid4())
        c.execute("""
            INSERT INTO refresh_tokens (token_jti, phone, status, expires_at)
            VALUES (?, ?, ?, ?)
        """, (new_refresh_jti, phone, "active", (datetime.utcnow() + timedelta(days=30)).isoformat()))
        
        # Fetch user role/details
        c.execute("SELECT name, role FROM users WHERE phone = ?", (phone,))
        user_row = c.fetchone()
        conn.commit()
        conn.close()
        
        if not user_row:
             return jsonify({"error": "User not found"}), 401
             
        # Issue rotated refresh token & new access token
        access_token = jwt.encode({
            "phone": phone,
            "role": user_row[1],
            "exp": datetime.utcnow() + timedelta(minutes=15)
        }, app.config["SECRET_KEY"], algorithm="HS256")
        
        new_refresh_token = jwt.encode({
            "phone": phone,
            "jti": new_refresh_jti,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=30)
        }, app.config["SECRET_KEY"], algorithm="HS256")
        
        response = make_response(jsonify({
            "access_token": access_token,
            "user": {"name": user_row[0], "role": user_row[1]}
        }))
        response.set_cookie('refresh_token', new_refresh_token, httponly=True, secure=False, samesite='Lax')
        return response
    except Exception as e:
        logger.warning(f"Security Alert: Silent refresh token rotation failed: {str(e)}")
        return jsonify({"error": "Invalid or expired refresh token"}), 401

@app.route("/api/logout", methods=["POST"])
@app.route("/api/v1/logout", methods=["POST"])
def logout():
    response = make_response(jsonify({"status": "success", "message": "Logged out"}))
    response.delete_cookie('refresh_token')
    session.clear()
    return response

# ─── Core API Endpoints (v1 prefixes mapped) ───────────────────────────
@app.route("/")
@app.route("/api/v1/")
@jwt_required
@limiter.limit("120 per minute")
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
@app.route("/api/v1/recommend")
@jwt_required
def recommend():
    season = request.args.get("season", "Rabi")
    state = request.args.get("state", "Rajasthan")
    region = STATE_TO_REGION.get(state, "North")
    lang = request.args.get("lang", "en")
    
    water_filter = request.args.get("water", "Any")
    type_filter = request.args.get("type", "Any")
    soil_override = request.args.get("soil", "Auto")
        
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
@app.route("/api/v1/demo")
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
@app.route("/api/v1/sensors", methods=["GET", "POST"])
@limiter.limit("60 per minute")  # Limit sensors to 60/min
def api_sensors():
    global latest
    if request.method == "POST":
        # Validate ESP8266 HMAC signatures
        signature = request.headers.get("X-Signature")
        nonce = request.headers.get("X-Nonce")
        timestamp = request.headers.get("X-Timestamp")
        device_id = request.headers.get("X-Device-ID", "esp8266_test_node_01")
        firmware = request.headers.get("X-Firmware-Version", "1.0.0")
        
        if not signature or not nonce or not timestamp:
            logger.warning(f"Security Alert: Invalid HMAC parameters from IP: {request.remote_addr}")
            return jsonify({"error": "Missing HMAC security parameters"}), 401
            
        # Fetch device registration secret and verify active status
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute("SELECT secret, status FROM devices WHERE device_id = ?", (device_id,))
        device_row = c.fetchone()
        
        if not device_row or device_row[1] != "active":
            conn.close()
            logger.warning(f"Security Alert: Blocked telemetry upload from unauthorized/revoked device ID: {device_id} from IP: {request.remote_addr}")
            return jsonify({"error": "Unauthorized device"}), 403
            
        hmac_secret = device_row[0].encode()
            
        # Prevent replay attacks using deque+set eviction cache
        if not is_valid_nonce(nonce, timestamp):
            conn.close()
            logger.warning(f"Security Alert: Replay attack blocked (nonce: {nonce}, timestamp: {timestamp}) from IP: {request.remote_addr}")
            return jsonify({"error": "Replay attack detected or request timestamp expired"}), 400
            
        data = request.json or {}
        
        # Verify HMAC signature integrity
        message = f"{nonce}:{timestamp}:{request.data.decode()}".encode()
        expected_sig = hmac.new(hmac_secret, message, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, signature):
            conn.close()
            logger.warning(f"Security Alert: HMAC signature mismatch from device: {device_id} IP: {request.remote_addr}")
            return jsonify({"error": "HMAC signature mismatch"}), 401
            
        # Validate range and anomaly checking rules
        is_valid, err_msg = validate_sensor_payload(data)
        if not is_valid:
            conn.close()
            logger.warning(f"Security Alert: Sensor anomaly check blocked payload from IP: {request.remote_addr} ({err_msg})")
            return jsonify({"error": f"Sensor verification failed: {err_msg}"}), 400
            
        # Log successful telemetry and update last seen in SQLite
        c.execute("UPDATE devices SET last_seen = ?, firmware_version = ? WHERE device_id = ?", 
                  (datetime.utcnow().isoformat(), firmware, device_id))
        conn.commit()
        conn.close()

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
@app.route("/api/v1/irrigation/auto", methods=["POST"])
@admin_required
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
@app.route("/api/v1/scan-image", methods=["POST"])
@limiter.limit("20 per minute")  # Limit scanner uploads to 20/min
@jwt_required
def scan_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
        
    # 1. Validate extension
    if not allowed_file(file.filename):
        logger.warning(f"Security Alert: Invalid upload extension blocked from IP: {request.remote_addr}")
        return jsonify({"error": "Unsupported image format. Allowed formats: PNG, JPG, JPEG"}), 400
        
    # 2. Check upload sizes (limit to 10 MB)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > 10 * 1024 * 1024:
        logger.warning(f"Security Alert: Upload size limit (10MB) exceeded from IP: {request.remote_addr}")
        return jsonify({"error": "Image size exceeds 10 MB threshold"}), 400
        
    # 3. Read bytes & check magic signatures
    image_bytes = file.read()
    if len(image_bytes) < 4:
         return jsonify({"error": "Corrupt image format"}), 400
         
    # Check for JPEG (\xff\xd8\xff) or PNG (\x89PNG) signatures
    is_jpeg = (image_bytes[:3] == b'\xff\xd8\xff')
    is_png = (image_bytes[:4] == b'\x89PNG')
    if not is_jpeg and not is_png:
        logger.warning(f"Security Alert: Upload blocked due to mismatched magic bytes from IP: {request.remote_addr}")
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
                
    # Add AI Safety Warning Wording Update
    safety_disclaimer = "This diagnosis is AI-assisted and should be confirmed using local agricultural guidance before applying pesticides, fertilizers, or other crop treatments."
                
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
@app.route("/api/v1/history", methods=["GET", "POST"])
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
@app.route("/api/v1/crops")
@jwt_required
def get_all_crops():
    return jsonify(crop_profiles)

@app.route("/api/schemes", methods=["GET"])
@app.route("/api/v1/schemes", methods=["GET"])
@jwt_required
def get_schemes():
    return jsonify([
        {"id": "pm-kisan", "title": "PM-KISAN", "category": "Financial Aid", "description": "Support of ₹6,000 per year.", "link": "https://pmkisan.gov.in/"},
        {"id": "pmfby", "title": "PMFBY", "category": "Insurance", "description": "Crop insurance support.", "link": "https://pmfby.gov.in/"}
    ])

@app.route("/api/suggest-next", methods=["GET"])
@app.route("/api/v1/suggest-next", methods=["GET"])
@jwt_required
def suggest_next_crop():
    history = load_history()
    if not history:
        return jsonify({"suggestions": [], "message": "Log your first yield."})
    
    last_crop = history[-1].get("crop", "").strip()
    
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

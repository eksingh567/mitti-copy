import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Make sure ml_service and threading are imported
if "import threading" not in code:
    code = code.replace("from flask import Flask, jsonify, render_template, request", 
                        "from flask import Flask, jsonify, render_template, request\nimport threading\nimport time\nfrom ml_service import CropDiseaseClassifier")

# Backend State for IoT
state_code = """
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
    crop_name = request.form.get('crop', 'Unknown')
    
    # Read bytes for the ML service
    image_bytes = file.read()
    
    # Run the solid stub ML pipeline
    prediction = ml_service.predict(image_bytes, crop_name)
    
    # Find the solution from crop_profiles
    solution = "General care recommended. Consult an expert."
    if crop_name in crop_profiles:
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

"""

if "api/sensors" not in code:
    code = code.replace("if __name__ == \"__main__\":", state_code + "\nif __name__ == \"__main__\":")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Backend endpoints and background thread injected successfully.")

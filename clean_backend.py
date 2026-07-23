import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# 1. Add CORS import and setup
if "from flask_cors import CORS" not in app_py:
    app_py = app_py.replace('from flask import Flask', 'from flask import Flask\nfrom flask_cors import CORS')
    app_py = app_py.replace('app = Flask(__name__)', 'app = Flask(__name__)\nCORS(app)')

# 2. Remove DASHBOARD_HTML
if 'DASHBOARD_HTML = """' in app_py:
    parts = app_py.split('DASHBOARD_HTML = """')
    before = parts[0]
    after = parts[1].split('"""\n', 1)[1]
    app_py = before + after

# 3. Clean up the dashboard route to return JSON
dashboard_old = '''@app.route("/")
def dashboard():
    """Serve the live dashboard."""
    greeting = f"Namaste, {session.get('name', 'Farmer')}! {get_greeting()}"
    user_state = session.get("state", "Rajasthan")
    soil_profile = detect_soil_profile(latest, state=user_state)
    
    return render_template_string(
        DASHBOARD_HTML,
        data=latest,
        advisories=["Optimal conditions for Kharif crops.", "Maintain soil moisture."],
        english="Optimal conditions for Kharif crops. Maintain soil moisture.",
        wisdom=generate_wisdom(),
        greeting=greeting,
        timestamp=latest.get("timestamp", "Not yet received"),
        state=user_state,
        city=session.get("city", "Jaipur"),
        soil_profile=soil_profile
    )'''

dashboard_new = '''@app.route("/")
def dashboard():
    """Serve the live dashboard data as JSON."""
    user_state = request.args.get("state", "Rajasthan")
    soil_profile = detect_soil_profile(latest, state=user_state)
    
    return jsonify({
        "status": "ok",
        "data": latest,
        "advisories": ["Optimal conditions for Kharif crops.", "Maintain soil moisture."],
        "wisdom": generate_wisdom(),
        "soil_profile": soil_profile
    })'''

app_py = app_py.replace(dashboard_old, dashboard_new)

# 4. Clean up /demo to return JSON redirect
demo_old = '''    return redirect(url_for("dashboard"))'''
demo_new = '''    return jsonify({"status": "demo_data_loaded", "profile": profile, "data": latest})'''
app_py = app_py.replace(demo_old, demo_new)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Backend API created successfully")

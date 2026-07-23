import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

with open('old_dashboard.html', 'r', encoding='utf-8') as f:
    old_html = f.read()

# Add DASHBOARD_HTML at the top
dashboard_var = 'DASHBOARD_HTML = """\\n' + old_html.replace('"', '\\"') + '\\n"""\n'
app_py = app_py.replace('app.config["SECRET_KEY"] = "mitti_secret_key_987"\n', 'app.config["SECRET_KEY"] = "mitti_secret_key_987"\n\n' + dashboard_var)

# Replace the dashboard() route to return HTML
old_dashboard_route = '''@app.route("/")
def dashboard():
    """Serve the live dashboard."""
    # Dynamic greeting with name
    greeting = f"Namaste, {session.get('name', 'Farmer')}! {get_greeting()}"
    
    # Detect soil profile category (use farmer's state for tiebreaker)
    user_state = session.get("state", "Rajasthan")
    soil_profile = detect_soil_profile(latest, state=user_state)
    
    return jsonify({"status": "ok", "profile": soil_profile})'''

new_dashboard_route = '''@app.route("/")
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

app_py = app_py.replace(old_dashboard_route, new_dashboard_route)

# Add /demo route to populate data and redirect to dashboard
demo_route = '''
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
    return redirect(url_for("dashboard"))
'''
app_py = app_py.replace('if __name__ == "__main__":', demo_route + '\nif __name__ == "__main__":')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Restored HTML UI")

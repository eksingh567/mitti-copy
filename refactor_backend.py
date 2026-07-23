import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# Match the crop_profiles dictionary inside calculate_suitability
# It looks like:
# def calculate_suitability(crop_name, soil_data, season, region, state=None):
#     crop_profiles = { ... }

match = re.search(r'def calculate_suitability\(.*?\):\n(    crop_profiles = \{.*?\n    \})', app_py, re.DOTALL)
if match:
    crop_profiles_dict = match.group(1)
    # Remove it from the function
    app_py = app_py.replace(crop_profiles_dict, '')
    
    # Dedent it by 4 spaces
    global_crop_profiles = '\n'.join([line[4:] if line.startswith('    ') else line for line in crop_profiles_dict.split('\n')])
    
    # Place it before the function
    app_py = app_py.replace('def calculate_suitability', global_crop_profiles + '\n\ndef calculate_suitability')

# Add the /history and /crops endpoints
endpoints = '''
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
'''

app_py = app_py.replace('if __name__ == "__main__":', endpoints + '\nif __name__ == "__main__":')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Refactored crop_profiles to global and added API endpoints")

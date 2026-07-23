import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_return = '''    if not soil_match:
        penalties += 20
        
    return max(0, 100 - penalties), profile'''

new_return = '''    if not soil_match:
        penalties += 20
        
    if "ph" in profile:
        profile["ph_range"] = f"{profile['ph'][0]} - {profile['ph'][1]}"
    else:
        profile["ph_range"] = "N/A"
        
    if "moisture" in profile:
        profile["moisture_range"] = f"{profile['moisture'][0]}% - {profile['moisture'][1]}%"
    else:
        profile["moisture_range"] = "N/A"
        
    if penalties == 0:
        profile["feedback"] = "Excellent match! All criteria are optimal."
    elif penalties <= 20:
        profile["feedback"] = "Good match. Minor seasonal or soil adjustments needed."
    else:
        profile["feedback"] = "Low suitability. Consider alternative crops for current conditions."
        
    return max(0, 100 - penalties), profile'''

code = code.replace(old_return, new_return)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Added missing fields to fix UI undefined errors")

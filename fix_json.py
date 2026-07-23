import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_for_loop = '''    for crop in crops:
        score, details = calculate_suitability(crop, latest, season, region, state=state)
        results[crop] = {"score": score, "details": details}'''

new_for_loop = '''    for crop in crops:
        score, details = calculate_suitability(crop, latest, season, region, state=state)
        # Check if details is a dictionary to prevent errors if crop not found
        if isinstance(details, dict):
            details["score"] = score
            results[crop] = details'''

code = code.replace(old_for_loop, new_for_loop)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Fixed recommend endpoint")

import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# 1. Update Ancient Wisdom
old_wisdom_func_pattern = r'def generate_wisdom\(\):\n    wisdoms = \[.*?\]\n    return random\.choice\(wisdoms\)'

new_wisdom_func = '''def generate_wisdom():
    wisdoms = [
        "Krishi Parashara: 'Rainfall in the month of Shravana brings an abundant harvest.'",
        "Vrikshayurveda: 'Applying Neem cake not only enriches the soil but acts as a powerful natural pest deterrent.'",
        "Traditional Knowledge: 'A deeply ploughed field in the hot summer drinks the monsoon rain completely.'",
        "Ancient Wisdom: 'Rotating leguminous crops with cereals restores the earth's vital life force.'",
        "Chanakya Niti: 'Agriculture is the root of all wealth.' Protect your topsoil like gold."
    ]
    return random.choice(wisdoms)'''

# We don't know exact regex match if it changed, let's just replace the whole function using standard string replace if we know it.
# Actually, let's just find def generate_wisdom(): and replace it and the next 4 lines.
app_py = re.sub(r'def generate_wisdom\(\):.*?return random\.choice\(wisdoms\)', new_wisdom_func, app_py, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Updated app.py with Ancient Indian Farming Wisdom")

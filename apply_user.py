import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace STATE_TO_REGION
state_region_pattern = r'STATE_TO_REGION\s*=\s*\{.*?\n\}'
new_state_region = '''STATE_TO_REGION = {
    "Punjab": "North", "Haryana": "North", "Himachal Pradesh": "North", "Uttarakhand": "North",
    "Uttar Pradesh": "North", "Delhi": "North", "Jammu & Kashmir": "North", "Ladakh": "North",
    "Chandigarh": "North",
    "Tamil Nadu": "South", "Kerala": "South", "Karnataka": "South", "Andhra Pradesh": "South",
    "Telangana": "South", "Puducherry": "South", "Lakshadweep": "South",
    "Andaman & Nicobar Islands": "South",
    "West Bengal": "East", "Bihar": "East", "Jharkhand": "East", "Odisha": "East",
    "Sikkim": "East", "Assam": "East", "Meghalaya": "East", "Tripura": "East",
    "Mizoram": "East", "Manipur": "East", "Nagaland": "East", "Arunachal Pradesh": "East",
    "Rajasthan": "West", "Gujarat": "West", "Maharashtra": "West", "Goa": "West",
    "Madhya Pradesh": "West", "Chhattisgarh": "West",
    "Dadra & Nagar Haveli and Daman & Diu": "West"
}'''
code = re.sub(state_region_pattern, new_state_region, code, flags=re.DOTALL)

# Replace STATE_SOIL_TYPES
state_soil_pattern = r'STATE_SOIL_TYPES\s*=\s*\{.*?\n\}'
new_state_soil = '''STATE_SOIL_TYPES = {
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
    "Jammu & Kashmir": ["Forest/Mountain Soil", "Alluvial Soil (Fertile)", "Peaty/Marshy Soil"],
    "Ladakh": ["Arid / Desert Soil", "Forest/Mountain Soil", "Saline/Alkaline Soil"],
    "Puducherry": ["Alluvial Soil (Fertile)", "Coastal Sandy Soil", "Red & Yellow Soil"],
    "Andaman & Nicobar Islands": ["Laterite Soil", "Coastal Sandy Soil", "Alluvial Soil (Fertile)", "Forest/Mountain Soil"],
    "Lakshadweep": ["Coastal Sandy Soil", "Saline/Alkaline Soil"],
    "Dadra & Nagar Haveli and Daman & Diu": ["Red & Yellow Soil", "Laterite Soil", "Coastal Sandy Soil", "Alluvial Soil (Fertile)"]
}'''
code = re.sub(state_soil_pattern, new_state_soil, code, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Applied user changes to app.py")

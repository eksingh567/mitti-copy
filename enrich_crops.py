import re

with open('app.py', 'r', encoding='utf-8') as f:
    app_py = f.read()

# Define the enrichment mapping
# format: "CropName": ("water_needs", "crop_type")
enrichments = {
    "Wheat": ("Medium", "Cereal"),
    "Paddy": ("High", "Cereal"),
    "Cotton": ("Medium", "Cash Crop"),
    "Mustard": ("Low", "Oilseed"),
    "Maize": ("Medium", "Cereal"),
    "Potato": ("High", "Vegetable"),
    "Sugarcane": ("High", "Cash Crop"),
    "Jute": ("High", "Cash Crop"),
    "Tea": ("High", "Plantation"),
    "Coffee": ("Medium", "Plantation"),
    "Rubber": ("High", "Plantation"),
    "Groundnut": ("Low", "Oilseed"),
    "Soybean": ("Medium", "Oilseed"),
    "Turmeric": ("Medium", "Spice"),
    "Cumin": ("Low", "Spice"),
    "Coriander": ("Medium", "Spice"),
    "Cardamom": ("High", "Spice"),
    "BlackPepper": ("High", "Spice"),
    "Coconut": ("Medium", "Plantation"),
    "Bajra": ("Low", "Cereal"),
    "Jowar": ("Low", "Cereal"),
    "Gram": ("Low", "Pulse"),
    "Tur": ("Medium", "Pulse"),
    "Onion": ("Medium", "Vegetable"),
    "Tomato": ("Medium", "Vegetable")
}

def enrich_crop(match):
    crop_name = match.group(1)
    crop_content = match.group(2)
    
    # Check if crop exists in enrichments
    # Wait, the match.group(1) is the string key like "Wheat", "Paddy"
    for key in enrichments:
        if key in crop_content or key == crop_name:
            water, ctype = enrichments[key]
            # Add attributes at the end of the dict, before the closing brace
            # Remove trailing brace and any whitespace
            content_stripped = crop_content.rstrip()
            if content_stripped.endswith('}'):
                content_stripped = content_stripped[:-1]
            
            # Avoid adding multiple times
            if '"water_needs"' not in content_stripped:
                content_stripped += f', "water_needs": "{water}", "crop_type": "{ctype}"}}'
            else:
                content_stripped += '}'
            return f'"{crop_name}": {content_stripped}'
            
    return match.group(0)

# The crop_profiles dict looks like "Wheat": {"name_en": ...}
app_py = re.sub(r'"([A-Za-z]+)":\s*(\{.*?\})', enrich_crop, app_py)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_py)

print("Enriched crop_profiles with water_needs and crop_type!")

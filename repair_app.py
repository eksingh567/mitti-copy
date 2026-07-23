import ast
import json

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# We need to extract crop_profiles safely.
# Since it's corrupted, ast.parse might still work because it's technically valid Python (just deeply nested).
tree = ast.parse(code)
crop_dict_node = None
for node in tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == 'crop_profiles':
                crop_dict_node = node.value
                break
        if crop_dict_node:
            break

# Evaluate the dictionary
import ast
crop_profiles = ast.literal_eval(crop_dict_node)

rich_data = {
    "Mango": {
        "steps": [
            {"title": "Pit Preparation", "desc": "Dig 1x1x1m pits and expose to sun.", "why": "Sun exposure kills harmful soil-borne pathogens and pests before planting."},
            {"title": "Planting", "desc": "Plant grafts in the center of the pit.", "why": "Grafts ensure the plant inherits the exact fruit quality of the parent tree, unlike seeds."},
            {"title": "Irrigation", "desc": "Water regularly for first 3 years.", "why": "Young saplings have shallow roots and cannot survive dry spells without consistent moisture."},
            {"title": "Harvesting", "desc": "Pluck fruits with a stalk to avoid sap burn.", "why": "Mango sap is highly acidic; if it drips onto the skin of the fruit, it causes black lesions that cause rotting."}
        ],
        "challenges": [
            {"issue": "Fruit flies", "solution": "Use pheromone traps and apply neem oil spray as a natural deterrent."},
            {"issue": "Powdery mildew fungus", "solution": "Spray wettable sulfur at the first sign of white powdery spots on leaves."},
            {"issue": "Alternate bearing", "solution": "Apply Paclobutrazol (a plant growth regulator) to the soil to encourage regular flowering."}
        ],
        "soil_tips": "Grow leguminous intercrops (like cowpea) between rows for the first 4 years to naturally fix nitrogen into the soil."
    },
    "Wheat": {
        "steps": [
            {"title": "Field Prep", "desc": "Plough the field 2-3 times to get fine tilth.", "why": "A fine seedbed ensures maximum seed-to-soil contact for uniform germination."},
            {"title": "Sowing", "desc": "Drill seeds at a depth of 4-5 cm.", "why": "Sowing too deep prevents the shoot from reaching the surface; too shallow exposes seeds to birds."},
            {"title": "Irrigation", "desc": "Provide 4-6 irrigations at critical stages.", "why": "The Crown Root Initiation (CRI) stage is highly water-sensitive; stress here drastically reduces yield."},
            {"title": "Harvesting", "desc": "Cut when grains become hard and moisture is < 15%.", "why": "Harvesting with high moisture leads to fungal growth during storage."}
        ],
        "challenges": [
            {"issue": "Termites", "solution": "Treat seeds with chlorpyrifos before sowing and ensure the field is well-irrigated."},
            {"issue": "Yellow rust disease", "solution": "Grow rust-resistant varieties and spray propiconazole if yellow stripes appear on leaves."},
            {"issue": "Heat stress during grain filling", "solution": "Maintain adequate soil moisture during the late growth stages to cool the microclimate."}
        ],
        "soil_tips": "Incorporate wheat stubble back into the soil instead of burning it; this builds soil organic carbon."
    },
    "Paddy": {
        "steps": [
            {"title": "Nursery", "desc": "Grow seedlings for 20-30 days.", "why": "Raising seedlings in a controlled area allows for rigorous weed and pest management early on."},
            {"title": "Transplanting", "desc": "Plant seedlings in puddled fields.", "why": "Puddling destroys soil structure to create a hardpan, preventing water from draining away."},
            {"title": "Water Management", "desc": "Maintain 2-5 cm of standing water.", "why": "Standing water suppresses weed growth because most terrestrial weeds cannot survive submerged."},
            {"title": "Harvesting", "desc": "Drain water 15 days before harvest.", "why": "Drying the field hardens the soil, making it easier for labor or machinery to operate."}
        ],
        "challenges": [
            {"issue": "Stem borers", "solution": "Use trichogramma (a beneficial wasp) egg cards in the field as a biological control."},
            {"issue": "Bacterial leaf blight", "solution": "Avoid excess nitrogen application and drain the field temporarily to stop the spread."},
            {"issue": "High methane emissions", "solution": "Practice Alternate Wetting and Drying (AWD) instead of continuous flooding."}
        ],
        "soil_tips": "Practice crop rotation with pulses (like Gram) after paddy to naturally break the hardpan and restore nitrogen."
    }
}

def get_generic_data(crop_name):
    return {
        "steps": [
            {"title": "Seed/Land Prep", "desc": f"Prepare the land specifically for {crop_name}.", "why": "Proper land preparation provides aeration to the roots and kills early weeds."},
            {"title": "Sowing & Care", "desc": f"Sow the seeds at the correct depth and spacing.", "why": "Optimal spacing prevents plants from competing with each other for sunlight and nutrients."},
            {"title": "Irrigation", "desc": "Water at critical growth stages.", "why": "Water acts as the transport system carrying soil nutrients up into the plant tissues."},
            {"title": "Harvesting", "desc": f"Harvest {crop_name} at peak maturity.", "why": "Harvesting at the right time maximizes nutritional value and market shelf-life."}
        ],
        "challenges": [
            {"issue": "Local pests and insects", "solution": "Regularly scout the field and use integrated pest management (IPM) techniques like neem oil."},
            {"issue": "Unpredictable weather patterns", "solution": "Ensure good drainage to prevent waterlogging, and mulch the soil to retain moisture during droughts."},
            {"issue": "Weed competition", "solution": "Perform manual weeding during the first 30-45 days, which is the critical weed-free period."}
        ],
        "soil_tips": "Use organic compost and practice crop rotation to maintain soil health and microbiome diversity."
    }

# Fix the dictionary!
for crop, details in crop_profiles.items():
    # Remove old junk if it exists
    if "farm_school_steps" in details:
        del details["farm_school_steps"]
    if "fertilizers" in details:
        del details["fertilizers"]
    
    # Assign fresh data
    details["farm_school"] = rich_data.get(crop, get_generic_data(crop))

# Now we need to write it back.
import pprint
formatted_dict = pprint.pformat(crop_profiles, indent=4, sort_dicts=False)

# Replace the old dict with the new one.
# We'll find where `crop_profiles = {` starts and where it ends.
# A simple way is to use ast.unparse, but since we want to preserve other code, we can string replace.
import re
new_code = re.sub(r'crop_profiles\s*=\s*\{.*?\n(?:    "[A-Za-z]+".*?\n)+\s*\}', f'crop_profiles = {formatted_dict}', code, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_code)

print("Repaired crop_profiles dictionary in app.py")

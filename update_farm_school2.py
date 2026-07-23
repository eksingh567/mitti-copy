import re
import json
import ast

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Define the new rich data with solutions for challenges and without fertilizers
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
            {"issue": "Alternate bearing (heavy yield one year, light the next)", "solution": "Apply Paclobutrazol (a plant growth regulator) to the soil to encourage regular flowering."}
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

# A generic fallback generator for crops not explicitly detailed above
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

pattern = r'("' + r'([a-zA-Z]+)' + r'": \{[^}]*?)(?=\})'

def repl(m):
    crop_name = m.group(2)
    # Remove the old farm_school_steps and farm_school if they exist
    content = m.group(1)
    content = re.sub(r', "farm_school_steps": \[.*?\]', '', content)
    content = re.sub(r', "farm_school": \{.*?\}', '', content)
    
    # Get the rich data
    data = rich_data.get(crop_name, get_generic_data(crop_name))
    
    # Inject it as a JSON string
    data_str = json.dumps(data)
    return content + f', "farm_school": {data_str}'

code = re.sub(pattern, repl, code)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated app.py with clickable challenges and removed nutrients.")

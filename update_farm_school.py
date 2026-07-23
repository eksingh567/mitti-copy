import re
import json

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Define rich farm school data for the crops
# To save space and time, I'll provide detailed data for a few key crops and a generic but rich template for the rest, 
# then scale it out.

rich_data = {
    "Mango": {
        "steps": [
            {"title": "Pit Preparation", "desc": "Dig 1x1x1m pits and expose to sun.", "why": "Sun exposure kills harmful soil-borne pathogens and pests before planting."},
            {"title": "Planting", "desc": "Plant grafts in the center of the pit.", "why": "Grafts ensure the plant inherits the exact fruit quality of the parent tree, unlike seeds."},
            {"title": "Irrigation", "desc": "Water regularly for first 3 years.", "why": "Young saplings have shallow roots and cannot survive dry spells without consistent moisture."},
            {"title": "Harvesting", "desc": "Pluck fruits with a stalk to avoid sap burn.", "why": "Mango sap is highly acidic; if it drips onto the skin of the fruit, it causes black lesions that cause rotting."}
        ],
        "challenges": ["Fruit flies", "Powdery mildew fungus", "Alternate bearing (yielding heavy one year, light the next)"],
        "fertilizers": "Requires balanced NPK. Apply heavy Potassium (K) during the flowering stage to improve fruit size.",
        "soil_tips": "Grow leguminous intercrops (like cowpea) between rows for the first 4 years to naturally fix nitrogen into the soil."
    },
    "Wheat": {
        "steps": [
            {"title": "Field Prep", "desc": "Plough the field 2-3 times to get fine tilth.", "why": "A fine seedbed ensures maximum seed-to-soil contact for uniform germination."},
            {"title": "Sowing", "desc": "Drill seeds at a depth of 4-5 cm.", "why": "Sowing too deep prevents the shoot from reaching the surface; too shallow exposes seeds to birds."},
            {"title": "Irrigation", "desc": "Provide 4-6 irrigations at critical stages.", "why": "The Crown Root Initiation (CRI) stage is highly water-sensitive; stress here drastically reduces yield."},
            {"title": "Harvesting", "desc": "Cut when grains become hard and moisture is < 15%.", "why": "Harvesting with high moisture leads to fungal growth during storage."}
        ],
        "challenges": ["Termites", "Yellow rust disease", "Heat stress during grain filling"],
        "fertilizers": "High Nitrogen requirement. Apply N in two splits to prevent leaching losses.",
        "soil_tips": "Incorporate wheat stubble back into the soil instead of burning it; this builds soil organic carbon."
    },
    "Paddy": {
        "steps": [
            {"title": "Nursery", "desc": "Grow seedlings for 20-30 days.", "why": "Raising seedlings in a controlled area allows for rigorous weed and pest management early on."},
            {"title": "Transplanting", "desc": "Plant seedlings in puddled fields.", "why": "Puddling destroys soil structure to create a hardpan, preventing water from draining away."},
            {"title": "Water Management", "desc": "Maintain 2-5 cm of standing water.", "why": "Standing water suppresses weed growth because most terrestrial weeds cannot survive submerged."},
            {"title": "Harvesting", "desc": "Drain water 15 days before harvest.", "why": "Drying the field hardens the soil, making it easier for labor or machinery to operate."}
        ],
        "challenges": ["Stem borers", "Bacterial leaf blight", "High methane emissions"],
        "fertilizers": "Apply Zinc sulphate if leaves show brown spots. Use urea briquettes for slow nitrogen release.",
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
        "challenges": ["Local pests and insects", "Unpredictable weather patterns", "Weed competition"],
        "fertilizers": "Use a balanced NPK fertilizer based on a recent soil test.",
        "soil_tips": "Use organic compost and practice crop rotation to maintain soil health and microbiome diversity."
    }

# Read the file and inject the new data
pattern = r'("' + r'([a-zA-Z]+)' + r'": \{[^}]*?)(?=\})'

def repl(m):
    crop_name = m.group(2)
    # Remove the old farm_school_steps if it exists
    content = m.group(1)
    content = re.sub(r', "farm_school_steps": \[.*?\]', '', content)
    
    # Get the rich data
    data = rich_data.get(crop_name, get_generic_data(crop_name))
    
    # Inject it as a JSON string
    data_str = json.dumps(data)
    return content + f', "farm_school": {data_str}'

code = re.sub(pattern, repl, code)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Rich Farm School data injected.")

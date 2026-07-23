import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Define the new data for each crop
extensions = {
    "Mango": {"sowing_months": ["Jul", "Aug"], "harvest_months": ["Apr", "May", "Jun"], "farm_school_steps": ["1. Pit Preparation: Dig 1x1x1m pits and expose to sun.", "2. Planting: Plant grafts in the center of the pit.", "3. Irrigation: Water regularly for first 3 years.", "4. Harvesting: Pluck fruits with a stalk to avoid sap burn."]},
    "Wheat": {"sowing_months": ["Oct", "Nov"], "harvest_months": ["Mar", "Apr"], "farm_school_steps": ["1. Field Prep: Plough the field 2-3 times to get fine tilth.", "2. Sowing: Drill seeds at a depth of 4-5 cm.", "3. Irrigation: Provide 4-6 irrigations at critical stages.", "4. Harvesting: Cut when grains become hard and moisture is < 15%."]},
    "Paddy": {"sowing_months": ["Jun", "Jul"], "harvest_months": ["Nov", "Dec"], "farm_school_steps": ["1. Nursery: Grow seedlings for 20-30 days.", "2. Transplanting: Plant seedlings in puddled fields.", "3. Water Management: Maintain 2-5 cm of standing water.", "4. Harvesting: Drain water 15 days before harvest."]},
    "Cotton": {"sowing_months": ["May", "Jun"], "harvest_months": ["Oct", "Nov", "Dec"], "farm_school_steps": ["1. Sowing: Dibble seeds keeping 90x60 cm spacing.", "2. Weed Control: Keep field weed-free for first 60 days.", "3. Irrigation: Avoid waterlogging but maintain moisture.", "4. Picking: Hand-pick open bolls in the morning."]},
    "Mustard": {"sowing_months": ["Oct", "Nov"], "harvest_months": ["Feb", "Mar"], "farm_school_steps": ["1. Sowing: Sow seeds in lines 30 cm apart.", "2. Thinning: Maintain plant-to-plant distance of 10-15 cm.", "3. Irrigation: Provide first irrigation at 35-40 days.", "4. Harvesting: Harvest when 75% of pods turn yellow."]},
    "Maize": {"sowing_months": ["Jun", "Jul"], "harvest_months": ["Sep", "Oct"], "farm_school_steps": ["1. Sowing: Sow on ridges to avoid waterlogging.", "2. Fertilizer: Apply Nitrogen in 3 splits.", "3. Irrigation: Crucial at tasseling and silking stages.", "4. Harvesting: Harvest when husks turn dry and brown."]},
    "Potato": {"sowing_months": ["Oct", "Nov"], "harvest_months": ["Feb", "Mar"], "farm_school_steps": ["1. Seed Prep: Cut tubers keeping 2-3 eyes per piece.", "2. Planting: Plant on ridges 60 cm apart.", "3. Earthing Up: Crucial to cover exposed tubers from sun.", "4. Harvesting: Dig out tubers when haulms dry."]},
    "Sugarcane": {"sowing_months": ["Jan", "Feb", "Mar"], "harvest_months": ["Dec", "Jan", "Feb"], "farm_school_steps": ["1. Planting: Plant 2-3 budded setts in trenches.", "2. Irrigation: Requires frequent irrigation (30+ times).", "3. Tying: Tie canes together to prevent lodging.", "4. Harvesting: Cut close to ground level for better ratoon."]},
    "Jute": {"sowing_months": ["Feb", "Mar"], "harvest_months": ["Jul", "Aug"], "farm_school_steps": ["1. Sowing: Broadcast seeds in finely prepared soil.", "2. Weeding: Hand weeding is essential.", "3. Harvesting: Cut close to ground level.", "4. Retting: Steep in clean water to extract fibers."]},
    "Tea": {"sowing_months": ["Oct", "Nov"], "harvest_months": ["Mar", "Apr", "May", "Jun", "Jul"], "farm_school_steps": ["1. Nursery: Raise cuttings in sleeves.", "2. Planting: Plant on contoured slopes.", "3. Pruning: Essential to maintain bush frame.", "4. Plucking: Hand-pluck 'two leaves and a bud'."]},
    "Coffee": {"sowing_months": ["Aug", "Sep"], "harvest_months": ["Nov", "Dec", "Jan"], "farm_school_steps": ["1. Planting: Plant under shade trees (e.g. Silver Oak).", "2. Pruning: Remove dead wood and manage canopy.", "3. Irrigation: Blossom showers are critical.", "4. Picking: Selectively hand-pick ripe red cherries."]},
    "Rubber": {"sowing_months": ["Jun", "Jul"], "harvest_months": ["Sep", "Oct", "Nov"], "farm_school_steps": ["1. Planting: Plant budded stumps in pits.", "2. Upkeep: Grow leguminous cover crops.", "3. Tapping: Start tapping when girth reaches 50cm.", "4. Processing: Coagulate latex into sheets."]},
    "Groundnut": {"sowing_months": ["Jun", "Jul"], "harvest_months": ["Oct", "Nov"], "farm_school_steps": ["1. Sowing: Treat seeds with Rhizobium before sowing.", "2. Earthing Up: Do not disturb soil during peg penetration.", "3. Irrigation: Crucial at flowering and pod development.", "4. Harvesting: Dig plants when pods have dark inner shells."]},
    "Soybean": {"sowing_months": ["Jun", "Jul"], "harvest_months": ["Sep", "Oct"], "farm_school_steps": ["1. Sowing: Sow on raised beds for drainage.", "2. Weed Control: Keep field clean for first 45 days.", "3. Irrigation: Essential at pod filling stage.", "4. Harvesting: Harvest when leaves turn yellow and drop."]},
    "Turmeric": {"sowing_months": ["May", "Jun"], "harvest_months": ["Jan", "Feb", "Mar"], "farm_school_steps": ["1. Planting: Plant rhizome pieces on ridges/beds.", "2. Mulching: Cover soil with green leaves to retain moisture.", "3. Earthing Up: Done at 45 and 90 days.", "4. Harvesting: Dig when leaves dry up completely."]},
    "Cumin": {"sowing_months": ["Nov", "Dec"], "harvest_months": ["Feb", "Mar"], "farm_school_steps": ["1. Sowing: Broadcast seeds in well-prepared beds.", "2. Weed Control: Highly sensitive to weed competition.", "3. Irrigation: Light and frequent irrigation.", "4. Harvesting: Uproot plants when seeds turn brown."]},
    "Coriander": {"sowing_months": ["Oct", "Nov"], "harvest_months": ["Feb", "Mar"], "farm_school_steps": ["1. Sowing: Rub seeds to split into two halves before sowing.", "2. Irrigation: Needs 3-4 irrigations.", "3. Frost Protection: Protect from frost at flowering.", "4. Harvesting: Harvest when 50% umbels turn yellow."]},
    "Cardamom": {"sowing_months": ["Jun", "Jul"], "harvest_months": ["Aug", "Sep", "Oct"], "farm_school_steps": ["1. Planting: Plant suckers in pits under forest canopy.", "2. Mulching: Conserve soil moisture.", "3. Irrigation: Essential during dry months.", "4. Harvesting: Hand-pick mature green capsules."]},
    "BlackPepper": {"sowing_months": ["Jun", "Jul"], "harvest_months": ["Dec", "Jan"], "farm_school_steps": ["1. Planting: Plant rooted cuttings near support trees (standards).", "2. Tying: Tie the growing vine to the standard.", "3. Pruning: Regulate shade of standard tree.", "4. Harvesting: Pluck spikes when 1-2 berries turn red."]},
    "Coconut": {"sowing_months": ["May", "Jun"], "harvest_months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], "farm_school_steps": ["1. Planting: Plant robust seedlings in deep pits.", "2. Manuring: Apply in circular basins around the palm.", "3. Irrigation: Drip irrigation saves water and boosts yield.", "4. Harvesting: Harvest mature nuts every 45-60 days."]},
    "Bajra": {"sowing_months": ["Jun", "Jul"], "harvest_months": ["Sep", "Oct"], "farm_school_steps": ["1. Sowing: Highly drought-tolerant; shallow sowing (2-3cm).", "2. Thinning: Maintain optimal plant population.", "3. Irrigation: Usually rainfed.", "4. Harvesting: Cut earheads when grains are hard."]},
    "Jowar": {"sowing_months": ["Jun", "Jul"], "harvest_months": ["Oct", "Nov"], "farm_school_steps": ["1. Sowing: Treat seeds for shoot fly protection.", "2. Fertilizer: Responds well to Nitrogen.", "3. Irrigation: Give life-saving irrigation if needed.", "4. Harvesting: Harvest when grains have 20% moisture."]},
    "Gram": {"sowing_months": ["Oct", "Nov"], "harvest_months": ["Feb", "Mar"], "farm_school_steps": ["1. Sowing: Deep sowing ensures good germination on residual moisture.", "2. Nipping: Pluck apical buds to encourage branching.", "3. Irrigation: Usually grown rainfed.", "4. Harvesting: Harvest when leaves turn reddish-brown."]},
    "Tur": {"sowing_months": ["Jun", "Jul"], "harvest_months": ["Dec", "Jan"], "farm_school_steps": ["1. Sowing: Deep rooted, requires deep ploughing.", "2. Intercropping: Often intercropped with cereals or groundnut.", "3. Weed Control: Critical in first 60 days.", "4. Harvesting: Cut plants when 80% pods turn brown."]},
    "Onion": {"sowing_months": ["Oct", "Nov"], "harvest_months": ["Feb", "Mar"], "farm_school_steps": ["1. Nursery: Raise seedlings for 6-8 weeks.", "2. Transplanting: Plant seedlings closely.", "3. Irrigation: Frequent light irrigation; stop 15 days before harvest.", "4. Curing: Dry harvested bulbs in shade for a few days."]},
    "Tomato": {"sowing_months": ["Jun", "Jul", "Jan", "Feb"], "harvest_months": ["Sep", "Oct", "Apr", "May"], "farm_school_steps": ["1. Nursery: Transplant 25-30 day old seedlings.", "2. Staking: Provide support to prevent fruits touching ground.", "3. Irrigation: Maintain uniform moisture to prevent fruit cracking.", "4. Harvesting: Pick at breaker or pink stage for market."]}
}

# Use regex to find the dictionary and inject the new fields
for crop, ext in extensions.items():
    # Construct the python dict string representation of the new fields
    ext_str = f', "sowing_months": {ext["sowing_months"]}, "harvest_months": {ext["harvest_months"]}, "farm_school_steps": {ext["farm_school_steps"]}'
    
    # Replace the crop definition line by finding the exact match
    pattern = r'("' + crop + r'": \{[^}]*?)(?=\})'
    def repl(m):
        if "sowing_months" in m.group(1):
            return m.group(1) # Already injected
        return m.group(1) + ext_str
        
    code = re.sub(pattern, repl, code)

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Crop profiles extended.")

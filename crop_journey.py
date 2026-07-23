"""
Crop Journey Generator
Generates a day-by-day/week-by-week task schedule from sowing to harvest for each crop.
Each task includes: WHAT, WHEN (day range), WHY, HOW.
"""

crop_journeys = {
    "Wheat": {
        "total_days": 150,
        "phases": [
            {
                "name": "Land Preparation",
                "day_start": 1, "day_end": 7,
                "tasks": [
                    {"day": 1, "what": "Plough the field 2-3 times", "why": "Breaking the soil clods ensures better root penetration and kills dormant weed seeds.", "how": "Use a tractor-mounted disc plough. Cross-plough on the second pass for fine tilth."},
                    {"day": 3, "what": "Apply farmyard manure (FYM)", "why": "FYM enriches the soil with organic carbon and beneficial microbes before sowing.", "how": "Spread 10-12 tonnes/hectare evenly across the field and mix with a cultivator."},
                    {"day": 5, "what": "Level the field with a laser leveler", "why": "An uneven field causes waterlogging in low spots and drought stress in high spots.", "how": "Use a tractor-mounted laser leveler. Ensure the gradient is less than 0.1%."},
                    {"day": 7, "what": "Create irrigation channels", "why": "Pre-built channels ensure water reaches every part of the field uniformly during the first irrigation.", "how": "Dig channels at 3-meter intervals using a ridger attachment."}
                ]
            },
            {
                "name": "Seed Treatment & Sowing",
                "day_start": 8, "day_end": 14,
                "tasks": [
                    {"day": 8, "what": "Treat seeds with fungicide (Thiram/Carbendazim)", "why": "Seed treatment prevents seed-borne diseases like smut and bunt that can destroy the entire crop.", "how": "Mix 2g Thiram per kg of seed. Shake in a closed container for 5 minutes until evenly coated."},
                    {"day": 10, "what": "Sow seeds using a seed drill at 4-5cm depth", "why": "Precise depth ensures uniform germination. Too shallow = birds eat seeds. Too deep = weak emergence.", "how": "Use a seed drill set to 20cm row spacing. Seed rate: 100-125 kg/hectare."},
                    {"day": 12, "what": "Apply pre-emergence herbicide (Pendimethalin)", "why": "Stops weeds from germinating alongside your crop during the critical first 30 days.", "how": "Spray 1 litre/hectare mixed in 500L water using a knapsack sprayer within 48 hours of sowing."},
                    {"day": 14, "what": "Give the first light irrigation", "why": "Moisture triggers germination. Without it, seeds will remain dormant and rot.", "how": "Flood irrigate gently. Avoid heavy flow that displaces seeds. Water should stand for 2-3 hours only."}
                ]
            },
            {
                "name": "Crown Root Initiation (CRI)",
                "day_start": 21, "day_end": 28,
                "tasks": [
                    {"day": 21, "what": "Check germination percentage", "why": "If germination is below 70%, you may need to re-sow gaps to maintain yield potential.", "how": "Count plants in 1 sq meter at 5 random spots. Average should be 200+ plants/sqm."},
                    {"day": 24, "what": "Apply first dose of urea (nitrogen)", "why": "The CRI stage is when crown roots form. Nitrogen deficiency here permanently reduces tillers and yield.", "how": "Broadcast 1/3 of total urea (40kg/hectare) evenly. Follow immediately with irrigation."},
                    {"day": 25, "what": "Irrigate immediately after urea application", "why": "Urea volatilizes (turns to gas) within hours if not watered in. You would lose 40% of the fertilizer.", "how": "Flood irrigate within 6 hours of urea application. Ensure uniform coverage."},
                    {"day": 28, "what": "Scout for yellow rust spots on leaves", "why": "Yellow rust is the most devastating wheat disease. Early detection saves the crop.", "how": "Walk through the field and check the undersides of leaves. Look for yellow-orange pustules in stripes."}
                ]
            },
            {
                "name": "Tillering & Growth",
                "day_start": 30, "day_end": 60,
                "tasks": [
                    {"day": 30, "what": "Manual weeding or post-emergence herbicide", "why": "Weeds compete directly with wheat for nutrients and sunlight. The first 45 days are critical.", "how": "If manual: pull weeds by hand. If chemical: spray 2,4-D at 0.5 litre/hectare."},
                    {"day": 40, "what": "Apply second dose of urea", "why": "The second split of nitrogen fuels tiller growth. More tillers = more grain-bearing heads.", "how": "Broadcast remaining 2/3 urea (80kg/hectare). Irrigate within 6 hours."},
                    {"day": 45, "what": "Second irrigation", "why": "Adequate moisture during tillering directly determines the number of productive tillers.", "how": "Flood irrigate. Allow water to soak for 4-5 hours."},
                    {"day": 55, "what": "Scout for aphids and termites", "why": "Aphid colonies can build up rapidly in cool weather and suck the sap out of young tillers.", "how": "Check leaf undersides and stem bases. If found, spray Imidacloprid at 0.5ml/litre water."}
                ]
            },
            {
                "name": "Heading & Flowering",
                "day_start": 60, "day_end": 90,
                "tasks": [
                    {"day": 65, "what": "Third irrigation at boot/heading stage", "why": "Water stress during heading causes empty spikelets — grain numbers are decided NOW.", "how": "Ensure the field is saturated. This is one of the most critical irrigations."},
                    {"day": 70, "what": "Spray micronutrient foliar (Zinc Sulphate)", "why": "Zinc deficiency during flowering causes poor grain filling and small, shriveled grains.", "how": "Dissolve 5g ZnSO4 per litre water. Spray on leaves in the early morning or late evening."},
                    {"day": 80, "what": "Fourth irrigation at grain filling", "why": "The grain is physically filling with starch now. Water shortage means lighter, smaller grains.", "how": "Light flood irrigation. Avoid waterlogging which can cause root rot at this stage."},
                    {"day": 85, "what": "Watch for heat stress signs", "why": "Sudden heat waves during grain filling can cause forced maturity — the grain dries out prematurely.", "how": "If temp exceeds 35°C, give a light sprinkler irrigation in the afternoon to cool the microclimate."}
                ]
            },
            {
                "name": "Maturity & Harvest",
                "day_start": 120, "day_end": 150,
                "tasks": [
                    {"day": 120, "what": "Stop all irrigation", "why": "Continuing irrigation now will delay maturity and increase the risk of lodging (plants falling over).", "how": "Simply stop watering. Let the field dry naturally."},
                    {"day": 130, "what": "Test grain moisture with a bite test", "why": "Harvesting too early (high moisture) causes fungal growth in storage. Too late causes shattering losses.", "how": "Bite a grain. If it cracks cleanly and is hard, moisture is ~12-14%. Ready to harvest."},
                    {"day": 140, "what": "Harvest with a combine harvester", "why": "Delayed harvest beyond optimal maturity causes the grains to shatter and fall, losing up to 10% yield.", "how": "Set combine height to 15cm. Harvest in early morning when grains are slightly moist to reduce shattering."},
                    {"day": 145, "what": "Dry grains to <12% moisture for storage", "why": "Grain above 14% moisture develops fungus (aflatoxins) in storage, making it toxic and unsellable.", "how": "Spread grains 2-3 inches thick on a tarpaulin in direct sun for 2-3 days. Turn every few hours."}
                ]
            }
        ]
    },
    "Paddy": {
        "total_days": 140,
        "phases": [
            {
                "name": "Nursery Preparation",
                "day_start": 1, "day_end": 10,
                "tasks": [
                    {"day": 1, "what": "Select and soak seeds in water for 24 hours", "why": "Soaking softens the seed coat and kick-starts germination, ensuring all seeds sprout together.", "how": "Use clean water. Add 1g Carbendazim per litre to prevent seed-borne diseases."},
                    {"day": 2, "what": "Incubate soaked seeds in a gunny bag for 48 hours", "why": "Warm, moist conditions inside the bag cause the seeds to sprout (chitting), giving them a head start.", "how": "Drain water, wrap in a moist gunny bag. Keep in shade. Sprinkle water every 12 hours."},
                    {"day": 4, "what": "Prepare the nursery bed", "why": "A dedicated nursery bed allows you to grow 1000+ seedlings per sqm in a small, manageable area.", "how": "Make raised beds 1m wide, any length. Mix 5kg FYM per sqm. Level perfectly."},
                    {"day": 5, "what": "Broadcast sprouted seeds on the nursery bed", "why": "Even distribution prevents overcrowding, which causes weak, etiolated seedlings.", "how": "Scatter 40g sprouted seed per sqm. Cover lightly with a thin layer of soil. Irrigate gently."}
                ]
            },
            {
                "name": "Main Field Preparation",
                "day_start": 15, "day_end": 25,
                "tasks": [
                    {"day": 15, "what": "Plough and puddle the main field", "why": "Puddling destroys soil aggregates to create an impermeable layer that holds standing water for paddy.", "how": "Flood the field with 5cm water, then use a rotavator or country plough to churn the soil."},
                    {"day": 18, "what": "Level the puddled field", "why": "Uneven fields cause unequal water depth — too deep drowns seedlings, too shallow allows weeds.", "how": "Use a wooden plank (leveling board) dragged behind a tractor or bullock."},
                    {"day": 20, "what": "Apply basal fertilizer (DAP + MoP)", "why": "Phosphorus and potassium must be placed in the root zone before transplanting for early root development.", "how": "Broadcast 60kg DAP + 40kg MoP per hectare. Incorporate into puddled soil."},
                    {"day": 25, "what": "Transplant 21-day old seedlings", "why": "Seedlings older than 25 days lose their transplanting vigor and take longer to establish.", "how": "Plant 2-3 seedlings per hill at 20x15cm spacing. Push roots 2-3cm into the puddled soil."}
                ]
            },
            {
                "name": "Vegetative Growth",
                "day_start": 26, "day_end": 60,
                "tasks": [
                    {"day": 30, "what": "Apply first urea top-dressing", "why": "Nitrogen drives leaf and tiller production. Deficiency now means fewer grain-bearing tillers.", "how": "Broadcast 40kg urea/hectare. Maintain 3-5cm standing water to prevent nitrogen loss."},
                    {"day": 35, "what": "Hand-weed or apply Butachlor herbicide", "why": "Weeds in paddy compete for light and nutrients. They can reduce yield by 30-50% if uncontrolled.", "how": "If manual: weed between rows. If chemical: apply Butachlor granules into standing water."},
                    {"day": 45, "what": "Apply second urea top-dressing", "why": "This split maximizes nitrogen use efficiency. A single large dose would wash away in standing water.", "how": "Broadcast 40kg urea/hectare. Drain excess water to 2cm before application for better absorption."},
                    {"day": 50, "what": "Scout for stem borers and leaf folders", "why": "Stem borers hollow out the stem causing 'dead hearts' — the central shoot dies and produces no grain.", "how": "Look for dead hearts. If found, release Trichogramma egg cards (1 card/hectare) as biocontrol."}
                ]
            },
            {
                "name": "Flowering & Grain Filling",
                "day_start": 60, "day_end": 100,
                "tasks": [
                    {"day": 65, "what": "Maintain 5cm standing water during flowering", "why": "Water stress during flowering causes spikelet sterility — the grains form but remain empty.", "how": "Check water level daily. Top up as needed."},
                    {"day": 75, "what": "Spray potassium chloride foliar feed", "why": "Potassium strengthens the grain filling process and improves grain weight and quality.", "how": "Dissolve 10g KCl per litre water. Spray on leaves in the evening."},
                    {"day": 85, "what": "Watch for blast disease", "why": "Neck blast at flowering can destroy the entire panicle, causing total grain loss.", "how": "Look for diamond-shaped brown spots on leaves. If found, spray Tricyclazole at 0.6g/litre."},
                    {"day": 95, "what": "Begin draining the field", "why": "Gradual drainage hardens the soil for harvest and forces the plant to redirect energy into grain filling.", "how": "Open field outlets. Allow water to drain over 5-7 days."}
                ]
            },
            {
                "name": "Harvest & Post-Harvest",
                "day_start": 110, "day_end": 140,
                "tasks": [
                    {"day": 115, "what": "Check grain maturity (80% straw-colored panicles)", "why": "Harvesting too early gives immature, chalky grains. Too late causes shattering and bird damage.", "how": "When 80% of panicles turn golden-straw colored, the crop is ready."},
                    {"day": 120, "what": "Harvest the crop", "why": "Delayed harvest beyond optimal maturity causes grain shattering losses of 3-5% per day.", "how": "Use a combine harvester or manual sickle cutting. Cut at 15cm above ground."},
                    {"day": 125, "what": "Thresh and clean the grain", "why": "Separating grain from straw quickly prevents moisture re-absorption and pest infestation.", "how": "Use a mechanical thresher. Winnow to remove chaff and broken grains."},
                    {"day": 130, "what": "Sun-dry to 14% moisture and store", "why": "Grain stored above 14% moisture develops aflatoxin fungus within weeks.", "how": "Spread on a clean surface in sun for 2-3 days. Store in jute bags in a ventilated room."}
                ]
            }
        ]
    },
    "Mango": {
        "total_days": 365,
        "phases": [
            {
                "name": "Pre-Flowering Care",
                "day_start": 1, "day_end": 30,
                "tasks": [
                    {"day": 1, "what": "Prune dead and diseased branches", "why": "Pruning opens up the canopy for sunlight and air, reducing fungal disease pressure.", "how": "Use clean secateurs. Cut branches at a 45° angle. Apply Bordeaux paste on large cuts."},
                    {"day": 7, "what": "Apply basal dose of organic manure", "why": "Mango trees are heavy feeders. Organic matter provides slow-release nutrients throughout the season.", "how": "Dig a ring trench 1m from the trunk. Fill with 20-25kg FYM per tree. Cover with soil."},
                    {"day": 15, "what": "Spray 2% KNO3 to induce flowering", "why": "Potassium nitrate tricks the tree into thinking winter stress is over, triggering flower bud differentiation.", "how": "Dissolve 20g KNO3 per litre water. Spray thoroughly on all branches."},
                    {"day": 25, "what": "Whitewash the trunk with lime", "why": "Whitewash reflects heat and prevents bark splitting. It also deters trunk borers.", "how": "Mix 1kg lime in 5L water. Paint the trunk from ground level to the first branch."}
                ]
            },
            {
                "name": "Flowering & Fruit Set",
                "day_start": 30, "day_end": 90,
                "tasks": [
                    {"day": 35, "what": "Spray insecticide for mango hopper", "why": "Mango hoppers suck sap from flowers, causing them to dry and drop. They can destroy 100% of flowers.", "how": "Spray Imidacloprid (0.3ml/L) at first sign of hopper nymphs on flower panicles."},
                    {"day": 45, "what": "Spray fungicide for powdery mildew", "why": "White powdery coating on flowers prevents pollination. No pollination = no fruit.", "how": "Spray wettable Sulphur (2g/L) or Hexaconazole (1ml/L). Repeat after 15 days if needed."},
                    {"day": 60, "what": "Install pheromone traps for fruit fly", "why": "Fruit flies lay eggs inside developing fruits. Larvae eat the pulp from inside.", "how": "Hang methyl eugenol traps (10 per hectare) at canopy height. Replace every 3 weeks."},
                    {"day": 75, "what": "Irrigate if no rain for 15+ days", "why": "Water stress during fruit development causes premature fruit drop.", "how": "Drip irrigate or basin irrigate. Avoid flooding which causes root rot in mango."}
                ]
            },
            {
                "name": "Fruit Development & Harvest",
                "day_start": 90, "day_end": 180,
                "tasks": [
                    {"day": 100, "what": "Thin excess fruits if needed", "why": "Too many fruits per panicle results in all fruits being small. Thinning lets remaining fruits grow large.", "how": "Remove deformed and very small fruits by hand. Leave 2-3 best fruits per panicle."},
                    {"day": 120, "what": "Apply potassium sulphate foliar spray", "why": "Potassium improves fruit sweetness, color development, and shelf life after harvest.", "how": "Dissolve 10g K2SO4 per litre. Spray on leaves and developing fruits."},
                    {"day": 150, "what": "Harvest fruits with 1cm stalk attached", "why": "Latex from a broken stalk drips onto fruit skin, causing black burn marks that reduce market value.", "how": "Use a mango harvesting net on a pole. Cut stalk with secateurs. Place fruits stalk-down on newspaper."},
                    {"day": 155, "what": "Ripen harvested mangoes in a dark room", "why": "Controlled ripening produces uniform color and flavor vs erratic sun-ripening.", "how": "Place in a closed room with ethylene-releasing banana bunches. Ripen in 5-7 days."}
                ]
            }
        ]
    }
}

# Generic journey for crops without a specific one
def get_generic_journey(crop_name, total_days=120):
    return {
        "total_days": total_days,
        "phases": [
            {
                "name": "Land Preparation & Sowing",
                "day_start": 1, "day_end": 14,
                "tasks": [
                    {"day": 1, "what": f"Prepare the field for {crop_name}", "why": "Proper land preparation ensures good soil aeration and weed control.", "how": "Plough 2-3 times. Level the field. Apply basal fertilizer."},
                    {"day": 7, "what": "Treat and sow seeds", "why": "Seed treatment prevents early diseases. Correct depth ensures uniform germination.", "how": "Treat with fungicide. Sow at recommended depth and spacing for your region."},
                    {"day": 10, "what": "First irrigation after sowing", "why": "Moisture triggers germination. Seeds will rot if soil stays dry for too long.", "how": "Light flood irrigation. Avoid heavy flow that displaces seeds."},
                    {"day": 14, "what": "Check germination and fill gaps", "why": "Gaps in the stand reduce yield per unit area.", "how": "Re-sow in bare patches using soaked seeds for faster emergence."}
                ]
            },
            {
                "name": "Vegetative Growth",
                "day_start": 15, "day_end": 50,
                "tasks": [
                    {"day": 20, "what": "First weeding", "why": "Weeds in the first 30-45 days compete most aggressively with the crop.", "how": "Manual weeding between rows or apply recommended herbicide."},
                    {"day": 30, "what": "Apply first dose of nitrogen fertilizer", "why": "Nitrogen drives vegetative growth. Deficiency leads to stunted, yellow plants.", "how": "Broadcast urea evenly. Irrigate within 6 hours to prevent volatilization."},
                    {"day": 40, "what": "Scout for pests and diseases", "why": "Early detection prevents small problems from becoming crop-destroying epidemics.", "how": "Walk through the field. Check 10 random plants. Look for discoloration, holes, wilting."},
                    {"day": 45, "what": "Second irrigation at critical growth stage", "why": "Water stress during active growth permanently reduces plant size and yield potential.", "how": "Flood irrigate. Allow water to stand for 3-4 hours."}
                ]
            },
            {
                "name": "Flowering & Grain Filling",
                "day_start": 50, "day_end": 90,
                "tasks": [
                    {"day": 55, "what": "Apply second dose of fertilizer", "why": "Plants need extra nutrients during flowering and fruit/grain development.", "how": "Apply recommended NPK mix. Irrigate afterwards."},
                    {"day": 65, "what": "Critical irrigation at flowering", "why": "Water stress during flowering causes flower drop and poor fruit/grain set.", "how": "Ensure the field has adequate moisture. This is the most sensitive stage."},
                    {"day": 75, "what": "Apply micronutrient foliar spray", "why": "Micronutrients like zinc and boron improve grain quality and filling.", "how": "Spray ZnSO4 solution on leaves in early morning or evening."},
                    {"day": 85, "what": "Monitor for late-season pests", "why": "Pod borers, fruit flies, and grain-sucking bugs attack during this stage.", "how": "Scout regularly. Apply targeted pesticide only if pest threshold is exceeded."}
                ]
            },
            {
                "name": "Maturity & Harvest",
                "day_start": 90, "day_end": total_days,
                "tasks": [
                    {"day": 95, "what": "Stop irrigation", "why": "Continued watering delays maturity and can cause lodging or fruit cracking.", "how": "Stop all irrigation. Let the field/plant dry naturally."},
                    {"day": int(total_days * 0.85), "what": "Test for maturity", "why": "Harvesting at optimal maturity maximizes nutritional value, taste, and market price.", "how": "Check crop-specific maturity indicators (color change, moisture test, etc.)."},
                    {"day": int(total_days * 0.9), "what": "Harvest the crop", "why": "Timely harvest prevents field losses from shattering, birds, or weather damage.", "how": "Use appropriate method (manual or mechanical) for your crop."},
                    {"day": int(total_days * 0.95), "what": "Dry and store properly", "why": "Proper post-harvest handling preserves quality and prevents storage losses.", "how": "Dry to safe moisture level. Store in clean, ventilated containers."}
                ]
            }
        ]
    }

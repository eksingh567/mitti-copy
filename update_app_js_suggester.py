import re

with open('frontend/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Replace the populatePlannerDropdown function
old_populate = """function populatePlannerDropdown() {
    const select = document.getElementById('planner-crop-select');
    if (!select) return;
    select.innerHTML = '<option value="">-- Select a Crop --</option>';
    for (const cropKey in plannerCropsData) {
        const crop = plannerCropsData[cropKey];
        const name = (typeof currentLang !== 'undefined' && currentLang === 'hi' && crop.name_hi) ? crop.name_hi : (crop.name_en || cropKey);
        select.innerHTML += `<option value="${cropKey}">${name}</option>`;
    }
}"""

new_populate = """
function filterPlannerCrops() {
    const seasonFilter = document.getElementById('planner-season-filter').value;
    const soilFilter = document.getElementById('planner-soil-filter').value;
    
    let matchedCrops = [];
    let fallbackCrops = [];
    
    for (const cropKey in plannerCropsData) {
        const crop = plannerCropsData[cropKey];
        let seasonMatch = (seasonFilter === 'All' || crop.season === seasonFilter);
        let soilMatch = (soilFilter === 'All' || (crop.soils && crop.soils.includes(soilFilter)));
        
        if (seasonMatch && soilMatch) {
            matchedCrops.push(cropKey);
        } else {
            fallbackCrops.push(cropKey);
        }
    }
    
    populatePlannerDropdown(matchedCrops, fallbackCrops, seasonFilter !== 'All' || soilFilter !== 'All');
}

function populatePlannerDropdown(matched = null, fallback = null, isFiltered = false) {
    const select = document.getElementById('planner-crop-select');
    if (!select) return;
    
    select.innerHTML = '';
    
    // If not manually filtered yet, just show all
    if (!matched) {
        matched = Object.keys(plannerCropsData);
        fallback = [];
    }
    
    if (matched.length > 0) {
        if (isFiltered) select.innerHTML += `<optgroup label="Highly Recommended">`;
        matched.forEach(cropKey => {
            const crop = plannerCropsData[cropKey];
            const name = (typeof currentLang !== 'undefined' && currentLang === 'hi' && crop.name_hi) ? crop.name_hi : (crop.name_en || cropKey);
            select.innerHTML += `<option value="${cropKey}">🌟 ${name}</option>`;
        });
        if (isFiltered) select.innerHTML += `</optgroup>`;
    } else {
        select.innerHTML = `<option value="">-- No perfect matches found --</option>`;
    }
    
    if (fallback.length > 0) {
        if (isFiltered) select.innerHTML += `<optgroup label="Other Crops (Suboptimal)">`;
        fallback.forEach(cropKey => {
            const crop = plannerCropsData[cropKey];
            const name = (typeof currentLang !== 'undefined' && currentLang === 'hi' && crop.name_hi) ? crop.name_hi : (crop.name_en || cropKey);
            select.innerHTML += `<option value="${cropKey}">${name}</option>`;
        });
        if (isFiltered) select.innerHTML += `</optgroup>`;
    }
    
    // Auto trigger the planner for the first available crop
    updatePlanner();
}
"""

js = js.replace(old_populate, new_populate)

with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(js)
    
print("app.js updated successfully with filterPlannerCrops")

js_code = """
// --- Planner Logic ---
let plannerCropsData = {};

async function fetchPlannerData() {
    try {
        const res = await fetch(`${API_URL}/crops`);
        plannerCropsData = await res.json();
        populatePlannerDropdown();
        detectNextSeason();
    } catch (e) {
        console.error('Error fetching planner data:', e);
    }
}

function populatePlannerDropdown() {
    const select = document.getElementById('planner-crop-select');
    if (!select) return;
    select.innerHTML = '<option value="">-- Select a Crop --</option>';
    for (const cropKey in plannerCropsData) {
        const crop = plannerCropsData[cropKey];
        const name = (typeof currentLang !== 'undefined' && currentLang === 'hi' && crop.name_hi) ? crop.name_hi : (crop.name_en || cropKey);
        select.innerHTML += `<option value="${cropKey}">${name}</option>`;
    }
}

function updatePlanner() {
    const select = document.getElementById('planner-crop-select');
    const cropKey = select.value;
    if (!cropKey || !plannerCropsData[cropKey]) {
        clearPlanner();
        return;
    }
    
    const crop = plannerCropsData[cropKey];
    
    // 1. Render Timeline
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const sowing = crop.sowing_months || [];
    const harvesting = crop.harvest_months || [];
    
    const grid = document.getElementById('timelineGrid');
    if (grid) {
        grid.innerHTML = '';
        months.forEach(m => {
            let classes = 'timeline-month';
            if (sowing.includes(m)) classes += ' sowing';
            if (harvesting.includes(m)) classes += ' harvesting';
            grid.innerHTML += `<div class="${classes}">${m}</div>`;
        });
    }
    
    // 2. Render Farm School
    const school = document.getElementById('farmSchoolContent');
    if (school) {
        school.innerHTML = '';
        const steps = crop.farm_school_steps || [];
        if (steps.length > 0) {
            steps.forEach(step => {
                school.innerHTML += `<div class="farm-step">${step}</div>`;
            });
        } else {
            school.innerHTML = '<p style="color: var(--text-muted);">Educational guide not available for this crop yet.</p>';
        }
    }
}

function clearPlanner() {
    const grid = document.getElementById('timelineGrid');
    if (grid) grid.innerHTML = '';
    const school = document.getElementById('farmSchoolContent');
    if (school) school.innerHTML = '<p style="color: var(--text-muted); font-style: italic;">Select a crop to view the educational guide.</p>';
}

function detectNextSeason() {
    const month = new Date().getMonth() + 1; // 1-12
    let nextSeason = '';
    let cropHints = '';
    
    if (month >= 3 && month <= 5) {
        nextSeason = 'Kharif (Starts in June)';
        cropHints = 'Prepare for: Rice, Maize, Cotton, Soybean.';
    } else if (month >= 6 && month <= 9) {
        nextSeason = 'Rabi (Starts in October)';
        cropHints = 'Prepare for: Wheat, Mustard, Gram, Potato.';
    } else {
        nextSeason = 'Zaid (Starts in March)';
        cropHints = 'Prepare for: Watermelon, Cucumber, Fodder crops.';
    }
    
    const textEl = document.getElementById('season-alert-text');
    if (textEl) {
        textEl.innerHTML = `<strong>Upcoming Season:</strong> ${nextSeason} <br><span style="font-size:0.9rem; color:var(--text-muted);">${cropHints}</span>`;
    }
}

// Ensure fetchPlannerData is called when app loads
window.addEventListener('DOMContentLoaded', () => {
    fetchPlannerData();
});
"""

with open('frontend/app.js', 'a', encoding='utf-8') as f:
    f.write(js_code)
print("js appended")

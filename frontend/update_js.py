import re

with open('app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Add new global variables and DOM Elements
globals_add = '''// New DOM Elements
const dashboardWisdom = document.getElementById('dashboard-wisdom');
const dashboardAdvisories = document.getElementById('dashboard-advisories');
const encyclopediaGrid = document.getElementById('encyclopediaGrid');
const historyList = document.getElementById('historyList');
'''
js = js.replace('// DOM Elements', globals_add + '\n// DOM Elements')

# Update fetchDashboardData to handle wisdom and advisories
old_update = '''        // Update basic metrics
        updateMetrics(data.data, data.soil_profile);'''
new_update = '''        // Update basic metrics
        updateMetrics(data.data, data.soil_profile);
        
        // Update Wisdom and Advisories
        if(dashboardWisdom && data.wisdom) dashboardWisdom.innerText = "";
        if(dashboardAdvisories && data.advisories) {
            dashboardAdvisories.innerHTML = data.advisories.map(adv => <li style="margin-bottom: 0.5rem;"><i data-lucide="alert-triangle" style="width: 16px; height: 16px; display: inline; margin-right: 8px; color: #facc15;"></i></li>).join('');
            if(window.lucide) lucide.createIcons();
        }'''
js = js.replace(old_update, new_update)

# Add new functions at the end of the file
new_funcs = '''
// ─── TABS LOGIC ──────────────────────────────────────────────
function switchTab(tabId) {
    // Hide all views
    document.querySelectorAll('.tab-view').forEach(v => v.style.display = 'none');
    // Show selected view
    document.getElementById(iew-).style.display = 'block';
    
    // Update sidebar UI
    document.querySelectorAll('.nav-links li').forEach(li => li.classList.remove('active'));
    document.getElementById(	ab-).classList.add('active');

    // Load data if needed
    if(tabId === 'encyclopedia') loadEncyclopedia();
    if(tabId === 'history') loadHistory();
}

// ─── ENCYCLOPEDIA LOGIC ──────────────────────────────────────
async function loadEncyclopedia() {
    try {
        const res = await fetch(${API_URL}/crops);
        const crops = await res.json();
        
        encyclopediaGrid.innerHTML = '';
        for(let key in crops) {
            let c = crops[key];
            let card = document.createElement('div');
            card.style.cssText = "background: rgba(255,255,255,0.03); border: 1px solid var(--border); padding: 1.5rem; border-radius: 12px;";
            card.innerHTML = 
                <h3 style="color: var(--primary); margin-bottom: 0.5rem; font-size: 1.2rem;"></h3>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1rem;">Season: <strong></strong> | Regions: </p>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.85rem;">
                    <div><span style="color: var(--text-muted)">pH:</span> </div>
                    <div><span style="color: var(--text-muted)">Moisture:</span> </div>
                    <div style="grid-column: span 2;"><span style="color: var(--text-muted)">N-P-K:</span> --</div>
                </div>
            ;
            encyclopediaGrid.appendChild(card);
        }
    } catch(err) {
        console.error(err);
    }
}

// ─── HISTORY LOGIC ──────────────────────────────────────────
async function loadHistory() {
    try {
        const res = await fetch(${API_URL}/history);
        const history = await res.json();
        
        historyList.innerHTML = '';
        if(history.length === 0) {
            historyList.innerHTML = '<p style="color: var(--text-muted)">No yields logged yet.</p>';
            return;
        }
        
        history.reverse().forEach(h => {
            let item = document.createElement('div');
            item.style.cssText = "background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;";
            item.innerHTML = 
                <div>
                    <h4 style="color: var(--primary); margin-bottom: 0.25rem;"></h4>
                    <span style="color: var(--text-muted); font-size: 0.85rem;"> </span>
                </div>
                <div style="font-size: 1.2rem; font-weight: bold; color: white;">
                     <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: normal;">Q</span>
                </div>
            ;
            historyList.appendChild(item);
        });
    } catch(err) {
        console.error(err);
    }
}

async function submitYield(e) {
    e.preventDefault();
    const crop = document.getElementById('yieldCrop').value;
    const season = document.getElementById('yieldSeason').value;
    const amount = document.getElementById('yieldAmount').value;
    
    try {
        await fetch(${API_URL}/history, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ crop: crop, season: season, yield: amount })
        });
        document.getElementById('yieldForm').reset();
        loadHistory();
    } catch(err) {
        console.error(err);
        alert("Failed to save yield record.");
    }
}

// ─── CALLING LOGIC ──────────────────────────────────────────
async function makeEmergencyCall() {
    try {
        alert("Initiating call to expert...");
        await fetch(${API_URL}/call);
    } catch(err) {
        console.error("Call failed", err);
    }
}
'''
js = js + '\n' + new_funcs

with open('app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated app.js with new logic")

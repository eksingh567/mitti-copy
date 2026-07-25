const API_URL = 'http://localhost:5000';
let currentRecommendations = {};
let currentLang = 'en';

// In-Memory JWT Access Token Storage (Critical OWASP vulnerability fix: keeps access token out of localStorage)
let accessToken = null;

// Secure authenticated fetch helper with automatic token refresh and CSRF headers
async function authFetch(url, options = {}) {
    options.headers = options.headers || {};
    
    // Add custom CSRF header check to prevent cross-site request forgery
    options.headers['X-Requested-With'] = 'XMLHttpRequest';
    
    if (accessToken) {
        options.headers['Authorization'] = `Bearer ${accessToken}`;
    }
    
    const res = await window.fetch(url, options);
    if (res.status === 401 && !url.includes('/api/login') && !url.includes('/api/refresh')) {
        // Access token expired, attempt silent rotation using refresh cookie
        try {
            await refreshSession();
            // Retry the original request
            if (accessToken) {
                options.headers['Authorization'] = `Bearer ${accessToken}`;
            }
            return await window.fetch(url, options);
        } catch(err) {
            logoutUser();
            throw new Error("Session expired. Please login again.");
        }
    }
    return res;
}

async function refreshSession() {
    try {
        const res = await window.fetch(`${API_URL}/api/v1/refresh`, { 
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (!res.ok) throw new Error("Silent refresh failed");
        
        const data = await res.json();
        accessToken = data.access_token;
        localStorage.setItem('user_profile', JSON.stringify(data.user));
        
        document.getElementById('loginOverlay').style.display = 'none';
        document.getElementById('profileName').textContent = data.user.name;
        document.getElementById('logoutBtn').style.display = 'block';
    } catch(e) {
        throw e;
    }
}

// Check session status on page load
document.addEventListener("DOMContentLoaded", async () => {
    try {
        await refreshSession();
        fetchDashboardData();
    } catch (err) {
        document.getElementById('loginOverlay').style.display = 'flex';
        document.getElementById('logoutBtn').style.display = 'none';
    }
});

async function loginUser() {
    const phone = document.getElementById('loginPhone').value.trim();
    const password = document.getElementById('loginPassword').value.trim();
    const errorEl = document.getElementById('loginError');
    
    if (!phone || !password) {
        errorEl.textContent = "Please fill in all fields.";
        errorEl.style.display = 'block';
        return;
    }
    
    try {
        const res = await window.fetch(`${API_URL}/api/v1/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ phone, password })
        });
        
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Login failed");
        
        accessToken = data.access_token;
        localStorage.setItem('user_profile', JSON.stringify(data.user));
        
        document.getElementById('loginOverlay').style.display = 'none';
        document.getElementById('profileName').textContent = data.user.name;
        document.getElementById('logoutBtn').style.display = 'block';
        
        // Refresh dashboard data
        fetchDashboardData();
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.style.display = 'block';
    }
}

async function logoutUser() {
    try {
        await window.fetch(`${API_URL}/api/v1/logout`, { 
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
    } catch(e) {}
    accessToken = null;
    localStorage.removeItem('user_profile');
    document.getElementById('loginOverlay').style.display = 'flex';
    document.getElementById('logoutBtn').style.display = 'none';
    document.getElementById('loginPhone').value = '';
    document.getElementById('loginPassword').value = '';
    document.getElementById('loginError').style.display = 'none';
}



// DOM Elements
const dashboardWisdom = document.getElementById('dashboard-wisdom');
const dashboardAdvisories = document.getElementById('dashboard-advisories');
const encyclopediaGrid = document.getElementById('encyclopediaGrid');
const historyList = document.getElementById('historyList');
const stateSelect = document.getElementById('stateSelect');
const seasonSelect = document.getElementById('seasonSelect');
const soilSelect = document.getElementById('soilSelect');
const waterSelect = document.getElementById('waterSelect');
const typeSelect = document.getElementById('typeSelect');
const phenomenonSelect = document.getElementById('phenomenonSelect');

const cropsGrid = document.getElementById('cropsGrid');
const cropDetailsPanel = document.getElementById('cropDetailsPanel');

async function loadDemoData() {
    await authFetch(`${API_URL}/api/v1/demo`);
    await fetchDashboardData();
}

async function fetchDashboardData() {
    try {
        const state = stateSelect.value;
        const res = await authFetch(`${API_URL}/?state=${state}&lang=${currentLang}&t=${Date.now()}`);
        const data = await res.json();
        
        // Update basic metrics
        updateMetrics(data.data, data.soil_profile);
        
                // Update Greeting
        const greetingEl = document.querySelector('header h1');
        if (greetingEl && data.greeting) {
            greetingEl.innerText = data.greeting;
        }
        
        // Update Wisdom and Advisories
        if(dashboardWisdom && data.wisdom) dashboardWisdom.innerText = `"${data.wisdom}"`;
        if(dashboardAdvisories && data.advisories) {
            dashboardAdvisories.innerHTML = data.advisories.map(adv => `<li style="margin-bottom: 0.5rem;"><i data-lucide="alert-triangle" style="width: 16px; height: 16px; display: inline; margin-right: 8px; color: #facc15;"></i>${adv}</li>`).join('');
            if(window.lucide) lucide.createIcons();
        }
        
        // Load recommendations based on selections
        await loadRecommendations();
    } catch (err) {
        console.error("Failed to fetch backend data", err);
    }
}

function updateMetrics(sensorData, profileName) {
    if(!sensorData) return;
    
    // Soil Profile
    document.getElementById('soilProfileName').innerText = profileName || "Unknown";
    
    // NPK
    document.getElementById('val-n').innerText = sensorData.n;
    document.getElementById('val-p').innerText = sensorData.p;
    document.getElementById('val-k').innerText = sensorData.k;
    
    // Bars (assuming max ~300 for calculation)
    document.getElementById('bar-n').style.width = `${Math.min((sensorData.n / 300) * 100, 100)}%`;
    document.getElementById('bar-p').style.width = `${Math.min((sensorData.p / 100) * 100, 100)}%`;
    document.getElementById('bar-k').style.width = `${Math.min((sensorData.k / 300) * 100, 100)}%`;
    
    // Health
    document.getElementById('val-ph').innerText = sensorData.ph.toFixed(1);
    document.getElementById('val-ec').innerHTML = `${sensorData.ec.toFixed(2)} <small>mS/cm</small>`;
    document.getElementById('val-moisture').innerText = `${sensorData.moisture}%`;
    document.getElementById('val-temp').innerText = `${sensorData.temp}°C`;
}

async function loadRecommendations() {
    const season = seasonSelect.value;
    const state = stateSelect.value;
    
    // Region determination is handled mostly backend now, but we pass state
    cropsGrid.innerHTML = '<div class="loading-pulse">Analyzing...</div>';
    
    try {
        
        const soil = soilSelect ? soilSelect.value : 'Auto';
        const water = waterSelect ? waterSelect.value : 'Any';
        const type = typeSelect ? typeSelect.value : 'Any';
        const phenomenon = phenomenonSelect ? phenomenonSelect.value : 'None';
        
        
        // Update the Active Soil Profile text based on the override
        const soilDisplay = document.getElementById('soilProfileName');
        if (soil !== 'Auto') {
            soilDisplay.innerHTML = `<span style="color: #fbbf24;">${soil} (Override)</span>`;
        } else {
            // If set back to Auto, we should re-fetch the real sensor data to update the display
            authFetch(`${API_URL}/?state=${state}&lang=${currentLang}&t=${Date.now()}`)
                .then(r => r.json())
                .then(data => {
                    soilDisplay.innerText = data.soil_profile || "Unknown";
                });
        }
        
        const res = await authFetch(`${API_URL}/recommend?season=${season}&state=${state}&soil=${soil}&water=${water}&type=${type}&phenomenon=${phenomenon}&lang=${currentLang}&t=${Date.now()}`);


        const data = await res.json();
        currentRecommendations = data;
        
        renderCropsGrid(data);
    } catch (err) {
        console.error(err);
        cropsGrid.innerHTML = '<div style="color: #f87171">Error connecting to suitability engine.</div>';
    }
}

function renderCropsGrid(data) {
    cropsGrid.innerHTML = '';
    
    // Convert to array and sort by score
    const sortedCrops = Object.entries(data).sort((a,b) => b[1].score - a[1].score);
    
    if (sortedCrops.length === 0) {
        cropsGrid.innerHTML = '<div style="color: #9ca3af; text-align: center; padding: 2rem; grid-column: 1 / -1;">No crops perfectly match these strict filters. Try adjusting your Water or Category selections.</div>';
        cropDetailsPanel.style.display = 'none';
        return;
    }
    
    sortedCrops.forEach(([cropKey, details], index) => {
        const btn = document.createElement('button');
        btn.className = `crop-btn ${index === 0 ? 'active' : ''}`;
        btn.id = `btn-${cropKey}`;
        btn.onclick = () => selectCrop(cropKey);
        
        // Determine dot color based on score
        let dotColor = '#ef4444'; // Red for <= 40
        if (details.score > 75) {
            dotColor = '#22c55e'; // Green
        } else if (details.score > 40) {
            dotColor = '#eab308'; // Yellow
        }
        
        btn.innerHTML = `
            <span>${details.name_en || cropKey}</span>
            <span style="display:inline-block; width:12px; height:12px; border-radius:50%; background-color:${dotColor}; margin-left:8px;" title="Score: ${details.score}%"></span>
        `;
        cropsGrid.appendChild(btn);
        
        if(index === 0) selectCrop(cropKey); // Auto-select first
    });
}

function selectCrop(cropKey) {
    // UI active state
    document.querySelectorAll('.crop-btn').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById(`btn-${cropKey}`);
    if(btn) btn.classList.add('active');
    
    const details = currentRecommendations[cropKey];
    if(!details) return;
    
    cropDetailsPanel.style.display = 'block';
    document.getElementById('detailName').innerText = details.name_hi || details.name_en || cropKey;
    
    // Render detailed actionable feedback
    const feedbackEl = document.getElementById('detailFeedback');
    if(details.feedback_list && details.feedback_list.length > 0) {
        feedbackEl.innerHTML = '<strong style="color: #facc15;">Required Actions:</strong><ul style="margin-top: 0.5rem; padding-left: 1.5rem; color: #d1d5db;">' + details.feedback_list.map(f => `<li>${f}</li>`).join('') + '</ul>';
    } else {
        feedbackEl.innerText = details.feedback || "No feedback available.";
    }
    
    document.getElementById('detailPh').innerText = details.ph_range || "N/A";
    document.getElementById('detailMoisture').innerText = details.moisture_range || "N/A";
    document.getElementById('detailRegions').innerText = (details.regions || []).join(', ');
    
    const matchBadge = document.getElementById('detailMatch');
    matchBadge.innerText = `${details.score}% Match`;
    matchBadge.className = 'match-badge ' + (details.score >= 80 ? 'high' : details.score >= 50 ? 'med' : 'low');
}

// Event Listeners
stateSelect.addEventListener('change', () => {
    document.getElementById('userLocation').innerText = `Farmer, ${stateSelect.value}`;
    fetchDashboardData();
});
seasonSelect.addEventListener('change', loadRecommendations);
if (soilSelect) soilSelect.addEventListener('change', loadRecommendations);
if (waterSelect) waterSelect.addEventListener('change', loadRecommendations);
if (typeSelect) typeSelect.addEventListener('change', loadRecommendations);
if (phenomenonSelect) phenomenonSelect.addEventListener('change', loadRecommendations);


// Init
window.onload = fetchDashboardData;

// ─── TABS LOGIC ──────────────────────────────────────────────
function switchTab(tabId) {
    // Hide all views
    document.querySelectorAll('.tab-view').forEach(v => v.style.display = 'none');
    // Show selected view
    document.getElementById(`view-${tabId}`).style.display = 'block';
    
    // Update sidebar UI
    document.querySelectorAll('.nav-links li').forEach(li => li.classList.remove('active'));
    document.getElementById(`tab-${tabId}`).classList.add('active');

    // Toggle controls visibility
    const controlsDiv = document.querySelector('.controls');
    if (controlsDiv) {
        controlsDiv.style.display = (tabId === 'dashboard') ? 'flex' : 'none';
    }

    // Load data if needed
    if(tabId === 'encyclopedia') loadEncyclopedia();
    if(tabId === 'history') { loadHistory(); loadSmartSuggestions(); }
    if(tabId === 'schemes') loadSchemes();
    if(tabId === 'journey') loadJourney();
}

// ─── ENCYCLOPEDIA LOGIC ──────────────────────────────────────
async function loadEncyclopedia() {
    try {
        encyclopediaGrid.innerHTML = '<div class="loading-pulse">Loading encyclopedia...</div>';
        const res = await authFetch(`${API_URL}/api/v1/crops`);
        const crops = await res.json();
        
        encyclopediaGrid.innerHTML = '';
        for(let key in crops) {
            let c = crops[key];
            let card = document.createElement('div');
            card.style.cssText = "background: rgba(255,255,255,0.03); border: 1px solid var(--border); padding: 1.5rem; border-radius: 12px;";
            card.innerHTML = `
                <h3 style="color: var(--primary); margin-bottom: 0.5rem; font-size: 1.2rem;">${c.name_hi || c.name_en}</h3>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1rem;">Season: <strong>${c.season}</strong> | Regions: ${c.regions.join(', ')}</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.85rem;">
                    <div><span style="color: var(--text-muted)">pH:</span> ${c.ph ? c.ph.join('-') : 'N/A'}</div>
                    <div><span style="color: var(--text-muted)">Moisture:</span> ${c.moisture ? c.moisture.join('-')+'%' : 'N/A'}</div>
                    <div style="grid-column: span 2;"><span style="color: var(--text-muted)">N-P-K:</span> ${c.n ? c.n.join('-') : '0'}-${c.p ? c.p.join('-') : '0'}-${c.k ? c.k.join('-') : '0'}</div>
                </div>
            `;
            encyclopediaGrid.appendChild(card);
        }
    } catch(err) {
        console.error(err);
        encyclopediaGrid.innerHTML = '<div style="color: #f87171">Failed to load encyclopedia data.</div>';
    }
}

// ─── HISTORY LOGIC ──────────────────────────────────────────
async function loadHistory() {
    try {
        historyList.innerHTML = '<div class="loading-pulse">Loading history...</div>';
        const res = await authFetch(`${API_URL}/api/v1/history`);
        const history = await res.json();
        
        historyList.innerHTML = '';
        if(history.length === 0) {
            historyList.innerHTML = '<p style="color: var(--text-muted)">No yields logged yet.</p>';
            return;
        }
        
        history.reverse().forEach(h => {
            let item = document.createElement('div');
            item.style.cssText = "background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;";
            item.innerHTML = `
                <div>
                    <h4 style="color: var(--primary); margin-bottom: 0.25rem;">${h.crop}</h4>
                    <span style="color: var(--text-muted); font-size: 0.85rem;">${h.season} ${h.year}</span>
                </div>
                <div style="font-size: 1.2rem; font-weight: bold; color: white;">
                    ${h.yield_quintals} <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: normal;">Q</span>
                </div>
            `;
            historyList.appendChild(item);
        });
    } catch(err) {
        console.error(err);
        historyList.innerHTML = '<div style="color: #f87171">Failed to load history.</div>';
    }
}

async function submitYield(e) {
    e.preventDefault();
    const crop = document.getElementById('yieldCrop').value;
    const season = document.getElementById('yieldSeason').value;
    const amount = document.getElementById('yieldAmount').value;
    
    try {
        await authFetch(`${API_URL}/api/v1/history`, {
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
        const state = stateSelect.value;
        const season = seasonSelect.value;
        alert("Initiating call to expert... Check Twilio logs!");
        await authFetch(`${API_URL}/call?state=${state}&season=${season}`);
    } catch(err) {
        console.error("Call failed", err);
    }
}

// ─── SMART CROP SUGGESTIONS ──────────────────────────────────
async function loadSmartSuggestions() {
    const container = document.getElementById('smartSuggestionContent');
    if(!container) return;
    
    container.innerHTML = '<p style="color: #94a3b8;"><i data-lucide="loader" class="spin" style="width: 16px; height: 16px;"></i> Analyzing your crop history...</p>';
    
    try {
        const res = await authFetch(`${API_URL}/api/v1/suggest-next`);
        const data = await res.json();
        
        if (!data.suggestions || data.suggestions.length === 0) {
            container.innerHTML = '<p style="color: #64748b; font-style: italic;">Log at least one yield record above to get personalized suggestions.</p>';
            return;
        }
        
        let html = '';
        
        // Analysis Summary
        html += `<div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 1rem;">
            <div style="flex: 1; min-width: 200px; background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; border-left: 3px solid #f59e0b;">
                <p style="color: #94a3b8; font-size: 0.85rem;">Last Crop Grown</p>
                <h3 style="margin: 0.25rem 0;">${data.last_crop} <span style="color: #94a3b8; font-size: 0.85rem;">(${data.last_season})</span></h3>
            </div>
            <div style="flex: 1; min-width: 200px; background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; border-left: 3px solid #10b981;">
                <p style="color: #94a3b8; font-size: 0.85rem;">Upcoming Season</p>
                <h3 style="margin: 0.25rem 0;">${data.upcoming_season} <span style="color: #94a3b8; font-size: 0.85rem;">(${data.upcoming_months})</span></h3>
            </div>
            <div style="flex: 1; min-width: 200px; background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 8px; border-left: 3px solid #3b82f6;">
                <p style="color: #94a3b8; font-size: 0.85rem;">Records Analyzed</p>
                <h3 style="margin: 0.25rem 0;">${data.history_analysis.total_records} records, ${data.history_analysis.unique_crops} crops</h3>
            </div>
        </div>`;
        
        // Diversity Warning
        if (data.history_analysis.diversity_warning) {
            html += `<div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                <p style="color: #fca5a5;"><strong>⚠️ Low Crop Diversity Warning:</strong> You have been growing the same crop repeatedly. This degrades soil health over time. Consider rotating your crops using the suggestions below.</p>
            </div>`;
        }
        
        // Rotation reason (if available)
        const rotationSuggestion = data.suggestions.find(s => s.source === 'crop_rotation');
        if (rotationSuggestion && rotationSuggestion.rotation_reason) {
            html += `<div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                <p style="color: #34d399;"><strong>🧠 Rotation Logic:</strong> ${rotationSuggestion.rotation_reason}</p>
            </div>`;
        }
        
        // Suggestion Cards
        html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem;">';
        data.suggestions.forEach((s, idx) => {
            const isTopPick = idx === 0;
            const borderColor = s.fits_upcoming_season ? '#10b981' : '#f59e0b';
            const badge = s.source === 'crop_rotation' ? '🔄 Rotation Pick' : '📅 Season Match';
            const topBadge = isTopPick ? '<span style="background: #10b981; color: #0f172a; font-size: 0.75rem; padding: 0.15rem 0.5rem; border-radius: 20px; font-weight: bold;">⭐ TOP PICK</span>' : '';
            
            html += `<div style="background: rgba(15, 23, 42, 0.6); border: 1px solid ${borderColor}; border-radius: 10px; padding: 1.2rem; transition: transform 0.2s;" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='none'">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 0.75rem; color: ${borderColor};">${badge}</span>
                    ${topBadge}
                </div>
                <h4 style="margin: 0.25rem 0;">${s.name}</h4>
                <p style="color: #94a3b8; font-size: 0.85rem; margin: 0.25rem 0;">Season: ${s.season}</p>
                <p style="color: #64748b; font-size: 0.8rem;">Sow: ${s.sowing_months.join(', ')}</p>
                ${!s.fits_upcoming_season ? '<p style="color: #f59e0b; font-size: 0.75rem; margin-top: 0.5rem;">⏳ Not in upcoming season</p>' : '<p style="color: #10b981; font-size: 0.75rem; margin-top: 0.5rem;">✅ Ready for upcoming season</p>'}
            </div>`;
        });
        html += '</div>';
        
        container.innerHTML = html;
        if(window.lucide) lucide.createIcons();
        
    } catch(e) {
        console.error("Failed to load suggestions", e);
        container.innerHTML = '<p style="color: #f87171;">Failed to load suggestions. Make sure you have yield records logged.</p>';
    }
}


// ─── NATIVE TRANSLATION DICTIONARY ──────────────────────────
const i18n = {
    "Dashboard": {"hinglish": "Dashboard", "hi": "डैशबोर्ड"},
    "Crop Encyclopedia": {"hinglish": "Fasal Ki Jankari", "hi": "फसल ज्ञानकोष"},
    "Yield History": {"hinglish": "Pichli Paidawar", "hi": "पिछली पैदावार"},
    "Settings": {"hinglish": "Settings", "hi": "सेटिंग्स"},
    "Region Map": {"hinglish": "Kshetra Naksha", "hi": "क्षेत्र नक्शा"},
    "Active Soil Profile": {"hinglish": "Aapki Mitti Ka Prakar", "hi": "सक्रिय मिट्टी प्रोफ़ाइल"},
    "Macronutrients": {"hinglish": "Zaroori Tatva (NPK)", "hi": "मुख्य पोषक तत्व (NPK)"},
    "Soil Health": {"hinglish": "Mitti Ki Sehat", "hi": "मिट्टी का स्वास्थ्य"},
    "Suitability Engine": {"hinglish": "Sahi Fasal Engine", "hi": "उपयुक्तता इंजन"},
    "Daily Wisdom & Advisories": {"hinglish": "Kheti Ka Gyan & Alerts", "hi": "कृषि ज्ञान और अलर्ट"},
    "Scan Sensors": {"hinglish": "Sensor Scan Karein", "hi": "सेंसर स्कैन करें"},
    "Call The Farmer": {"hinglish": "Kisan Ko Call Karein", "hi": "किसान को कॉल करें"},
    "State": {"hinglish": "Rajya", "hi": "राज्य"},
    "Season": {"hinglish": "Mausam", "hi": "मौसम"},
    "Required Actions:": {"hinglish": "Zaroori Kadam:", "hi": "आवश्यक कदम:"},
    "Log New Yield": {"hinglish": "Nayi Paidawar Darj Karein", "hi": "नई उपज दर्ज करें"},
    "Past Yield Records": {"hinglish": "Pichla Record", "hi": "पिछला रिकॉर्ड"},
    "Save Record": {"hinglish": "Record Save Karein", "hi": "रिकॉर्ड सहेजें"}
};

let currentLang = 'en';

function setNativeLanguage(lang) {
    currentLang = lang;
    
    // Update active button state
    document.querySelectorAll('[id^="lang-btn-"]').forEach(btn => btn.style.background = 'none');
    document.getElementById('lang-btn-' + lang).style.background = 'rgba(16, 185, 129, 0.4)';
    
    // Quick and dirty text replacement by searching for English keys in text nodes
    walkDOM(document.body, function(node) {
        if(node.nodeType === 3) { // Text node
            let text = node.originalText || node.nodeValue.trim();
            if(!node.originalText && text.length > 0) node.originalText = text; // Save original
            
            if(node.originalText) {
                // Try exact match
                if(i18n[node.originalText]) {
                    node.nodeValue = lang === 'en' ? node.originalText : i18n[node.originalText][lang];
                }
            }
        }
    });
    
    // Also re-render dynamic content
    fetchDashboardData();
}

function walkDOM(node, func) {
    func(node);
    node = node.firstChild;
    while(node) {
        walkDOM(node, func);
        node = node.nextSibling;
    }
}

// --- Planner Logic ---
let plannerCropsData = {};

let knowsSoil = true;
let currentDetectedSoil = "Alluvial";

function handleSoilKnowledgeChange() {
    const toggle = document.getElementById('globalSoilKnowledgeToggle');
    if(!toggle) return;
    
    knowsSoil = toggle.checked;
    
    const plannerSoil = document.getElementById('planner-soil-filter');
    const journeySoil = document.getElementById('journeySoilSelect');
    
    if (knowsSoil) {
        if(plannerSoil) { plannerSoil.disabled = false; plannerSoil.style.opacity = '1'; }
        if(journeySoil) { journeySoil.disabled = false; journeySoil.style.opacity = '1'; }
    } else {
        if(plannerSoil) { 
            plannerSoil.disabled = true; 
            plannerSoil.style.opacity = '0.5'; 
            plannerSoil.value = currentDetectedSoil; 
        }
        if(journeySoil) { 
            journeySoil.disabled = true; 
            journeySoil.style.opacity = '0.5';
            journeySoil.value = currentDetectedSoil; 
        }
    }
}

async function fetchSensorData() {
    try {
        const res = await authFetch(`${API_URL}/api/data`);
        const data = await res.json();
        updateDashboard(data);
        
        // Auto-detect soil if they don't know it
        if(data.detected_soil) {
            currentDetectedSoil = data.detected_soil;
            if(!knowsSoil) {
                const plannerSoil = document.getElementById('planner-soil-filter');
                const journeySoil = document.getElementById('journeySoilSelect');
                if(plannerSoil && plannerSoil.value !== currentDetectedSoil) plannerSoil.value = currentDetectedSoil;
                if(journeySoil && journeySoil.value !== currentDetectedSoil) journeySoil.value = currentDetectedSoil;
            }
        }
        
    } catch (e) {
        console.error("Sensor fetch error", e);
    }
}


async function fetchPlannerData() {
    try {
        const res = await authFetch(`${API_URL}/api/v1/crops`);
        plannerCropsData = await res.json();
        populatePlannerDropdown();
        detectNextSeason();
    } catch (e) {
        console.error('Error fetching planner data:', e);
    }
}


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
        let sowingStepCount = 1;
        let harvestStepCount = (crop.farm_school_steps || []).length;
        months.forEach(m => {
            let classes = 'timeline-month';
            let label = '';
            
            if (sowing.includes(m)) {
                classes += ' sowing';
                label = `<br><span style="font-size: 0.75rem; opacity: 0.8; font-weight: bold;">Step ${sowingStepCount}</span>`;
                sowingStepCount++;
            }
            if (harvesting.includes(m)) {
                classes += ' harvesting';
                label = `<br><span style="font-size: 0.75rem; opacity: 0.8; font-weight: bold;">Step ${harvestStepCount}</span>`;
            }
            
            grid.innerHTML += `<div class="${classes}">${m}${label}</div>`;
        });
    }
    
    // 2. Render Farm School (Rich)
    const school = document.getElementById('farmSchoolContent');
    if (school) {
        school.innerHTML = '';
        const fs = crop.farm_school;
        
        if (fs && fs.steps && fs.steps.length > 0) {
            // Steps Section
            let stepsHtml = '<div class="farm-school-section"><div class="farm-school-title"><i data-lucide="list-ordered"></i> Growing Steps</div>';
            fs.steps.forEach((step, idx) => {
                stepsHtml += `
                    <div class="fs-step-card">
                        <div class="fs-step-header"><span>Step ${idx + 1}: ${step.title}</span></div>
                        <div class="fs-step-desc">${step.desc}</div>
                        <div class="fs-step-why"><strong>🧠 The "Why":</strong> ${step.why}</div>
                    </div>
                `;
            });
            stepsHtml += '</div>';
            school.innerHTML += stepsHtml;
            
            // Challenges Section (Interactive)
            if (fs.challenges && fs.challenges.length > 0) {
                let chalHtml = '<div class="farm-school-section"><div class="farm-school-title" style="color: #ef4444; border-color: rgba(239, 68, 68, 0.2);"><i data-lucide="alert-triangle"></i> Key Challenges</div><div class="fs-challenges-list" style="display: flex; flex-direction: column; gap: 0.5rem;">';
                fs.challenges.forEach(c => {
                    chalHtml += `
                        <details class="fs-challenge-details" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 0.5rem;">
                            <summary style="cursor: pointer; color: #fca5a5; font-weight: bold; outline: none; list-style: none; display: flex; align-items: center; gap: 0.5rem;">
                                <i data-lucide="help-circle" style="width: 16px; height: 16px;"></i> ${c.issue}
                            </summary>
                            <div style="margin-top: 0.5rem; padding-left: 1.5rem; color: #f87171; font-size: 0.9rem;">
                                <strong>Solution:</strong> ${c.solution}
                            </div>
                        </details>
                    `;
                });
                chalHtml += '</div></div>';
                school.innerHTML += chalHtml;
            }
            
            // Soil Tips Section
            if (fs.soil_tips) {
                school.innerHTML += `
                    <div class="farm-school-section">
                        <div class="farm-school-title" style="color: #f59e0b; border-color: rgba(245, 158, 11, 0.2);"><i data-lucide="sprout"></i> Soil Replenishment</div>
                        <div class="fs-info-box">${fs.soil_tips}</div>
                    </div>
                `;
            }
            
            lucide.createIcons(); // re-init icons for dynamic content
            
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

// --- IoT Auto-Irrigate Logic ---
let sensorInterval;

function startSensorPolling() {
    if(sensorInterval) clearInterval(sensorInterval);
    sensorInterval = setInterval(fetchRealTimeSensors, 2000);
}

async function fetchRealTimeSensors() {
    try {
        const res = await authFetch(`${API_URL}/api/v1/sensors`);
        if(!res.ok) return;
        const data = await res.json();
        
        // Update Moisture UI
        const moistureVal = document.getElementById('moisture-val');
        const moistureBar = document.getElementById('moisture-bar');
        const moistureStatus = document.getElementById('moisture-status');
        const pumpBadge = document.getElementById('pumpBadge');
        
        if (moistureVal) moistureVal.innerText = `${data.moisture}%`;
        if (moistureBar) moistureBar.style.width = `${Math.min(data.moisture, 100)}%`;
        
        if (moistureStatus) {
            if (data.moisture < 40) moistureStatus.innerText = "Critical: Too Dry";
            else if (data.moisture > 70) moistureStatus.innerText = "Good: Well Hydrated";
            else moistureStatus.innerText = "Fair: Drying out";
        }
        
        // Pump Status
        if (pumpBadge) {
            pumpBadge.style.display = data.pump_status ? 'block' : 'none';
        }
        
        // Ensure toggle reflects backend state on initial load
        const toggle = document.getElementById('autoIrrigateToggle');
        if (toggle && toggle.dataset.initialized !== 'true') {
            toggle.checked = data.auto_irrigate;
            toggle.dataset.initialized = 'true';
        }
        
    } catch(e) {
        console.error("Error polling sensors:", e);
    }
}

async function toggleAutoIrrigate() {
    const toggle = document.getElementById('autoIrrigateToggle');
    
    // Pump control safety prompt
    const confirmToggle = confirm("Are you sure you want to toggle the automated water pump irrigation status? This controls physical hardware locks.");
    if (!confirmToggle) {
        toggle.checked = !toggle.checked;
        return;
    }
    
    try {
        await authFetch(`${API_URL}/api/v1/irrigation/auto`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ auto_irrigate: toggle.checked, confirm: true })
        });
        // Immediately fetch state
        fetchRealTimeSensors();
    } catch(e) {
        console.error("Failed to toggle auto-irrigate", e);
        toggle.checked = !toggle.checked; // Revert on failure
    }
}

// Start polling on load
window.addEventListener('load', startSensorPolling);

// --- Gov Schemes Logic ---
async function loadSchemes() {
    try {
        const res = await authFetch(`${API_URL}/api/v1/schemes`);
        const schemes = await res.json();
        const container = document.getElementById('schemesContainer');
        if(!container) return;
        
        container.innerHTML = '';
        schemes.forEach(scheme => {
            const card = document.createElement('div');
            card.className = 'scheme-card';
            card.innerHTML = `
                <div class="scheme-category" style="background: rgba(16, 185, 129, 0.2); color: #10b981;">${scheme.category}</div>
                <h3 style="margin-bottom: 0.5rem;">${scheme.title}</h3>
                <p style="color: #94a3b8; font-size: 0.95rem; line-height: 1.5; margin-bottom: 1.5rem;">${scheme.description}</p>
                <a href="${scheme.link}" target="_blank" class="scheme-btn">Check Eligibility & Apply</a>
            `;
            container.appendChild(card);
        });
    } catch(e) {
        console.error("Failed to load schemes:", e);
        const container = document.getElementById('schemesContainer');
        if(container) container.innerHTML = '<p>Failed to load schemes.</p>';
    }
}

// --- AI Scanner Logic ---
let uploadedFile = null;

function handleFileUpload(e) {
    const file = e.target.files[0];
    if(!file) return;
    
    uploadedFile = file;
    const reader = new FileReader();
    reader.onload = (event) => {
        document.getElementById('uploadZone').style.display = 'none';
        document.getElementById('previewZone').style.display = 'block';
        document.getElementById('imagePreview').src = event.target.result;
        
        document.getElementById('scanResults').style.display = 'none';
    };
    reader.readAsDataURL(file);
}

async function startScan() {
    if(!uploadedFile) return;
    
    // UI state
    document.getElementById('scanBtn').style.display = 'none';
    document.getElementById('scanLoading').style.display = 'block';
    document.getElementById('scanResults').style.display = 'none';
    
    const formData = new FormData();
    formData.append('image', uploadedFile);
    
    try {
        const res = await authFetch(`${API_URL}/api/v1/scan-image`, {
            method: 'POST',
            body: formData
        });
        
        if(!res.ok) throw new Error("API Error");
        const result = await res.json();
        
        document.getElementById('scanLoading').style.display = 'none';
        document.getElementById('scanResults').style.display = 'block';
        
        document.getElementById('resDisease').innerText = result.disease;
        document.getElementById('resConfidence').innerText = result.confidence.toFixed(1);
        document.getElementById('resSolution').innerText = result.solution;
        
    } catch(e) {
        console.error("Scan failed", e);
        alert("Scan failed. Please try again.");
        document.getElementById('scanBtn').style.display = 'block';
        document.getElementById('scanLoading').style.display = 'none';
    }
}

function resetScanner() {
    uploadedFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('uploadZone').style.display = 'block';
    document.getElementById('previewZone').style.display = 'none';
    document.getElementById('scanResults').style.display = 'none';
    document.getElementById('scanBtn').style.display = 'block';
}

// Call loadSchemes if we switch to the schemes tab
const originalSwitchTab = window.switchTab;
window.switchTab = function(tabId) {
    if(originalSwitchTab) originalSwitchTab(tabId);
    else {
        document.querySelectorAll('.tab-view').forEach(v => v.style.display = 'none');
        const view = document.getElementById(`view-${tabId}`);
        if(view) view.style.display = 'block';
    }
    
    // Hide controls unless on dashboard
    const controls = document.querySelector('.controls');
    if (controls) {
        controls.style.display = (tabId === 'dashboard') ? 'flex' : 'none';
    }
    
    if (tabId === 'schemes') loadSchemes();
    if (tabId === 'planner') fetchPlannerData();
    if (tabId === 'journey') loadJourney();
    
    // Re-render Lucide icons for dynamically injected content
    if(window.lucide) lucide.createIcons();
};

// --- Crop Journey Logic ---
async function loadJourney() {
    try {
        const res = await authFetch(`${API_URL}/api/v1/journey`);
        const data = await res.json();
        
        if (!data.active) {
            document.getElementById('journeySetup').style.display = 'block';
            document.getElementById('activeJourney').style.display = 'none';
            // Set default date to today
            document.getElementById('journeyStartDate').valueAsDate = new Date();
            return;
        }
        
        document.getElementById('journeySetup').style.display = 'none';
        document.getElementById('activeJourney').style.display = 'block';
        
        document.getElementById('journeyCropName').innerText = data.crop;
        document.getElementById('journeyActiveSoil').innerText = data.soil_type || "Standard";
        document.getElementById('journeyCurrentDay').innerText = data.current_day;
        document.getElementById('journeyTotalDays').innerText = data.total_days;
        document.getElementById('journeyPhaseName').innerText = data.current_phase || "Growth Phase";
        
        document.getElementById('journeyProgressText').innerText = `${data.progress_pct}%`;
        document.getElementById('journeyProgressBar').style.width = `${data.progress_pct}%`;
        
        // Render today's tasks
        const todayContainer = document.getElementById('journeyTodayTasks');
        todayContainer.innerHTML = '';
        if (data.today_tasks && data.today_tasks.length > 0) {
            data.today_tasks.forEach(task => {
                todayContainer.appendChild(createTaskCard(task, true));
            });
        } else {
            todayContainer.innerHTML = '<p style="color: #94a3b8; font-style: italic;">No specific tasks for today. Keep monitoring the crop!</p>';
        }
        
        // Render upcoming tasks
        const upcomingContainer = document.getElementById('journeyUpcomingTasks');
        upcomingContainer.innerHTML = '';
        if (data.upcoming_tasks && data.upcoming_tasks.length > 0) {
            data.upcoming_tasks.forEach(task => {
                upcomingContainer.appendChild(createTaskCard(task, false));
            });
        } else {
            upcomingContainer.innerHTML = '<p style="color: #94a3b8; font-style: italic;">No more upcoming tasks for this journey.</p>';
        }
        
        if(window.lucide) lucide.createIcons();
        
    } catch(e) {
        console.error("Failed to load journey", e);
    }
}

function createTaskCard(task, isToday) {
    const card = document.createElement('div');
    card.style.background = 'rgba(15, 23, 42, 0.6)';
    card.style.border = `1px solid ${isToday ? 'var(--primary-color)' : 'rgba(255,255,255,0.1)'}`;
    card.style.borderRadius = '10px';
    card.style.padding = '1.25rem';
    
    const dayLabel = isToday ? 
        (task.days_until === 0 ? "Today" : (task.days_until < 0 ? `${Math.abs(task.days_until)} days ago` : `In ${task.days_until} days`)) 
        : `In ${task.days_until} days (Day ${task.day})`;
        
    const dayColor = isToday ? 'var(--primary-color)' : '#94a3b8';
    
    const checkboxHtml = isToday ? `
        <button onclick="completeTask('${task.task_id}')" style="background: ${task.completed ? '#10b981' : 'transparent'}; border: 2px solid ${task.completed ? '#10b981' : '#94a3b8'}; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s;">
            <i data-lucide="check" style="color: ${task.completed ? '#0f172a' : 'transparent'}; width: 16px; height: 16px;"></i>
        </button>
    ` : '';
    
    const soilAdviceHtml = task.soil_advice ? `
        <div style="background: rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981; padding: 0.75rem; border-radius: 0 4px 4px 0; margin-top: 0.75rem;">
            <p style="margin: 0; font-size: 0.85rem; color: #cbd5e1;"><strong><i data-lucide="sprout" style="width:14px; height:14px; vertical-align: middle;"></i> Soil Tip:</strong> ${task.soil_advice}</p>
        </div>
    ` : '';

    card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
            <div>
                <span style="font-size: 0.75rem; color: ${dayColor}; font-weight: bold; text-transform: uppercase; letter-spacing: 0.05em;">${dayLabel} &bull; ${task.phase}</span>
                <h4 style="margin: 0.25rem 0; font-size: 1.1rem; ${task.completed ? 'text-decoration: line-through; color: #64748b;' : 'color: white;'}">${task.what}</h4>
            </div>
            ${checkboxHtml}
        </div>
        <div style="display: grid; gap: 0.75rem; ${task.completed ? 'opacity: 0.5;' : ''}">
            <div style="background: rgba(245, 158, 11, 0.1); border-left: 3px solid #f59e0b; padding: 0.75rem; border-radius: 0 4px 4px 0;">
                <p style="margin: 0; font-size: 0.85rem; color: #cbd5e1;"><strong>Why:</strong> ${task.why}</p>
            </div>
            <div style="background: rgba(56, 189, 248, 0.1); border-left: 3px solid #38bdf8; padding: 0.75rem; border-radius: 0 4px 4px 0;">
                <p style="margin: 0; font-size: 0.85rem; color: #cbd5e1;"><strong>How:</strong> ${task.how}</p>
            </div>
            ${soilAdviceHtml}
        </div>
    `;
    return card;
}

async function startJourney() {
    const crop = document.getElementById('journeyCropSelect').value;
    const soilType = document.getElementById('journeySoilSelect').value;
    const startDate = document.getElementById('journeyStartDate').value;
    
    if(!startDate) {
        alert("Please select a start date.");
        return;
    }
    
    try {
        const res = await authFetch(`${API_URL}/api/v1/journey/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ crop, soil_type: soilType, start_date: startDate })
        });
        const data = await res.json();
        if(data.status === 'success') {
            loadJourney();
        } else {
            alert(data.error);
        }
    } catch(e) {
        console.error("Failed to start journey", e);
    }
}

async function stopJourney() {
    if(!confirm("Are you sure you want to end this crop journey?")) return;
    
    try {
        console.log("Attempting to stop journey...");
        const res = await authFetch(`${API_URL}/api/v1/journey/stop`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        console.log("Stop Journey Response:", data);
        
        if(data.status === 'success') {
            alert("Journey successfully ended.");
            // Force a reload of the UI by calling loadJourney
            await loadJourney();
            // Fallback: hide the active view if loadJourney fails to do it
            document.getElementById('activeJourney').style.display = 'none';
            document.getElementById('journeySetup').style.display = 'block';
        } else {
            alert("Could not end journey: " + (data.error || data.message));
        }
    } catch(e) {
        console.error("Failed to stop journey", e);
        alert("Error ending journey: " + e.message);
    }
}

async function completeTask(taskId) {
    try {
        await authFetch(`${API_URL}/api/v1/journey/complete-task`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_id: taskId })
        });
        loadJourney(); // Reload to update UI
    } catch(e) {
        console.error("Failed to complete task", e);
    }
}

// Toggle between Login and Sign Up Forms
function toggleAuthForm(formType) {
    const errorEl = document.getElementById('loginError');
    errorEl.style.display = 'none';
    
    if (formType === 'signup') {
        document.getElementById('loginFormContainer').style.display = 'none';
        document.getElementById('signupFormContainer').style.display = 'block';
    } else {
        document.getElementById('loginFormContainer').style.display = 'block';
        document.getElementById('signupFormContainer').style.display = 'none';
    }
}

// Register a new user and login automatically
async function registerUser() {
    const name = document.getElementById('signupName').value.trim();
    const phone = document.getElementById('signupPhone').value.trim();
    const password = document.getElementById('signupPassword').value.trim();
    const errorEl = document.getElementById('loginError');
    
    if (!name || !phone || !password) {
        errorEl.textContent = "All registration fields are required.";
        errorEl.style.display = 'block';
        return;
    }
    
    try {
        const res = await window.fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ name, phone, password })
        });
        
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Registration failed");
        
        // Auto-fill login fields
        document.getElementById('loginPhone').value = phone;
        document.getElementById('loginPassword').value = password;
        
        // Toggle view back to login and log in
        toggleAuthForm('login');
        
        // Clear registration input fields
        document.getElementById('signupName').value = '';
        document.getElementById('signupPhone').value = '';
        document.getElementById('signupPassword').value = '';
        
        await loginUser();
    } catch(err) {
        errorEl.textContent = err.message;
        errorEl.style.display = 'block';
    }
}

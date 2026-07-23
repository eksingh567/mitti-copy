
// --- IoT Auto-Irrigate Logic ---
let sensorInterval;

function startSensorPolling() {
    if(sensorInterval) clearInterval(sensorInterval);
    sensorInterval = setInterval(fetchRealTimeSensors, 2000);
}

async function fetchRealTimeSensors() {
    try {
        const res = await fetch(`${API_URL}/api/sensors`);
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
    try {
        await fetch(`${API_URL}/api/irrigation/auto`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ auto_irrigate: toggle.checked })
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
        const res = await fetch(`${API_URL}/api/schemes`);
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
    
    // Provide crop context if available
    const plannerSelect = document.getElementById('planner-crop-select');
    if (plannerSelect) formData.append('crop', plannerSelect.value);
    
    try {
        const res = await fetch(`${API_URL}/api/scan-image`, {
            method: 'POST',
            body: formData
        });
        
        if(!res.ok) throw new Error("API Error");
        const result = await res.json();
        
        document.getElementById('scanLoading').style.display = 'none';
        document.getElementById('scanResults').style.display = 'block';
        
        document.getElementById('resDisease').innerText = result.disease;
        document.getElementById('resConfidence').innerText = (result.confidence * 100).toFixed(1);
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
};

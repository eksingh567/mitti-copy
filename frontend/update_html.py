import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add Call Button
call_btn = '''                    <button class="btn-primary" onclick="loadDemoData()">
                        <i data-lucide="refresh-cw"></i> Scan Sensors
                    </button>
                    <button class="btn-primary" style="background: #ef4444; color: white;" onclick="makeEmergencyCall()">
                        <i data-lucide="phone-call"></i> Call Expert
                    </button>'''
html = html.replace('''                    <button class="btn-primary" onclick="loadDemoData()">
                        <i data-lucide="refresh-cw"></i> Scan Sensors
                    </button>''', call_btn)

# 2. Add Wisdom & Advisories card right after the Active Soil Profile
wisdom_card = '''                <!-- Wisdom & Advisories -->
                <section class="card wisdom-card full-width">
                    <div class="card-header" style="color: #facc15;">
                        <i data-lucide="sun"></i>
                        <h3>Daily Wisdom & Advisories</h3>
                    </div>
                    <div style="background: rgba(250, 204, 21, 0.05); border-left: 4px solid #facc15; padding: 1.5rem; border-radius: 8px;">
                        <p id="dashboard-wisdom" style="font-size: 1.1rem; font-style: italic; color: #fef08a; margin-bottom: 1rem;">"Wisdom quote here"</p>
                        <ul id="dashboard-advisories" style="list-style-type: none; margin: 0; padding: 0; color: #f3f4f6; line-height: 1.6;">
                            <!-- Populated via JS -->
                        </ul>
                    </div>
                </section>'''

html = html.replace('<!-- NPK Levels -->', wisdom_card + '\n\n                <!-- NPK Levels -->')

# 3. Add IDs and onclicks to Sidebar for Tabs
sidebar_old = '''            <ul class="nav-links">
                <li class="active"><i data-lucide="layout-dashboard"></i> Dashboard</li>
                <li><i data-lucide="map"></i> Region Map</li>
                <li><i data-lucide="history"></i> History</li>
                <li><i data-lucide="settings"></i> Settings</li>
            </ul>'''
sidebar_new = '''            <ul class="nav-links">
                <li id="tab-dashboard" class="active" onclick="switchTab('dashboard')"><i data-lucide="layout-dashboard"></i> Dashboard</li>
                <li id="tab-encyclopedia" onclick="switchTab('encyclopedia')"><i data-lucide="book-open"></i> Crop Encyclopedia</li>
                <li id="tab-history" onclick="switchTab('history')"><i data-lucide="history"></i> Yield History</li>
            </ul>'''
html = html.replace(sidebar_old, sidebar_new)

# 4. Wrap dashboard grid and engine card in a tab container, and add new tabs
dashboard_wrap_start = '''            <!-- Tab Views -->
            <div id="view-dashboard" class="tab-view active">
            <!-- Dashboard Grid -->'''
html = html.replace('<!-- Dashboard Grid -->', dashboard_wrap_start)

# Finding the end of the engine card to close the dashboard div and start new divs
engine_end = '''            </section>'''
new_views = '''            </section>
            </div> <!-- End view-dashboard -->

            <!-- Encyclopedia View -->
            <div id="view-encyclopedia" class="tab-view" style="display: none;">
                <section class="card full-width">
                    <div class="card-header">
                        <i data-lucide="book-open"></i>
                        <h3>Mitti Crop Encyclopedia</h3>
                    </div>
                    <p style="margin-bottom: 1.5rem; color: var(--text-muted);">Learn about the specific soil, water, and regional needs of all major Indian crops.</p>
                    <div class="crops-container" id="encyclopediaGrid" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
                        <!-- Populated by JS -->
                    </div>
                </section>
            </div>

            <!-- History View -->
            <div id="view-history" class="tab-view" style="display: none;">
                <div class="dashboard-grid">
                    <section class="card">
                        <div class="card-header">
                            <i data-lucide="plus-circle"></i>
                            <h3>Log New Yield</h3>
                        </div>
                        <form id="yieldForm" onsubmit="submitYield(event)" style="display: flex; flex-direction: column; gap: 1rem;">
                            <div class="control-group">
                                <label>Crop</label>
                                <input type="text" id="yieldCrop" required style="padding: 0.75rem; background: var(--bg-card); border: 1px solid var(--border); color: white; border-radius: 8px;">
                            </div>
                            <div class="control-group">
                                <label>Season</label>
                                <select id="yieldSeason" style="padding: 0.75rem;">
                                    <option value="Kharif">Kharif</option>
                                    <option value="Rabi">Rabi</option>
                                    <option value="Zaid">Zaid</option>
                                </select>
                            </div>
                            <div class="control-group">
                                <label>Yield Amount (Quintals)</label>
                                <input type="number" id="yieldAmount" required min="1" style="padding: 0.75rem; background: var(--bg-card); border: 1px solid var(--border); color: white; border-radius: 8px;">
                            </div>
                            <button type="submit" class="btn-primary" style="margin-top: 1rem;"><i data-lucide="save"></i> Save Record</button>
                        </form>
                    </section>
                    
                    <section class="card">
                        <div class="card-header">
                            <i data-lucide="bar-chart-2"></i>
                            <h3>Past Yield Records</h3>
                        </div>
                        <div id="historyList" style="display: flex; flex-direction: column; gap: 1rem;">
                            <!-- Populated by JS -->
                        </div>
                    </section>
                </div>
            </div>'''
html = html.replace(engine_end, new_views, 1)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated index.html with new tabs and sections")

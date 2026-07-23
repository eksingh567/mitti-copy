import re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# We want to replace everything from <!-- History View --> down to </main>
target_regex = re.compile(r'<!-- History View -->.*?</main>', re.DOTALL)

replacement = """<!-- History View -->
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
                    
                    <!-- Smart Next Crop Suggestion -->
                    <section class="card full-width" style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.08), rgba(6, 95, 70, 0.08)); border: 1px solid var(--primary-color);">
                        <div class="card-header">
                            <i data-lucide="brain-circuit"></i>
                            <h3 style="color: var(--primary-color);">Smart Next Crop Suggestion</h3>
                        </div>
                        <p style="color: #94a3b8; margin-bottom: 1.5rem;">Based on your past crop history, soil type, and the upcoming season, here is what you should grow next:</p>
                        
                        <div id="smartSuggestionContent" style="display: flex; flex-direction: column; gap: 1rem;">
                            <p style="color: #64748b; font-style: italic;">Log at least one yield record above to get personalized suggestions.</p>
                        </div>
                    </section>
                </div>
            </div>

            <!-- Planner View -->
            <div id="view-planner" class="tab-view" style="display: none;">
                <!-- Global Soil Knowledge Toggle for Planner -->
                <div style="display: flex; justify-content: flex-end; margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; background: rgba(15, 23, 42, 0.4); padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid var(--border);">
                        <label style="margin: 0; font-size: 0.9rem;">I know my soil type</label>
                        <label class="switch" style="transform: scale(0.8);">
                            <input type="checkbox" id="globalSoilKnowledgeToggle" checked onchange="handleSoilKnowledgeChange()">
                            <span class="slider round"></span>
                        </label>
                    </div>
                </div>

                <div class="dashboard-grid">
                    
                    <!-- Top section: Smart Crop Suggester -->
                    <section class="card full-width" style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 1rem; background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(6, 95, 70, 0.1)); border: 1px solid var(--primary-color);">
                        <div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; flex: 2;">
                            <h3 style="color: var(--primary-color); margin: 0; white-space: nowrap;"><i data-lucide="brain-circuit"></i> Smart Suggester</h3>
                            
                            <!-- Filter: Season -->
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <label style="font-size: 0.9rem; color: #94a3b8;">Upcoming Season:</label>
                                <select id="planner-season-filter" class="theme-select" style="padding: 0.4rem 0.8rem; border-radius: 6px; font-size: 0.9rem;" onchange="filterPlannerCrops()">
                                    <option value="All">All Seasons</option>
                                    <option value="Kharif">Kharif (Jun - Oct)</option>
                                    <option value="Rabi">Rabi (Oct - Mar)</option>
                                    <option value="Zaid">Zaid (Mar - Jun)</option>
                                </select>
                            </div>
                            
                            <!-- Filter: Soil -->
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <label style="font-size: 0.9rem; color: #94a3b8;">Soil Type:</label>
                                <select id="planner-soil-filter" class="theme-select" style="padding: 0.4rem 0.8rem; border-radius: 6px; font-size: 0.9rem;" onchange="filterPlannerCrops()">
                                    <option value="All">Any Soil</option>
                                    <option value="Alluvial Soil (Fertile)">Alluvial</option>
                                    <option value="Black Soil (Regur)">Black</option>
                                    <option value="Red & Yellow Soil">Red & Yellow</option>
                                    <option value="Laterite Soil">Laterite</option>
                                    <option value="Arid/Desert Soil">Arid/Desert</option>
                                </select>
                            </div>
                        </div>
                        
                        <!-- Filtered Results Dropdown -->
                        <div style="flex: 1; text-align: right; min-width: 250px;">
                            <label for="planner-crop-select" style="font-weight: 500; margin-right: 0.5rem; color: #34d399;">Suggested Crop:</label>
                            <select id="planner-crop-select" class="theme-select" style="padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.5); background: rgba(15, 23, 42, 0.9); color: var(--text-color); font-size: 1rem; font-weight: bold; width: 100%; max-width: 200px;" onchange="updatePlanner()">
                                <!-- Populated by JS -->
                            </select>
                        </div>
                    </section>
                    
                    <!-- Left: Seasonal Timeline -->
                    <section class="card" style="grid-column: span 2;">
                        <div class="card-header">
                            <i data-lucide="calendar-days"></i>
                            <h3>Seasonal Timeline</h3>
                        </div>
                        <div class="timeline-container">
                            <div class="timeline-grid" id="timelineGrid">
                                <!-- Generated by JS -->
                            </div>
                            <div class="timeline-legend" style="display: flex; gap: 1rem; margin-top: 1.5rem; justify-content: center; font-size: 0.9rem;">
                                <div style="display: flex; align-items: center; gap: 0.5rem;"><span style="width: 12px; height: 12px; background: #3b82f6; border-radius: 3px;"></span> Sowing</div>
                                <div style="display: flex; align-items: center; gap: 0.5rem;"><span style="width: 12px; height: 12px; background: #f59e0b; border-radius: 3px;"></span> Harvesting</div>
                            </div>
                        </div>
                    </section>
                    
                    <!-- Farm School -->
                    <section class="card" style="grid-column: span 2;">
                        <div class="card-header">
                            <i data-lucide="graduation-cap"></i>
                            <h3>Farm School</h3>
                        </div>
                        <div id="farmSchoolContent" style="display: flex; flex-direction: column; gap: 1rem; margin-top: 1rem;">
                            <!-- Populated by JS -->
                            <p style="color: var(--text-muted); font-style: italic;">Select a crop to view the educational guide.</p>
                        </div>
                    </section>
                </div>
            </div>

            <!-- AI Scanner View -->
            <div id="view-scanner" class="tab-view" style="display: none;">
                <div class="card" style="max-width: 600px; margin: 0 auto; text-align: center; padding: 2rem;">
                    <h2><i data-lucide="scan-line"></i> Crop Disease AI Scanner</h2>
                    <p style="color: #94a3b8; margin-bottom: 2rem;">Upload an image of a sick leaf to instantly identify the disease.</p>
                    
                    <div class="upload-zone" id="uploadZone" onclick="document.getElementById('fileInput').click()" style="border: 2px dashed #10b981; border-radius: 12px; padding: 3rem 1rem; cursor: pointer; transition: all 0.3s; background: rgba(16, 185, 129, 0.05);">
                        <i data-lucide="upload-cloud" style="width: 48px; height: 48px; color: #10b981; margin-bottom: 1rem;"></i>
                        <h4 style="margin: 0;">Click or Drag image to upload</h4>
                        <p style="color: #64748b; font-size: 0.9rem; margin-top: 0.5rem;">Supports JPG, PNG</p>
                        <input type="file" id="fileInput" accept="image/*" style="display: none;" onchange="handleFileUpload(event)">
                    </div>
                    
                    <!-- Preview -->
                    <div id="previewZone" style="display: none; margin-top: 2rem;">
                        <img id="imagePreview" src="" alt="Preview" style="max-width: 100%; border-radius: 8px; border: 2px solid #334155; margin-bottom: 1rem;">
                        <button class="btn-primary" onclick="startScan()" id="scanBtn" style="width: 100%; font-size: 1.1rem; padding: 1rem;"><i data-lucide="cpu"></i> Analyze Image</button>
                    </div>
                    
                    <!-- Loading -->
                    <div id="scanLoading" style="display: none; margin-top: 2rem;">
                        <div class="scanner-laser"></div>
                        <p style="color: #10b981; font-weight: bold; margin-top: 1rem;">Analyzing leaf structure...</p>
                    </div>
                    
                    <!-- Results -->
                    <div id="scanResults" style="display: none; margin-top: 2rem; background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; border-radius: 8px; padding: 1.5rem; text-align: left;">
                        <h3 style="color: #ef4444; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; margin-bottom: 1rem;"><i data-lucide="alert-circle"></i> Diagnosis Result</h3>
                        <p><strong>Detected Issue:</strong> <span id="resDisease" style="color: #fca5a5;"></span></p>
                        <p><strong>AI Confidence:</strong> <span id="resConfidence" style="color: #10b981;"></span>%</p>
                        <div style="margin-top: 1rem; padding: 1rem; background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; border-radius: 4px;">
                            <strong style="color: #34d399;">Recommended Solution:</strong>
                            <p id="resSolution" style="margin-top: 0.5rem; font-size: 0.95rem; line-height: 1.5;"></p>
                        </div>
                        <button class="btn-primary" onclick="resetScanner()" style="margin-top: 1.5rem; background: #334155; border-color: #475569;">Scan Another</button>
                    </div>
                </div>
            </div>

            <!-- Gov Schemes View -->
            <div id="view-schemes" class="tab-view" style="display: none;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
                    <h2><i data-lucide="landmark"></i> Government Schemes & Subsidies</h2>
                    <p style="color: #94a3b8;">Discover financial aid and resources available for your farm.</p>
                </div>
                <div class="dashboard-grid" id="schemesContainer">
                    <!-- Schemes rendered by JS -->
                    <div style="grid-column: span 2; text-align: center; color: #94a3b8;"><i data-lucide="loader" class="spin"></i> Loading schemes...</div>
                </div>
            </div>

            <!-- Crop Journey View -->
            <div id="view-journey" class="tab-view" style="display: none;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h2><i data-lucide="footprints"></i> My Crop Journey</h2>
                    <p style="color: #94a3b8;">Daily guidance from sowing to harvest.</p>
                </div>
                
                <div id="journeySetup" class="card" style="margin-bottom: 2rem; display: none;">
                    <h3>Start a New Journey</h3>
                    <p style="color: #94a3b8; margin-bottom: 1rem;">Select a crop and start date to get personalized daily reminders.</p>
                    <div style="display: flex; gap: 1rem; align-items: flex-end;">
                        <div class="control-group" style="flex: 1;">
                            <label>Crop</label>
                            <select id="journeyCropSelect" style="padding: 0.75rem;">
                                <option value="Wheat">Wheat</option>
                                <option value="Paddy">Paddy</option>
                                <option value="Mango">Mango</option>
                                <option value="Cotton">Cotton</option>
                            </select>
                        </div>
                        <div class="control-group" style="flex: 1;">
                            <label>Soil Type</label>
                            <select id="journeySoilSelect" style="padding: 0.75rem;">
                                <option value="Alluvial">Alluvial (Loamy)</option>
                                <option value="Black">Black (Clayey)</option>
                                <option value="Red">Red (Sandy/Porous)</option>
                                <option value="Laterite">Laterite (Acidic)</option>
                            </select>
                        </div>
                        <div class="control-group" style="flex: 1;">
                            <label>Start Date</label>
                            <input type="date" id="journeyStartDate" style="padding: 0.75rem; background: var(--bg-card); border: 1px solid var(--border); color: white; border-radius: 8px;">
                        </div>
                        <button class="btn-primary" onclick="startJourney()" style="height: 45px;"><i data-lucide="play"></i> Start Journey</button>
                    </div>
                </div>

                <div id="activeJourney" style="display: none;">
                    <div class="card" style="margin-bottom: 1rem; background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(6, 95, 70, 0.1)); border: 1px solid var(--primary-color);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                            <div>
                                <h3 style="color: var(--primary-color); font-size: 1.5rem; margin-bottom: 0.25rem;">
                                    <span id="journeyCropName">Wheat</span> 
                                    <span style="font-size: 0.9rem; color: #94a3b8; font-weight: normal; margin-left: 0.5rem; border: 1px solid #475569; padding: 0.2rem 0.5rem; border-radius: 4px;">Soil: <span id="journeyActiveSoil">Unknown</span></span>
                                </h3>
                                <p style="color: #94a3b8;">Day <span id="journeyCurrentDay" style="color: white; font-weight: bold;">12</span> of <span id="journeyTotalDays">150</span></p>
                            </div>
                            <button class="btn-primary" onclick="stopJourney()" style="background: rgba(239, 68, 68, 0.2); border-color: rgba(239, 68, 68, 0.5); color: #fca5a5;"><i data-lucide="stop-circle"></i> End Journey</button>
                        </div>
                        <div style="background: rgba(15, 23, 42, 0.5); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.85rem;">
                                <span>Progress</span>
                                <span id="journeyProgressText">8%</span>
                            </div>
                            <div style="height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden;">
                                <div id="journeyProgressBar" style="height: 100%; width: 8%; background: var(--primary-color); border-radius: 4px; transition: width 0.3s ease;"></div>
                            </div>
                        </div>
                        <p style="color: #34d399; font-weight: bold;"><i data-lucide="map-pin"></i> Current Phase: <span id="journeyPhaseName">Vegetative Growth</span></p>
                    </div>
                    
                    <h3 style="margin: 2rem 0 1rem 0;"><i data-lucide="sun"></i> Today's Tasks</h3>
                    <div id="journeyTodayTasks" style="display: flex; flex-direction: column; gap: 1rem;">
                        <!-- Tasks go here -->
                    </div>

                    <h3 style="margin: 2rem 0 1rem 0; color: #94a3b8;"><i data-lucide="calendar-clock"></i> Upcoming Tasks</h3>
                    <div id="journeyUpcomingTasks" style="display: flex; flex-direction: column; gap: 1rem; opacity: 0.8;">
                        <!-- Upcoming Tasks go here -->
                    </div>
                </div>
            </div>
        </main>"""

new_html, count = target_regex.subn(replacement, html)

if count > 0:
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"Successfully fixed index.html (replaced {count} occurrences)")
else:
    print("Failed to find the target string to replace.")

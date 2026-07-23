import re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# I will find the exact string to replace. I know the HTML is broken around view-history and view-planner.
# Let's restore the end of view-history and the start of view-planner.

# The current broken HTML looks like:
#                         <p style="color: #94a3b8; margin-bottom: 1.5rem;">Based on your past crop history, soil type, and the upcoming season, here is what you should grow next:</p>
#                         
#                         <div id="smartSuggestionContent" style="display: flex; flex-direction: column; gap: 1rem;">
#                             </select>
#                         </div>
#                     </section>

# I need to restore the full structure from line 340 onwards. Let's just rewrite the end of view-history and the start of view-planner completely.

target_regex = re.compile(r'<div id="smartSuggestionContent" style="display: flex; flex-direction: column; gap: 1rem;">.*?</div>\s*</section>\s*</div>\s*</div>', re.DOTALL)

replacement = """<div id="smartSuggestionContent" style="display: flex; flex-direction: column; gap: 1rem;">
                            <p style="color: #64748b; font-style: italic;">Log at least one yield record above to get personalized suggestions.</p>
                        </div>
                    </section>
                </div>
            </div>

            <!-- Planner View -->
            <div id="view-planner" class="tab-view" style="display: none;">
                
                <!-- Toggle placed at the very top of Planner view -->
                <div style="display: flex; justify-content: flex-end; margin-bottom: 1.5rem; padding-right: 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.75rem; background: rgba(15, 23, 42, 0.7); padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid var(--primary-color);">
                        <label style="margin: 0; font-size: 0.95rem; color: #fff; font-weight: bold;"><i data-lucide="test-tube" style="width: 16px; height: 16px; display: inline-block; vertical-align: middle; margin-right: 4px;"></i> I know my soil type</label>
                        <label class="switch" style="margin: 0;">
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
"""

# Wait, the broken code in index.html currently is:
#                         <div id="smartSuggestionContent" style="display: flex; flex-direction: column; gap: 1rem;">
#                             </select>
#                         </div>
#                     </section>
#                     
#                     <!-- Left: Seasonal Timeline -->

# Let's replace from <div id="smartSuggestionContent" ... up to just before Left: Seasonal Timeline.

target_regex_2 = re.compile(r'<div id="smartSuggestionContent" style="display: flex; flex-direction: column; gap: 1rem;">.*?</select>\s*</div>\s*</section>', re.DOTALL)

new_html, count = target_regex_2.subn(replacement, html)

if count > 0:
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"Successfully fixed index.html (replaced {count} occurrences)")
else:
    print("Failed to find the target string to replace.")


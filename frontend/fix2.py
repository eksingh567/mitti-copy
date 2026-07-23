import re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# The broken HTML currently looks like this around line 380-399:
#             <!-- AI Scanner View -->
#             <div id="view-scanner" class="tab-view" style="display: none;">
#                 <div class="card" style="max-width: 600px; margin: 0 auto; text-align: center; padding: 2rem;">
#                     <h2><i data-lucide="scan-line"></i> Crop Disease AI Scanner</h2>
#                     <p style="color: #94a3b8; margin-bottom: 2rem;">Upload an image of a sick leaf to instantly identify the disease.</p>
#                     
#                     <div class="upload-zone" id="uploadZone" onclick="document.getElementById('fileInput').click()" style="border: 2px dashed #10b981; border-radius: 12px; padding: 3rem 1rem; cursor: pointer; transition: all 0.3s; background: rgba(16, 185, 129, 0.05);">
#                         <i data-lucide="upload-cloud" style="width: 48px; height: 48px; color: #10b981; margin-bottom: 1rem;"></i>
#                         <h4 style="margin: 0;">Click or Drag image to upload</h4>
#                         <p style="color: #64748b; font-size: 0.9rem; margin-top: 0.5rem;">Supports JPG, PNG</p>
#                 <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
#                     <h2><i data-lucide="landmark"></i> Government Schemes & Subsidies</h2>
#                     <p style="color: #94a3b8;">Discover financial aid and resources available for your farm.</p>
#                 </div>

# We need to replace from "<!-- AI Scanner View -->" down to right before "<!-- Crop Journey View -->"
target_regex = re.compile(r'<!-- AI Scanner View -->.*?<!-- Crop Journey View -->', re.DOTALL)

replacement = """<!-- AI Scanner View -->
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

            <!-- Crop Journey View -->"""

new_html, count = target_regex.subn(replacement, html)

if count > 0:
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"Successfully fixed index.html (replaced {count} occurrences)")
else:
    print("Failed to find the target string to replace.")

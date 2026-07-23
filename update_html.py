import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

new_controls = """
                  <div class="controls">
                      <div class="control-group">
                          <label>State</label>
"""

# Insert Advanced Filters below the Season select
advanced_filters = """
                      <div class="control-group">
                          <label>Soil Profile</label>
                          <select id="soilSelect">
                              <option value="Auto">Auto-Detect (Sensor)</option>
                              <option value="Alluvial Soil (Fertile)">Alluvial Soil</option>
                              <option value="Black Soil (Regur)">Black Soil (Regur)</option>
                              <option value="Red & Yellow Soil">Red & Yellow Soil</option>
                              <option value="Laterite Soil">Laterite Soil</option>
                              <option value="Arid / Desert Soil">Arid / Desert Soil</option>
                              <option value="Forest/Mountain Soil">Forest/Mountain Soil</option>
                              <option value="Saline/Alkaline Soil">Saline/Alkaline Soil</option>
                              <option value="Peaty/Marshy Soil">Peaty/Marshy Soil</option>
                              <option value="Coastal Sandy Soil">Coastal Sandy Soil</option>
                          </select>
                      </div>
                      <div class="control-group">
                          <label>Water Availability</label>
                          <select id="waterSelect">
                              <option value="Any">Any</option>
                              <option value="Low">Low (Rainfed)</option>
                              <option value="Medium">Medium</option>
                              <option value="High">High (Irrigated)</option>
                          </select>
                      </div>
                      <div class="control-group">
                          <label>Crop Category</label>
                          <select id="typeSelect">
                              <option value="Any">Any</option>
                              <option value="Cereal">Cereals</option>
                              <option value="Pulse">Pulses</option>
                              <option value="Spice">Spices</option>
                              <option value="Vegetable">Vegetables</option>
                              <option value="Cash Crop">Cash Crops</option>
                              <option value="Oilseed">Oilseeds</option>
                              <option value="Plantation">Plantation</option>
                          </select>
                      </div>
                  </div>
"""

# Replace the closing div of controls
html = html.replace('</select>\n                      </div>\n                  </div>', '</select>\n                      </div>' + advanced_filters)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Added advanced filters to index.html!")

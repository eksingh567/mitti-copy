import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Insert Phenomenon Dropdown below the Category select
advanced_filters = """
                    <div class="control-group">
                        <label>Category</label>
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
                    <div class="control-group">
                        <label>Local Weather</label>
                        <select id="phenomenonSelect">
                            <option value="None">None / Normal</option>
                            <option value="Mango Showers">Mango Showers (South)</option>
                            <option value="Kal Baisakhi">Kal Baisakhi (East)</option>
                            <option value="Western Disturbances">Western Disturbances (North)</option>
                            <option value="Loo">Loo Hot Winds (North/West)</option>
                        </select>
                    </div>
"""

# We replace the typeSelect control group block
old_type_select = """                    <div class="control-group">
                        <label>Category</label>
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
                    </div>"""

html = html.replace(old_type_select, advanced_filters)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Added Phenomenon dropdown to index.html!")

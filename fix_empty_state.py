import re

with open('frontend/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

old_render = """function renderCropsGrid(data) {
    cropsGrid.innerHTML = '';
    
    // Convert to array and sort by score
    const sortedCrops = Object.entries(data).sort((a,b) => b[1].score - a[1].score);
    
    sortedCrops.forEach(([cropKey, details], index) => {"""

new_render = """function renderCropsGrid(data) {
    cropsGrid.innerHTML = '';
    
    // Convert to array and sort by score
    const sortedCrops = Object.entries(data).sort((a,b) => b[1].score - a[1].score);
    
    if (sortedCrops.length === 0) {
        cropsGrid.innerHTML = '<div style="color: #9ca3af; text-align: center; padding: 2rem; grid-column: 1 / -1;">No crops perfectly match these strict filters. Try adjusting your Water or Category selections.</div>';
        cropDetailsPanel.style.display = 'none';
        return;
    }
    
    sortedCrops.forEach(([cropKey, details], index) => {"""

if old_render in js:
    js = js.replace(old_render, new_render)
else:
    print("Could not find exact old_render string.")
    
with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated app.js to handle empty filters!")

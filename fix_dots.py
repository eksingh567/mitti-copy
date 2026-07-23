import re

with open('frontend/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Find the renderCropsGrid function
old_render = """function renderCropsGrid(data) {
    cropsGrid.innerHTML = '';
    
    // Convert to array and sort by score
    const sortedCrops = Object.entries(data).sort((a,b) => b[1].score - a[1].score);
    
    sortedCrops.forEach(([cropKey, details], index) => {
        const btn = document.createElement('button');
        btn.className = `crop-btn ${index === 0 ? 'active' : ''}`;
        btn.id = `btn-${cropKey}`;
        btn.onclick = () => selectCrop(cropKey);
        
        btn.innerHTML = `
            <span>${details.name_en || cropKey}</span>
            <span class="score">${details.score}%</span>
        `;
        cropsGrid.appendChild(btn);
        
        if(index === 0) selectCrop(cropKey); // Auto-select first
    });
}"""

new_render = """function renderCropsGrid(data) {
    cropsGrid.innerHTML = '';
    
    // Convert to array and sort by score
    const sortedCrops = Object.entries(data).sort((a,b) => b[1].score - a[1].score);
    
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
}"""

if old_render in js:
    js = js.replace(old_render, new_render)
else:
    # Use regex if exact match fails
    js = re.sub(r'function renderCropsGrid\(data\).*?if\(index === 0\) selectCrop\(cropKey\); // Auto-select first\s*\}\);\s*\}', new_render, js, flags=re.DOTALL)

with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated app.js to use colored dots instead of percentages!")

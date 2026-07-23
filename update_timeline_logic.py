import re

with open('frontend/app.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace the timeline rendering block
old_block = """        months.forEach(m => {
            let classes = 'timeline-month';
            if (sowing.includes(m)) classes += ' sowing';
            if (harvesting.includes(m)) classes += ' harvesting';
            grid.innerHTML += `<div class="${classes}">${m}</div>`;
        });"""

new_block = """        let sowingStepCount = 1;
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
        });"""

code = code.replace(old_block, new_block)

with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(code)
print("Updated timeline logic")

import re

with open('frontend/app.js', 'r', encoding='utf-8') as f:
    code = f.read()

old_block = """    // 2. Render Farm School
    const school = document.getElementById('farmSchoolContent');
    if (school) {
        school.innerHTML = '';
        const steps = crop.farm_school_steps || [];
        if (steps.length > 0) {
            steps.forEach(step => {
                school.innerHTML += `<div class="farm-step">${step}</div>`;
            });
        } else {
            school.innerHTML = '<p style="color: var(--text-muted);">Educational guide not available for this crop yet.</p>';
        }
    }"""

new_block = """    // 2. Render Farm School (Rich)
    const school = document.getElementById('farmSchoolContent');
    if (school) {
        school.innerHTML = '';
        const fs = crop.farm_school;
        
        if (fs && fs.steps && fs.steps.length > 0) {
            // Steps Section
            let stepsHtml = '<div class="farm-school-section"><div class="farm-school-title"><i data-lucide="list-ordered"></i> Growing Steps</div>';
            fs.steps.forEach((step, idx) => {
                stepsHtml += `
                    <div class="fs-step-card">
                        <div class="fs-step-header"><span>Step ${idx + 1}: ${step.title}</span></div>
                        <div class="fs-step-desc">${step.desc}</div>
                        <div class="fs-step-why"><strong>🧠 The "Why":</strong> ${step.why}</div>
                    </div>
                `;
            });
            stepsHtml += '</div>';
            school.innerHTML += stepsHtml;
            
            // Challenges Section
            if (fs.challenges && fs.challenges.length > 0) {
                let chalHtml = '<div class="farm-school-section"><div class="farm-school-title" style="color: #ef4444; border-color: rgba(239, 68, 68, 0.2);"><i data-lucide="alert-triangle"></i> Key Challenges</div><div class="fs-tags">';
                fs.challenges.forEach(c => {
                    chalHtml += `<span class="fs-tag">${c}</span>`;
                });
                chalHtml += '</div></div>';
                school.innerHTML += chalHtml;
            }
            
            // Fertilizers Section
            if (fs.fertilizers) {
                school.innerHTML += `
                    <div class="farm-school-section">
                        <div class="farm-school-title" style="color: #3b82f6; border-color: rgba(59, 130, 246, 0.2);"><i data-lucide="flask-conical"></i> Nutrients & Fertilizers</div>
                        <div class="fs-info-box">${fs.fertilizers}</div>
                    </div>
                `;
            }
            
            // Soil Tips Section
            if (fs.soil_tips) {
                school.innerHTML += `
                    <div class="farm-school-section">
                        <div class="farm-school-title" style="color: #f59e0b; border-color: rgba(245, 158, 11, 0.2);"><i data-lucide="sprout"></i> Soil Replenishment</div>
                        <div class="fs-info-box">${fs.soil_tips}</div>
                    </div>
                `;
            }
            
            lucide.createIcons(); // re-init icons for dynamic content
            
        } else {
            school.innerHTML = '<p style="color: var(--text-muted);">Educational guide not available for this crop yet.</p>';
        }
    }"""

code = code.replace(old_block, new_block)

with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated app.js with rich farm school rendering")

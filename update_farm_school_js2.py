import re

with open('frontend/app.js', 'r', encoding='utf-8') as f:
    code = f.read()

old_block = """            // Challenges Section
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
            }"""

new_block = """            // Challenges Section (Interactive)
            if (fs.challenges && fs.challenges.length > 0) {
                let chalHtml = '<div class="farm-school-section"><div class="farm-school-title" style="color: #ef4444; border-color: rgba(239, 68, 68, 0.2);"><i data-lucide="alert-triangle"></i> Key Challenges</div><div class="fs-challenges-list" style="display: flex; flex-direction: column; gap: 0.5rem;">';
                fs.challenges.forEach(c => {
                    chalHtml += `
                        <details class="fs-challenge-details" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 0.5rem;">
                            <summary style="cursor: pointer; color: #fca5a5; font-weight: bold; outline: none; list-style: none; display: flex; align-items: center; gap: 0.5rem;">
                                <i data-lucide="help-circle" style="width: 16px; height: 16px;"></i> ${c.issue}
                            </summary>
                            <div style="margin-top: 0.5rem; padding-left: 1.5rem; color: #f87171; font-size: 0.9rem;">
                                <strong>Solution:</strong> ${c.solution}
                            </div>
                        </details>
                    `;
                });
                chalHtml += '</div></div>';
                school.innerHTML += chalHtml;
            }"""

code = code.replace(old_block, new_block)

with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated app.js with interactive challenges and removed fertilizers")

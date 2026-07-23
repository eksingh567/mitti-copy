import re

with open('app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Update selectCrop function to render the detailed feedback_list
old_select = '''    cropDetailsPanel.style.display = 'block';
    document.getElementById('detailName').innerText = details.name_hi || details.name_en || cropKey;
    document.getElementById('detailFeedback').innerText = details.feedback || "No feedback available.";
    document.getElementById('detailPh').innerText = details.ph_range || "N/A";'''

new_select = '''    cropDetailsPanel.style.display = 'block';
    document.getElementById('detailName').innerText = details.name_hi || details.name_en || cropKey;
    
    // Render detailed actionable feedback
    const feedbackEl = document.getElementById('detailFeedback');
    if(details.feedback_list && details.feedback_list.length > 0) {
        feedbackEl.innerHTML = '<strong style="color: #facc15;">Required Actions:</strong><ul style="margin-top: 0.5rem; padding-left: 1.5rem; color: #d1d5db;">' + details.feedback_list.map(f => <li></li>).join('') + '</ul>';
    } else {
        feedbackEl.innerText = details.feedback || "No feedback available.";
    }
    
    document.getElementById('detailPh').innerText = details.ph_range || "N/A";'''

js = js.replace(old_select, new_select)

with open('app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated app.js to show detailed deficiency list")

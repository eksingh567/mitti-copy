import re

with open('frontend/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

# 1. Update root variables for a much greener, vibrant theme
old_root = """:root {
    --bg-dark: #0a0e17;
    --bg-card: rgba(16, 24, 39, 0.7);
    --primary: #10b981;
    --primary-glow: rgba(16, 185, 129, 0.3);
    --text-main: #f3f4f6;
    --text-muted: #9ca3af;
    --border: rgba(255, 255, 255, 0.08);
}"""

new_root = """:root {
    --bg-dark: #04120c; /* Deep forest green black */
    --bg-card: rgba(6, 36, 24, 0.6); /* Tinted green glass */
    --primary: #10b981;
    --primary-glow: rgba(16, 185, 129, 0.5);
    --text-main: #ecfdf5;
    --text-muted: #a7f3d0; /* Muted green */
    --border: rgba(16, 185, 129, 0.2);
}"""

css = css.replace(old_root, new_root)

# 2. Update body background gradient for a richer green feel
old_body_bg = """    background-image: 
        radial-gradient(circle at 15% 50%, rgba(16, 185, 129, 0.05), transparent 25%),
        radial-gradient(circle at 85% 30%, rgba(59, 130, 246, 0.05), transparent 25%);"""

new_body_bg = """    background-image: 
        radial-gradient(circle at 15% 50%, rgba(16, 185, 129, 0.15), transparent 35%),
        radial-gradient(circle at 85% 30%, rgba(5, 150, 105, 0.15), transparent 35%),
        radial-gradient(circle at 50% 100%, rgba(4, 120, 87, 0.1), transparent 40%);"""

css = css.replace(old_body_bg, new_body_bg)

# 3. Update top-header to wrap beautifully
old_top_header = """.top-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 2.5rem;
}"""

new_top_header = """.top-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 2.5rem;
    flex-wrap: wrap;
    gap: 2rem;
}"""

css = css.replace(old_top_header, new_top_header)

# 4. Update .controls to fix the squished alignment and give it a premium container
old_controls = """.controls {
    display: flex;
    gap: 1.5rem;
    align-items: flex-end;
}"""

new_controls = """.controls {
    display: flex;
    gap: 1.25rem;
    align-items: flex-end;
    flex-wrap: wrap;
    background: rgba(16, 185, 129, 0.05);
    padding: 1.5rem;
    border-radius: 16px;
    border: 1px solid var(--border);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    flex-grow: 1;
    max-width: 100%;
}"""

css = css.replace(old_controls, new_controls)

# 5. Make selects look premium
old_select = """select {
    appearance: none;
    background: var(--bg-card);
    border: 1px solid var(--border);"""

new_select = """select {
    appearance: none;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--border);
    transition: all 0.3s ease;"""

css = css.replace(old_select, new_select)

# Add hover effect for select
if "select:hover" not in css:
    css += """
select:hover, select:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
    outline: none;
}
"""

with open('frontend/style.css', 'w', encoding='utf-8') as f:
    f.write(css)

print("Applied premium green aesthetic and fixed alignments!")

with open('frontend/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

new_css = """
/* --- Toggle Switch --- */
.switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 22px;
}
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255,255,255,0.1);
  transition: .4s;
  border: 1px solid rgba(255,255,255,0.2);
}
.slider:before {
  position: absolute;
  content: "";
  height: 14px;
  width: 14px;
  left: 3px;
  bottom: 3px;
  background-color: #cbd5e1;
  transition: .4s;
}
input:checked + .slider {
  background-color: #3b82f6;
  border-color: #3b82f6;
}
input:checked + .slider:before {
  transform: translateX(18px);
  background-color: white;
}
.slider.round {
  border-radius: 34px;
}
.slider.round:before {
  border-radius: 50%;
}

/* --- Scanner Laser Animation --- */
.scanner-laser {
    width: 100%;
    height: 150px;
    background: repeating-linear-gradient(
      0deg,
      rgba(16, 185, 129, 0) 0%,
      rgba(16, 185, 129, 0.1) 48%,
      rgba(16, 185, 129, 0.8) 50%,
      rgba(16, 185, 129, 0.1) 52%,
      rgba(16, 185, 129, 0) 100%
    );
    background-size: 100% 200%;
    animation: scan 2s linear infinite;
    border: 2px solid rgba(16, 185, 129, 0.3);
    border-radius: 8px;
}
@keyframes scan {
    0% { background-position: 0 -100%; }
    100% { background-position: 0 100%; }
}

/* --- Scheme Card Styles --- */
.scheme-card {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 1.5rem;
    transition: transform 0.3s, border-color 0.3s, box-shadow 0.3s;
    display: flex;
    flex-direction: column;
}
.scheme-card:hover {
    transform: translateY(-5px);
    border-color: #10b981;
    box-shadow: 0 10px 25px rgba(16, 185, 129, 0.1);
}
.scheme-category {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    font-weight: bold;
    display: inline-block;
    margin-bottom: 1rem;
}
.scheme-btn {
    margin-top: auto;
    background: transparent;
    border: 1px solid #10b981;
    color: #10b981;
    padding: 0.6rem;
    border-radius: 6px;
    text-align: center;
    cursor: pointer;
    transition: background 0.3s, color 0.3s;
    text-decoration: none;
}
.scheme-btn:hover {
    background: #10b981;
    color: white;
}
"""

with open('frontend/style.css', 'w', encoding='utf-8') as f:
    f.write(css + '\n' + new_css)
    
print("style.css updated successfully.")

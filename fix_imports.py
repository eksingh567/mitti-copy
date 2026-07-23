import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix the import line
old_import = 'from flask_cors import CORS, request, jsonify, render_template_string, redirect, url_for, session'
new_import = 'from flask_cors import CORS\\nfrom flask import request, jsonify, render_template_string, redirect, url_for, session'

code = code.replace(old_import, new_import)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Fixed imports")

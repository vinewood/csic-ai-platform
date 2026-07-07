#!/usr/bin/env python3
"""
CSIC AI Platform — JSX Pre-Compiler
Extracts <script type="text/babel"> from Jinja2 templates,
transpiles with Babel via Node.js, saves as static JS files.
"""
import os, re, subprocess, sys, shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE, "templates")
OUTPUT_DIR = os.path.join(BASE, "static", "js", "pages")
NODE = "C:/Users/vinew/.workbuddy/binaries/node/versions/22.22.2/node.exe"

# Template → output JS file mapping
# (template_path_relative, output_name_no_ext)
PAGES = [
    ("public/landing.html",  "landing"),
    ("public/login.html",    "login"),
    ("chat.html",            "chat"),
    ("workspace/teaching.html", "teaching"),
    ("workspace/research.html", "research"),
    ("workspace/news.html",     "news"),
    ("workspace/skills.html",   "skills"),
    ("workspace/video.html",    "video"),
    ("workspace/admin.html",    "admin"),
    ("workspace/knowledge.html","knowledge"),
]

def extract_babel_script(template_path):
    """Extract JSX content from <script type='text/babel'> ... </script>"""
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Strip {% raw %} and {% endraw %} tags
    content = re.sub(r'\{%\s*raw\s*%\}', '', content)
    content = re.sub(r'\{%\s*endraw\s*%\}', '', content)
    
    # Extract script type="text/babel" content
    pattern = r'<script\s+type=["\']text/babel["\'][^>]*>(.*?)</script>'
    matches = re.findall(pattern, content, re.DOTALL)
    
    if not matches:
        print(f"  [SKIP] No babel script found")
        return None
    
    jsx = matches[0].strip()
    return jsx

def transpile_with_babel(jsx_code, page_name):
    """Use Node.js + Babel to transpile JSX to JS"""
    # Create a temp .jsx file
    jsx_file = os.path.join(OUTPUT_DIR, f"_{page_name}.jsx")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(jsx_file, 'w', encoding='utf-8') as f:
        f.write(jsx_code)
    
    # Use the local babel.min.js to transpile, or use npx @babel/cli
    # Let's try using @babel/standalone via Node.js
    js_file = os.path.join(OUTPUT_DIR, f"_{page_name}.js")
    
    # Method: Use babel.min.js standalone with Node.js
    babel_lib = os.path.join(BASE, "static", "lib", "babel.min.js")
    
    if not os.path.exists(babel_lib):
        print(f"  [ERR] babel.min.js not found at {babel_lib}")
        return None
    
    # Read babel lib, then run the transform
    transform_script = f"""
    const fs = require('fs');
    const babel = require('{babel_lib.replace(chr(92), '/')}');
    const code = fs.readFileSync('{jsx_file.replace(chr(92), '/')}', 'utf8');
    try {{
        const result = babel.transform(code, {{
            presets: ['react'],
            filename: '{page_name}.jsx',
        }});
        fs.writeFileSync('{js_file.replace(chr(92), '/')}', result.code, 'utf8');
        console.log('OK: ' + result.code.length + ' bytes');
    }} catch(e) {{
        console.error('ERROR: ' + e.message);
        process.exit(1);
    }}
    """
    
    # Actually, require won't work for a UMD script in Node.js.
    # Let's use a different approach: run babel as a standalone script via the CLI.
    
    # Alternative: use @babel/core from npm
    result = subprocess.run([
        NODE, "-e", f"""
        const babel = require('./node_modules/@babel/standalone/babel.js');
        const fs = require('fs');
        const code = fs.readFileSync({repr(jsx_file)}, 'utf8');
        try {{
            const out = babel.transform(code, {{ presets: ['react'] }});
            fs.writeFileSync({repr(js_file)}, out.code, 'utf8');
            console.log('OK: ' + out.code.length + ' bytes');
        }} catch(e) {{
            console.error('TRANSILE_ERROR: ' + e.message);
            process.exit(1);
        }}
        """
    ], capture_output=True, text=True, cwd=BASE)
    
    if result.returncode != 0:
        print(f"  [ERR] {result.stderr.strip()}")
        # Try installing @babel/standalone
        return None
    
    print(f"  [OK] {result.stdout.strip()}")
    return js_file

def rep(text):
    return json.dumps(text)

chr = chr
import json

def repr(s):
    return json.dumps(s)

def main():
    print(f"JSX Pre-Compiler for CSIC AI Platform")
    print(f"Templates: {TEMPLATES_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print()
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Check if @babel/standalone is installed
    node_modules_babel = os.path.join(BASE, "node_modules", "@babel", "standalone", "babel.js")
    if not os.path.exists(node_modules_babel):
        print("[INSTALL] @babel/standalone via npm...")
        result = subprocess.run([
            NODE, os.path.join(BASE, "node_modules", "npm", "bin", "npm-cli.js"),
            "install", "@babel/standalone"
        ], capture_output=True, text=True, cwd=BASE)
        # Try using npm from the node installation
        result = subprocess.run([
            "npm", "install", "@babel/standalone"
        ], capture_output=True, text=True, cwd=BASE, shell=True)
        print(result.stdout[-200:] if len(result.stdout) > 200 else result.stdout)
        if result.returncode != 0:
            print(f"[ERR] npm install failed: {result.stderr[-300:]}")
            sys.exit(1)
        print("[OK] @babel/standalone installed")
    
    compiled = []
    for rel_path, name in PAGES:
        full_path = os.path.join(TEMPLATES_DIR, rel_path)
        print(f"\n[{name}] {rel_path}")
        
        jsx = extract_babel_script(full_path)
        if jsx is None:
            continue
        
        out_file = transpile_with_babel(jsx, name)
        if out_file:
            compiled.append((name, out_file, rel_path))
    
    print(f"\n{'='*50}")
    print(f"Compiled {len(compiled)}/{len(PAGES)} pages")
    for name, out_file, _ in compiled:
        size = os.path.getsize(out_file)
        print(f"  {name}: {size/1024:.1f}KB -> {out_file}")

if __name__ == "__main__":
    main()

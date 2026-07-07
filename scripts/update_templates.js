/**
 * Update all templates to use pre-compiled JS instead of inline babel scripts.
 */
const fs = require('fs');
const path = require('path');

const BASE = path.resolve(__dirname, '..');
const TEMPLATES = path.join(BASE, 'templates');

const PAGES = [
  ['public/landing.html',  'landing',  false],
  ['public/login.html',    'login',    false],
  ['chat.html',            'chat',     true],
  ['workspace/teaching.html', 'teaching', true],
  ['workspace/research.html', 'research', true],
  ['workspace/news.html',     'news',     true],
  ['workspace/skills.html',   'skills',   true],
  ['workspace/video.html',    'video',    true],
  ['workspace/admin.html',    'admin',    true],
  ['workspace/knowledge.html','knowledge', true],
];

let updated = 0;
for (const [relPath, name, hasTopbar] of PAGES) {
  const fullPath = path.join(TEMPLATES, relPath);
  let content = fs.readFileSync(fullPath, 'utf-8');
  
  // Check if this page has a scripts block with babel content
  const scriptsMatch = content.match(/\{% block scripts %\}[\s\S]*?\{% endblock %\}/);
  if (!scriptsMatch) {
    console.log(`[SKIP] ${relPath}: no scripts block`);
    continue;
  }
  
  const newScripts = `{% block scripts %}\n<script src="/static/js/pages/${name}.js" defer></script>\n{% endblock %}`;
  content = content.replace(scriptsMatch[0], newScripts);
  
  fs.writeFileSync(fullPath, content, 'utf-8');
  console.log(`[OK] ${relPath} → static/js/pages/${name}.js`);
  updated++;
}

console.log(`\nUpdated ${updated} templates`);

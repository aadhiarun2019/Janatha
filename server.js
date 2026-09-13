// Janatha Reading Room & Library — backend server
// Uses only Node's built-in modules (http + node:sqlite). No "npm install" needed.
// Requires Node.js 22.5+ (for the built-in SQLite module).

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { DatabaseSync } = require('node:sqlite');

const PORT = process.env.PORT || 3000;
// IMPORTANT: change this before you deploy the site publicly.
// You can also set it via: ADMIN_PASSWORD=yourpassword node server.js
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'vayanashala2024';

const DB_PATH = path.join(__dirname, 'library.db');
const PUBLIC_DIR = path.join(__dirname, 'public');
const DEFAULT_CONTENT = JSON.parse(fs.readFileSync(path.join(__dirname, 'default-content.json'), 'utf8'));

// ---- Database setup ----
const db = new DatabaseSync(DB_PATH);
db.exec(`
  CREATE TABLE IF NOT EXISTS site_content (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    data TEXT NOT NULL,
    updated_at TEXT
  )
`);

function ensureSeed() {
  const row = db.prepare('SELECT id FROM site_content WHERE id = 1').get();
  if (!row) {
    db.prepare('INSERT INTO site_content (id, data, updated_at) VALUES (1, ?, ?)')
      .run(JSON.stringify(DEFAULT_CONTENT), new Date().toISOString());
    console.log('Seeded database with default content.');
  }
}
ensureSeed();

function getContent() {
  const row = db.prepare('SELECT data FROM site_content WHERE id = 1').get();
  return row ? row.data : JSON.stringify(DEFAULT_CONTENT);
}

function setContent(dataStr) {
  db.prepare('UPDATE site_content SET data = ?, updated_at = ? WHERE id = 1')
    .run(dataStr, new Date().toISOString());
}

// ---- Tiny static file server for the /public folder ----
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
};

function serveStatic(req, res) {
  let reqPath = req.url === '/' ? '/index.html' : req.url;
  const filePath = path.normalize(path.join(PUBLIC_DIR, reqPath));
  if (!filePath.startsWith(PUBLIC_DIR)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }
  fs.readFile(filePath, (err, content) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not found');
      return;
    }
    const ext = path.extname(filePath);
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    res.end(content);
  });
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', (chunk) => (body += chunk));
    req.on('end', () => resolve(body));
    req.on('error', reject);
  });
}

// ---- HTTP server + tiny JSON API ----
const server = http.createServer(async (req, res) => {
  // Public: read the current site content
  if (req.url === '/api/content' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(getContent());
    return;
  }

  // Admin: save updated site content (requires correct password header)
  if (req.url === '/api/content' && req.method === 'POST') {
    const pw = req.headers['x-admin-password'];
    if (pw !== ADMIN_PASSWORD) {
      res.writeHead(401, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Unauthorized' }));
      return;
    }
    try {
      const body = await readBody(req);
      JSON.parse(body); // validate it's real JSON before saving
      setContent(body);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true }));
    } catch (e) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Invalid JSON body' }));
    }
    return;
  }

  // Admin: check password without saving anything (used to unlock the Admin tab)
  if (req.url === '/api/admin/login' && req.method === 'POST') {
    try {
      const body = await readBody(req);
      const { password } = JSON.parse(body);
      if (password === ADMIN_PASSWORD) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true }));
      } else {
        res.writeHead(401, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false }));
      }
    } catch (e) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Invalid request' }));
    }
    return;
  }

  // Everything else: serve the website files
  serveStatic(req, res);
});

server.listen(PORT, () => {
  console.log(`Janatha Library server running at http://localhost:${PORT}`);
  console.log(`Database file: ${DB_PATH}`);
});

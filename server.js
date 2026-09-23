// Janatha Reading Room & Library — backend server (Supabase web-API version)
// Content is stored in Supabase over plain HTTPS, so admin edits survive
// Render restarts, spin-downs and redeploys. No database driver needed.
//
// Required environment variables (set in Render -> Environment):
//   SUPABASE_URL         e.g. https://raovpzgyrdcmldjpgnzj.supabase.co
//   SUPABASE_SECRET_KEY  the Supabase "secret" key (sb_secret_...) — keep private!
//   ADMIN_PASSWORD       password for the Admin tab
// Optional:
//   PORT                 provided automatically by Render

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const PORT = process.env.PORT || 3000;
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'vayanashala2024';
const SUPABASE_URL = (process.env.SUPABASE_URL || '').trim().replace(/\/+$/, '');
const SUPABASE_KEY = (process.env.SUPABASE_SECRET_KEY || '').trim();

if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.error('ERROR: SUPABASE_URL and SUPABASE_SECRET_KEY must be set as environment variables.');
  process.exit(1);
}
if (!process.env.ADMIN_PASSWORD) {
  console.warn('WARNING: ADMIN_PASSWORD not set — using the insecure default. Set it before going live.');
}

const PUBLIC_DIR = path.join(__dirname, 'public');
const DEFAULT_CONTENT = JSON.parse(fs.readFileSync(path.join(__dirname, 'default-content.json'), 'utf8'));

// ---- Supabase (PostgREST) helpers ----
const TABLE_URL = `${SUPABASE_URL}/rest/v1/site_content`;

function supabaseHeaders(extra = {}) {
  const headers = { apikey: SUPABASE_KEY, 'Content-Type': 'application/json', ...extra };
  // New-style keys (sb_secret_...) go in "apikey" only. Old-style JWT keys (eyJ...) also need Authorization.
  if (SUPABASE_KEY.startsWith('eyJ')) headers.Authorization = `Bearer ${SUPABASE_KEY}`;
  return headers;
}

async function supabaseFetch(url, options = {}) {
  const res = await fetch(url, { ...options, headers: supabaseHeaders(options.headers) });
  if (!res.ok) {
    const text = await res.text();
    let hint = '';
    if (res.status === 404 && text.includes('site_content')) {
      hint = ' — the "site_content" table does not exist yet. Run the SQL setup step in Supabase.';
    } else if (res.status === 401 || res.status === 403) {
      hint = ' — the Supabase key was rejected. Check SUPABASE_SECRET_KEY.';
    }
    throw new Error(`Supabase error ${res.status}: ${text.slice(0, 300)}${hint}`);
  }
  return res;
}

async function readRow() {
  const res = await supabaseFetch(`${TABLE_URL}?id=eq.1&select=data`);
  const rows = await res.json();
  return rows.length ? rows[0].data : null;
}

async function writeRow(obj, { onlyIfMissing = false } = {}) {
  await supabaseFetch(`${TABLE_URL}?on_conflict=id`, {
    method: 'POST',
    headers: {
      Prefer: `resolution=${onlyIfMissing ? 'ignore' : 'merge'}-duplicates,return=minimal`,
    },
    body: JSON.stringify({ id: 1, data: obj, updated_at: new Date().toISOString() }),
  });
}

async function initDb() {
  const existing = await readRow(); // also proves the URL, key and table are all correct
  if (existing === null) {
    await writeRow(DEFAULT_CONTENT, { onlyIfMissing: true });
    console.log('Seeded database with default content.');
  } else {
    console.log('Connected to Supabase; existing content found.');
  }
}

async function getContent() {
  const data = await readRow();
  return JSON.stringify(data === null ? DEFAULT_CONTENT : data);
}

async function setContent(dataStr) {
  await writeRow(JSON.parse(dataStr));
}

async function getContentObj() {
  const obj = JSON.parse(await getContent());
  if (!Array.isArray(obj.notices)) obj.notices = [];
  return obj;
}

async function setContentObj(obj) {
  await writeRow(obj);
}

function checkAdminPassword(req) {
  return req.headers['x-admin-password'] === ADMIN_PASSWORD;
}

// ---- Tiny static file server for the /public folder ----
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

function serveStatic(req, res) {
  const urlPath = decodeURIComponent(req.url.split('?')[0]);
  const reqPath = urlPath === '/' ? '/index.html' : urlPath;
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
    req.on('data', (chunk) => {
      body += chunk;
      if (body.length > 20 * 1024 * 1024) { // 20 MB safety limit (images may be embedded)
        reject(new Error('Body too large'));
        req.destroy();
      }
    });
    req.on('end', () => resolve(body));
    req.on('error', reject);
  });
}

function sendJson(res, status, obj) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(obj));
}

// ---- HTTP server + tiny JSON API ----
const server = http.createServer(async (req, res) => {
  try {
    const url = req.url.split('?')[0];

    // Public: read the current site content
    if (url === '/api/content' && req.method === 'GET') {
      const data = await getContent();
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(data);
      return;
    }

    // Admin: save updated site content
    if (url === '/api/content' && req.method === 'POST') {
      if (!checkAdminPassword(req)) return sendJson(res, 401, { error: 'Unauthorized' });
      let body;
      try {
        body = await readBody(req);
        JSON.parse(body); // validate before saving
      } catch (e) {
        return sendJson(res, 400, { error: 'Invalid JSON body' });
      }
      await setContent(body);
      return sendJson(res, 200, { ok: true });
    }

    // Admin: add a new scrolling notice
    if (url === '/api/admin/notices' && req.method === 'POST') {
      if (!checkAdminPassword(req)) return sendJson(res, 401, { error: 'Unauthorized' });
      let text;
      try {
        ({ text } = JSON.parse(await readBody(req)));
      } catch (e) {
        return sendJson(res, 400, { error: 'Invalid request body' });
      }
      if (!text || (!text.ml && !text.en)) {
        return sendJson(res, 400, { error: 'Notice must include text.ml and/or text.en' });
      }
      const content = await getContentObj();
      const notice = {
        id: crypto.randomUUID(),
        text: { ml: text.ml || '', en: text.en || '' },
        active: true,
      };
      content.notices.push(notice);
      await setContentObj(content);
      return sendJson(res, 200, { ok: true, notice, notices: content.notices });
    }

    // Admin: edit or toggle a notice
    if (/^\/api\/admin\/notices\/[^/]+$/.test(url) && req.method === 'PATCH') {
      if (!checkAdminPassword(req)) return sendJson(res, 401, { error: 'Unauthorized' });
      const id = decodeURIComponent(url.split('/').pop());
      let updates;
      try {
        updates = JSON.parse(await readBody(req));
      } catch (e) {
        return sendJson(res, 400, { error: 'Invalid request body' });
      }
      const content = await getContentObj();
      const notice = content.notices.find((n) => n.id === id);
      if (!notice) return sendJson(res, 404, { error: 'Notice not found' });
      if (typeof updates.active === 'boolean') notice.active = updates.active;
      if (updates.text) {
        notice.text = {
          ml: updates.text.ml ?? notice.text.ml,
          en: updates.text.en ?? notice.text.en,
        };
      }
      await setContentObj(content);
      return sendJson(res, 200, { ok: true, notice, notices: content.notices });
    }

    // Admin: delete a notice
    if (/^\/api\/admin\/notices\/[^/]+$/.test(url) && req.method === 'DELETE') {
      if (!checkAdminPassword(req)) return sendJson(res, 401, { error: 'Unauthorized' });
      const id = decodeURIComponent(url.split('/').pop());
      const content = await getContentObj();
      const before = content.notices.length;
      content.notices = content.notices.filter((n) => n.id !== id);
      if (content.notices.length === before) return sendJson(res, 404, { error: 'Notice not found' });
      await setContentObj(content);
      return sendJson(res, 200, { ok: true, notices: content.notices });
    }

    // Admin: check password (unlocks the Admin tab)
    if (url === '/api/admin/login' && req.method === 'POST') {
      let password;
      try {
        ({ password } = JSON.parse(await readBody(req)));
      } catch (e) {
        return sendJson(res, 400, { error: 'Invalid request' });
      }
      return password === ADMIN_PASSWORD
        ? sendJson(res, 200, { ok: true })
        : sendJson(res, 401, { ok: false });
    }

    // Everything else: serve the website files
    serveStatic(req, res);
  } catch (err) {
    console.error('Request error:', err.message);
    if (!res.headersSent) sendJson(res, 500, { error: 'Server error' });
    else res.end();
  }
});

// Start the server only after the database check passes
initDb()
  .then(() => {
    server.listen(PORT, () => {
      console.log(`Janatha Library server running on port ${PORT}`);
    });
  })
  .catch((err) => {
    console.error('Could not reach the database:', err.message);
    process.exit(1);
  });

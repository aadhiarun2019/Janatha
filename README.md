# Janatha Reading Room & Library — website + database backend

This folder contains a small self-contained server: it hosts your website AND
stores its content (books, building updates, sports activities, etc.) in a
real SQLite database, so admin edits are saved permanently and shown to every
visitor.

No external services, no npm install, no signup required — it only uses
Node.js's own built-in tools.

## What's inside

- `server.js` — the backend (serves the website + a small JSON API + the database)
- `default-content.json` — starting content, loaded into the database the first time you run the server
- `public/index.html` — the website itself
- `library.db` — created automatically the first time you run the server (this IS your database)

## Requirements

- Node.js version 22.5 or newer (check with `node --version`)

## Run it locally

```
cd janatha-library-server
node server.js
```

Then open **http://localhost:3000** in your browser.

The first time it runs, it creates `library.db` and fills it with the sample
content. From then on, all admin edits are saved into that file.

## Scrolling notices ("scrolls")

The site content now includes a `notices` array — short bilingual messages
meant to be shown as a scrolling ticker/marquee on the site (e.g. "New books
available this week"). Each one looks like:

```json
{ "id": "n1", "text": { "ml": "...", "en": "..." }, "active": true }
```

They come back as part of `GET /api/content` (under `data.notices`), and the
frontend just needs to render the ones with `active: true` as a scrolling
strip — nothing else to do on the backend for display.

To manage them without resending the whole site content, three admin-only
endpoints are available (all require the `x-admin-password` header):

- `POST /api/admin/notices` — add a new one
  ```
  curl -X POST http://localhost:3000/api/admin/notices \
    -H "x-admin-password: vayanashala2024" \
    -H "Content-Type: application/json" \
    -d '{"text":{"ml":"...","en":"..."}}'
  ```
- `PATCH /api/admin/notices/:id` — edit text and/or toggle it on/off
  ```
  curl -X PATCH http://localhost:3000/api/admin/notices/n1 \
    -H "x-admin-password: vayanashala2024" \
    -d '{"active": false}'
  ```
- `DELETE /api/admin/notices/:id` — remove one
  ```
  curl -X DELETE http://localhost:3000/api/admin/notices/n1 \
    -H "x-admin-password: vayanashala2024"
  ```

If `public/index.html` doesn't have an admin UI for this yet, these
endpoints are ready to be wired up to a simple "add scroll" form.

## Using the admin panel

1. Open the site, click the **Admin** tab
2. Default password: `vayanashala2024`
3. **Change this before putting the site online** — set it as an environment variable instead of using the built-in default:

```
ADMIN_PASSWORD=your-new-password node server.js
```

Anyone who knows the password can edit and save content — there's no
separate account per admin. If you need multiple admins with different
permissions later, that's a bigger step up (real user accounts) — let me
know if you want that built.

## Deploying so it's live on the internet

This is a real running server (not just static files), so it needs a host
that can run Node.js continuously — plain static hosts like Netlify Drop or
GitHub Pages won't work for this version. Good simple options:

- **Render.com** — free tier, connect a GitHub repo, it runs `node server.js` automatically
- **Railway.app** — similar, very quick to deploy from GitHub
- **A basic VPS** (DigitalOcean, Linode, etc.) — more control, more setup

For any of these:
1. Push this folder to a GitHub repository
2. Connect that repo to Render/Railway
3. Set the `ADMIN_PASSWORD` environment variable in their dashboard
4. Deploy — they'll run `node server.js` for you and give you a public URL

The `library.db` file lives on that server's disk. Most of these platforms
offer a "persistent disk" or "volume" option — make sure it's enabled, or
the database will reset every time the app restarts.

## Backing up your data

`library.db` is a single file containing everything — books, building
updates, all your content. Copy it somewhere safe occasionally (or set up
automatic backups on your host) so you don't lose it.

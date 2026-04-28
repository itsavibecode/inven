# The Ledger — Collectibles Inventory

A self-hosted inventory manager for Beanie Babies and resale collectibles. Dark mode, modern design. Captures every detail needed for Poshmark and eBay listings, with full import/export.

**Zero dependencies. Runs entirely in the browser. Free to host on GitHub Pages.**

Current version: **v0.2.0** — see [Changelog](#changelog) at the bottom for release history.

---

## What's new in this version

### 🔍 UPC / Barcode lookup
- Type or paste a UPC/EAN/ISBN — the app queries **Open Food Facts** and **Open Library** (both free, no API key needed) to auto-fill name, brand, country, size, material, and sometimes an image.
- **Scan with your phone camera** — uses the browser's native `BarcodeDetector` API (works on Chrome and Edge, including mobile). Point camera at barcode, app auto-fills.
- UPC is stored with the item and exported in the eBay File Exchange CSV.
- For vintage items where no UPC exists (most Beanie Babies), this gracefully falls back to manual entry — the UPC is just a reference field.

### 🐻 Beanie Baby reference database
- **60+ curated Beanies** baked in with year, birthday, tag poem, style #, retirement date, and collector notes on variations and errors that affect value.
- **Auto-suggest as you type** the item name — pick a match and it fills year, birthday, poem, style #, and rarity notes.
- **"Fill from DB"** button in the Beanie Details tab with richer search.
- **"Save to DB"** button — turn any item you're cataloguing into a reusable reference entry. Your custom entries appear alongside the seed database and sync via JSON backup.
- Includes all Original 9 Beanies, famous rarities (Princess, Peanut Royal Blue, Humphrey, Garcia, etc.), seasonal Holiday bears, and commonly-confused variations.

### 🎨 New design
- **Dark mode** with charcoal base, teal accents, and modern Geist typography
- **Refined status colors**: amber for ready-to-list, purple for Poshmark, blue for eBay, teal for both, green for sold
- Subtle ambient glow and proper hover states throughout
- Real favicon (plush bear with heart tag)

---

## All features

### Built for Beanie Babies (and more)
- Dedicated **Beanie Details** tab: year released, date of birth, tag poem, **swing/heart tag generation (1st–18th gen)**, tush tag generation, tag conditions, style/PE number, PVC vs PE pellets, errors & variations, rarity notes.
- Expandable to **12+ categories**: plush, clothing, shoes, accessories, jewelry, electronics, home decor, books, trading cards, toys, vintage, and more.

### Listing-ready information capture
- Listing title with **live Poshmark (50) / eBay (80) character counter**
- Auto-built description that combines all details from every tab
- Tags/keywords, cost, asking price, minimum accept, sold price
- Platform tracking (Poshmark, eBay, Mercari, Facebook, local)
- Direct listing URL storage
- 8 status states from Draft → Ready → Listed → Sold → Shipped → Archived

### Shipping & packaging
- Weight (oz/lb/g/kg) and package dimensions (in/cm)
- Package type presets (poly mailer, padded, USPS flat-rate sizes, etc.)
- Carrier selection and shipping cost tracking
- Inventory number (SKU) to **physically mark on your package**

### Condition & authenticity
- 8-level condition scale (NWT through For Parts)
- Detailed flaw notes, packaging status
- Smoke/pet environment disclosure
- Authentication notes

### Photos
- Drag-and-drop photo uploads
- Auto-downscaling to keep browser storage manageable
- UPC lookup can auto-add a product image when available

### Import / Export
- **JSON backup** (full fidelity, includes custom Beanie DB entries, re-importable)
- **CSV spreadsheet** (open in Excel / Google Sheets)
- **Poshmark listings TXT** (formatted, ready to copy-paste)
- **eBay File Exchange CSV** (upload directly to Seller Hub, includes UPC)
- Import JSON or CSV with merge or replace modes

### Polished UX
- Grid and table views
- Live search across names, SKUs, **UPCs**, tags, locations
- Category/status filters, multi-key sorting
- Keyboard shortcuts: `Esc` closes modals, `Cmd/Ctrl+S` saves, `Cmd/Ctrl+N` new item
- Fully responsive — works on phones (barcode scanner needs HTTPS, which GitHub Pages provides)

---

## Deploy to GitHub Pages (free hosting)

1. Create a new repo on GitHub (e.g. `inventory`).
2. Upload all five files: `index.html`, `styles.css`, `app.js`, `beanie-db.js`, `favicon.svg`.
3. Go to **Settings → Pages**.
4. Under **Source**, pick `Deploy from a branch` → select `main` branch, `/ (root)` folder, click **Save**.
5. Wait 30-60 seconds. Your site will be live at `https://YOUR-USERNAME.github.io/inventory/`

That's it — no build step, no framework, no database server.

**Important:** The barcode scanner requires camera access, which browsers only grant over HTTPS. GitHub Pages serves over HTTPS automatically, so it works. If you open the files directly with `file://`, the scanner won't work but everything else will.

### Use locally instead
Just double-click `index.html`. Works offline (UPC lookup needs internet, but everything else works).

---

## Data & storage

The Ledger has two storage modes — pick whichever fits how you use it.

### Guest mode (default)
- Everything lives in your browser's **localStorage**. Nothing leaves the device except anonymous UPC lookups to Open Food Facts and Open Library.
- **Export regularly** — if you clear browser data or switch devices, you lose everything without a backup.
- Custom Beanie DB entries are included in JSON backups.
- localStorage typically caps around 5–10 MB per site. Photos are auto-compressed.

### Signed-in mode (optional)
- Click **"Sign in with Google to sync"** at the top. Inventory items and your custom Beanie DB entries sync to **Cloud Firestore** in real time across every device you're signed in on. Photos sync to **Firebase Storage**.
- Your data lives at `/users/{your uid}/...` in Firebase, locked to you by Firestore and Storage rules — no other account can see it.
- The first time you sign in on a device that already has guest-mode items, you're prompted to upload them to your account in a single click. Your local copy stays as a backup either way.
- Sign out at any time to drop back to guest mode. localStorage isn't cleared on sign-out.
- **Browser cache caveat:** if you ship a new release, bump the cache-bust query strings on the script tags in `index.html` (the `?v=…` part) so users on a stale browser cache get the new JS.

### Self-hosting (forking)

The committed `firebase-config.js` points at itsavibecode's Firebase project. If you fork this repo and want your own backend, replace that file with your project's config and paste both `firestore.rules` and `storage.rules` into your Firebase console. Sign-in still works against the original project until you swap the config — useful for trying it out.

---

## Which browsers support barcode scanning?

The native `BarcodeDetector` API is supported in:
- ✅ Chrome (desktop & mobile)
- ✅ Edge (desktop & mobile)
- ✅ Samsung Internet
- ✅ Opera
- ❌ Safari (not yet — Safari users can still manually type the UPC)
- ❌ Firefox (behind a flag)

Everything else works in every modern browser.

---

## File structure

```
inventory/
├── index.html      # Single-page app markup
├── styles.css      # Dark mode theme
├── app.js          # All logic (CRUD, lookups, import/export)
├── beanie-db.js    # Curated Beanie Baby reference data
├── favicon.svg     # Plush bear icon
└── README.md       # This file
```

No `node_modules`. No build step. Just open and use.

---

## Changelog

### v0.2.0 — Google sign-in and multi-device sync (2026-04-28)

Adds optional Google sign-in. When signed in, all inventory items and any custom Beanie DB entries sync to Cloud Firestore in real time, and photos sync to Firebase Storage — open the app on a phone, laptop, or tablet, and your collection follows you. A slim auth bar above the header shows the current state and exposes the sign-in/out controls. Guest mode is unchanged: data stays in localStorage and nothing is sent off-device, so you can still use the app without an account.

The first time you sign in on a device with existing guest-mode items, the app counts the items and Beanie DB entries that aren't already in your account and prompts to upload them in one click. Your local copy stays as a backup either way. The prompt only fires once per sign-in.

To set up sync the first time, paste `firestore.rules` and `storage.rules` (committed at the repo root) into the Firebase console — Firestore Database → Rules and Storage → Rules respectively. Both lock each user to their own `/users/{uid}/...` subtree, deny anonymous access, and have no fallthrough rule, so anything outside that namespace is implicitly denied. Storage uploads are constrained to image/* and capped at 8 MiB to keep accidental large uploads from chewing through the free tier.

Photos taken in guest mode stay device-local in localStorage until you sign in and migrate; once uploaded to Storage, the app stores download URLs in the Firestore doc rather than base64 (URLs are tiny and stay well under the 1 MiB document cap regardless of photo count). Item delete fans out a best-effort cleanup of the matching Storage folder so orphan blobs don't pile up.

Adds cache-busting `?v=` query strings to all local script tags in `index.html`. Bump them alongside `APP_VERSION` on each release that ships JS changes, so users on a stale browser cache get the new files.

Known limits: photo sync requires Firebase's Blaze (pay-as-you-go) plan, but the free tier (5 GB storage, 1 GB/day download) covers a personal inventory at this scale with no charge in expected use; set a $1 budget alert in the Firebase console for peace of mind. iPhone Safari/Chrome still can't run the native barcode scanner — that's a known issue tracked for a later release with a JS fallback library.

### v0.1.0 — Initial baseline (2026-04-27)

First tagged release. Captures the state of the app as originally built and uploaded via the GitHub web UI on 2026-04-19. No behavior changes from that upload — this release just adds a visible version number in the site footer (`v0.1.0`), an `APP_VERSION` constant in `app.js` as the single source of truth, and this Changelog section. Intended as the clean starting point before adding multi-device sync, an iPhone barcode-scanner fallback, an expanded Beanie reference database, and other features tracked in future releases.

# The Ledger — Collectibles Inventory

A self-hosted inventory manager for Beanie Babies and resale collectibles. Dark mode, modern design. Captures every detail needed for Poshmark and eBay listings, with full import/export.

**Zero dependencies. Runs entirely in the browser. Free to host on GitHub Pages.**

Current version: **v0.6.0** — see [Changelog](#changelog) at the bottom for release history.

---

## What's new in this version

### 🔍 UPC / Barcode lookup
- Type or paste a UPC/EAN/ISBN — the app queries **Open Food Facts** and **Open Library** (both free, no API key needed) to auto-fill name, brand, country, size, material, and sometimes an image.
- **Scan with your phone camera** — uses the browser's native `BarcodeDetector` API (works on Chrome and Edge, including mobile). Point camera at barcode, app auto-fills.
- UPC is stored with the item and exported in the eBay File Exchange CSV.
- For vintage items where no UPC exists (most Beanie Babies), this gracefully falls back to manual entry — the UPC is just a reference field.

### 🐻 Beanie Baby reference database
- **120+ curated Beanies** baked in with year, birthday, style #, retirement date, and collector notes on variations and errors that affect value. Tag poems are filled for the original 60 seed entries; the v0.6.0 expansion leaves poems blank — fill them from your physical heart tag, which is the canonical source for that item anyway.
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

Barcode scanning works on every modern browser as of v0.4.0:

- ✅ Chrome (desktop & mobile) — uses the native `BarcodeDetector` API
- ✅ Edge (desktop & mobile) — native
- ✅ Samsung Internet — native
- ✅ Opera — native
- ✅ Safari (iOS / macOS) — uses a WASM-backed polyfill, lazy-loaded only when the native API is missing so non-Safari users don't pay the bytes
- ✅ Firefox — same polyfill path as Safari

Camera access is HTTPS-only (browser policy). GitHub Pages serves over HTTPS, so the live URL works; opening `index.html` from `file://` won't.

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

### v0.6.0 — Beanie reference DB expanded from 60 → 124 entries (2026-04-30)

Hand-curated expansion of `beanie-db.js`, adding 66 entries on top of the original 60-entry seed. Coverage now includes the full set of holiday teddies (1998/1999/2000), the value-tier 1995 dinosaur trio (Rex / Steg / Bronty), the 1996 political bears (Lefty / Righty), the Mexican exclusive Osito, the USA-flag Libearty (with the intentional spelling), most popular dogs (Bones / Bruno / Doby / Fetch / Pugsly / Rover / Tracker / Wrinkles), the Iggy/Rainbow material-mix-up pair, the 1995-era Tank/Coral/Sting/Bubbles/Manny early-retirees, and a dozen other commonly-traded Beanies.

Each new entry has accurate name, year, birthday, style #, and retirement date, plus collector notes on value-affecting variations where they exist. Tag poems are intentionally left blank on the new entries — your physical heart tag is the canonical source for that copy, and pre-filling them risks copyright exposure on a public repo.

This was originally scoped as a Beaniepedia scrape but the data on that site is in flowing prose rather than structured tables, URL slugs collide with newer Disney-character Beanies (the Bluey "Bingo" overrides the original 1990s spotted dog), and reproducing their editorial content on a public repo is a legitimate copyright concern. Hand-curated expansion is faster, cleaner, and matches the style of the original seed entries — the long tail of obscure Beanies stays handled by the existing "Save to DB" button.

### v0.5.0 — Pricing Research tab with margin estimate (2026-04-30)

A new "Research" tab in the item editor for recording what comparable items have actually sold for. Three platform sections side by side — eBay sold avg, Poshmark sold avg, Price Guide — each with a numeric value, a date stamp, and a free-text source/notes field. Anything older than 30 days picks up a small "stale" badge so it's obvious when to re-check.

A live "Suggested listing price" panel below averages whatever you've filled in (just the platforms with a price > 0), and a one-click "Use as listing price" button copies that average into the Listing & Pricing tab's price field. Below that, a margin estimate panel shows the rough net after typical fees: ~80% of asking on Poshmark (20% fee on sales ≥ $15, $2.95 flat below), ~87% on eBay (13% final value fee + small payment-processing flat). If a cost is set, both blocks also show profit-or-loss vs. cost in green or red. Numbers update live as you type.

Auto-fetch from Poshmark and price-guide sites isn't shipping — Poshmark has no public API and most guide sites forbid scraping. The eBay Browse API is legitimately doable but requires OAuth and a CORS proxy worker (same pattern as the stocks-worker), which is queued for a separate v0.5.1 stretch. For now everything is manual entry, and the workflow is good enough to start anchoring real listing decisions on it.

### v0.4.1 — Social-share meta tags, OG image, apple-touch-icon (2026-04-29)

Pasting the live URL into iMessage / Discord / Slack / Twitter / Bluesky now produces a proper link preview instead of a barebones URL. Adds a 1200×630 og-image.png with the bear plush logo and brand on a charcoal/teal panel matching the site, plus a 180×180 apple-touch-icon.png for iOS home-screen pins. Wires the full set of `og:*` and `twitter:*` meta tags (type, url, title, description, image with alt text and dimensions, summary_large_image card), a canonical URL, theme-color matching `--bg-0`, and an apple-touch-icon link.

The OG image is generated from a Python script committed at `.scripts/build-og-image.py` (Pillow + system Inter/Arial Black fonts), mirroring the pattern used in the spacex repo. Re-run the script and bump version on any future brand-affecting change.

### v0.4.0 — Barcode scanner now works on iOS Safari and Firefox (2026-04-29)

The native `BarcodeDetector` API is Chromium-only — iOS Safari, iOS Chrome (which is also WebKit), and Firefox all lacked it, so the scanner opened on those browsers and immediately bailed with "Try Chrome or Edge on mobile." Now `openScanner` checks for native support, and if it's missing, dynamically imports the WASM-backed `barcode-detector` polyfill (sec-ant/barcode-detector v2) from jsDelivr. The polyfill patches `globalThis.BarcodeDetector` so the existing detection loop keeps using `new BarcodeDetector()` unchanged. The import is a one-shot promise cached for re-opens, never fired on browsers with native support, so non-Safari users don't pay the ~280 KB load.

The scanner UI now shows "Loading scanner for this browser…" while the polyfill resolves, then transitions to the regular "Starting camera…" / "Position the barcode in the frame…" copy. If both native and polyfill fail, the message degrades to "Barcode scanning is not available here" with a hint that manual UPC entry still works.

Updates the README's browser-support section accordingly. Camera access still requires HTTPS — the live GitHub Pages URL covers this; `file://` opens still won't get camera permission.

### v0.3.0 — Variation flag, per-platform descriptions, eBay item # (2026-04-28)

Three schema additions tracked from the original 2026-04-19 design notes.

A `has_variations` checkbox in the Basics tab marks items where each example differs (tye-dye, hand-painted, color-varied) plus an optional `variation_description` text field for the specifics. When set, the auto-built description includes a "Variation: …" line so listings make the uniqueness explicit. The variation description field hides itself unless the checkbox is on, so the form stays clean for non-varied items.

The single Listing Description has split into three: a shared one (the existing default, used when nothing platform-specific is set) plus optional eBay-only and Poshmark-only overrides. eBay tends to want detailed, condition-focused copy; Poshmark tends to want shorter, hashtag-friendly copy. The Poshmark TXT export uses the Poshmark override; the eBay File Exchange CSV uses the eBay override; both fall back to the shared description when their override is empty, so existing items keep working without migration.

Adds an explicit `ebay_item_number` field next to the eBay listing URL — useful when the URL alone isn't enough to find the listing in Seller Hub.

The form save now correctly handles checkboxes (the checked state, not the `value` attribute), and openEditor populates checkboxes via `.checked` rather than `.value`. Existing items missing the new fields fall through to default empty/false values without any explicit migration.

### v0.2.1 — Sign-in UI and Beanie DB autofill fixes (2026-04-28)

Two small bugs surfaced on first real sign-in test in v0.2.0. The "Sign in with Google" button stayed visible alongside the signed-in pill because `.btn-link`'s `display: inline-flex` was beating the user-agent `[hidden] { display: none }` rule — added an explicit `.btn-link[hidden] { display: none; }` so `signInBtn.hidden = true` actually hides it. Clicking a Beanie DB suggestion didn't replace the partial name the user had typed to trigger the suggest in the first place — `setIfEmpty('name', entry.name)` was a no-op because the field wasn't empty. The name is now always replaced with the canonical DB entry name (other fields keep the setIfEmpty behavior so the user's manual entries aren't clobbered).

### v0.2.0 — Google sign-in and multi-device sync (2026-04-28)

Adds optional Google sign-in. When signed in, all inventory items and any custom Beanie DB entries sync to Cloud Firestore in real time, and photos sync to Firebase Storage — open the app on a phone, laptop, or tablet, and your collection follows you. A slim auth bar above the header shows the current state and exposes the sign-in/out controls. Guest mode is unchanged: data stays in localStorage and nothing is sent off-device, so you can still use the app without an account.

The first time you sign in on a device with existing guest-mode items, the app counts the items and Beanie DB entries that aren't already in your account and prompts to upload them in one click. Your local copy stays as a backup either way. The prompt only fires once per sign-in.

To set up sync the first time, paste `firestore.rules` and `storage.rules` (committed at the repo root) into the Firebase console — Firestore Database → Rules and Storage → Rules respectively. Both lock each user to their own `/users/{uid}/...` subtree, deny anonymous access, and have no fallthrough rule, so anything outside that namespace is implicitly denied. Storage uploads are constrained to image/* and capped at 8 MiB to keep accidental large uploads from chewing through the free tier.

Photos taken in guest mode stay device-local in localStorage until you sign in and migrate; once uploaded to Storage, the app stores download URLs in the Firestore doc rather than base64 (URLs are tiny and stay well under the 1 MiB document cap regardless of photo count). Item delete fans out a best-effort cleanup of the matching Storage folder so orphan blobs don't pile up.

Adds cache-busting `?v=` query strings to all local script tags in `index.html`. Bump them alongside `APP_VERSION` on each release that ships JS changes, so users on a stale browser cache get the new files.

Known limits: photo sync requires Firebase's Blaze (pay-as-you-go) plan, but the free tier (5 GB storage, 1 GB/day download) covers a personal inventory at this scale with no charge in expected use; set a $1 budget alert in the Firebase console for peace of mind. iPhone Safari/Chrome still can't run the native barcode scanner — that's a known issue tracked for a later release with a JS fallback library.

### v0.1.0 — Initial baseline (2026-04-27)

First tagged release. Captures the state of the app as originally built and uploaded via the GitHub web UI on 2026-04-19. No behavior changes from that upload — this release just adds a visible version number in the site footer (`v0.1.0`), an `APP_VERSION` constant in `app.js` as the single source of truth, and this Changelog section. Intended as the clean starting point before adding multi-device sync, an iPhone barcode-scanner fallback, an expanded Beanie reference database, and other features tracked in future releases.

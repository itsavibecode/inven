# The Ledger — Collectibles Inventory

A self-hosted inventory manager for Beanie Babies and resale collectibles. Dark mode, modern design. Captures every detail needed for Poshmark and eBay listings, with full import/export.

**Zero dependencies. Runs entirely in the browser. Free to host on GitHub Pages.**

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

- All inventory is stored in your browser's **localStorage**. Nothing is sent to any server (except UPC lookups, which hit Open Food Facts and Open Library anonymously).
- **Export regularly** — if you clear browser data or switch devices, you lose everything without a backup.
- Your custom Beanie DB entries are included in JSON backups.
- localStorage typically caps around 5-10 MB per site. Photos are auto-compressed.

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

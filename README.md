# The Ledger — Collectibles Inventory

A beautiful, self-hosted inventory manager for Beanie Babies and other resale collectibles. Designed to capture every detail needed for Poshmark and eBay listings, with full import/export support.

**Zero dependencies. Runs entirely in the browser. Free to host on GitHub Pages.**

---

## Features

### Built for Beanie Babies (and more)
- Dedicated **Beanie Details** tab: year released, date of birth, tag poem, swing/heart tag generation (1st-18th gen), tush tag generation, tag conditions, style/PE number, PVC vs PE pellets, errors & variations, rarity notes.
- Expandable to **12+ categories**: plush, clothing, shoes, accessories, jewelry, electronics, home decor, books, trading cards, toys, vintage, and more.

### Listing-ready information capture
- Listing title with **live Poshmark (50 char) / eBay (80 char) counter**
- Full description builder that assembles rich copy automatically
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
- Authentication notes (e.g., True Blue Beans verified)

### Photos
- Drag-and-drop photo uploads
- Auto-downscaling to keep browser storage manageable

### Import / Export
- **JSON backup** (full fidelity, re-importable)
- **CSV spreadsheet** (open in Excel / Google Sheets)
- **Poshmark listings TXT** (formatted, ready to copy-paste)
- **eBay File Exchange CSV** (upload directly to Seller Hub)
- Import JSON or CSV with merge or replace modes

### Polished UX
- Grid and table views
- Live search, category/status filters, multi-key sorting
- Keyboard shortcuts: `Esc` closes modals, `Cmd/Ctrl+S` saves, `Cmd/Ctrl+N` new item
- Fully responsive — works on phones

---

## Deploy to GitHub Pages (free hosting)

1. Create a new repo on GitHub (e.g. `inventory`).
2. Upload the three files: `index.html`, `styles.css`, `app.js`.
3. Go to **Settings → Pages**.
4. Under **Source**, pick `Deploy from a branch` → select `main` branch, `/ (root)` folder, click **Save**.
5. Wait 30-60 seconds. Your site will be live at `https://YOUR-USERNAME.github.io/inventory/`

That's it — no build step, no framework, no database server.

### Use locally instead
Just double-click `index.html`. Works offline.

---

## Data & storage

- All inventory is stored in your browser's **localStorage**. Nothing is sent to any server.
- **Export regularly** — if you clear browser data or switch devices, you lose everything without a backup.
- localStorage typically caps around 5-10 MB per site. Photos are auto-compressed, but if you hit the limit, export a JSON backup and consider splitting by category.

---

## Tips for best results

**Photograph with natural light.** Front, back, tags, bottom, any flaws. Buyers trust sellers who show everything.

**Write descriptions once, reuse often.** Fill in every detail on a Beanie Baby and the exporter builds beautifully formatted copy for both platforms automatically.

**Mark the SKU on the package itself.** When a sale comes in, you just need to match the SKU — no hunting through bins.

**Use the Ready to List status as a queue.** Catalogue items in bulk, then batch-list in the evening when listing tools are less competitive.

**Track minimum accept prices.** Poshmark's offer-to-likers feature and eBay's best-offer both reward sellers who know their floors.

---

## File structure

```
inventory/
├── index.html     # Single-page app markup
├── styles.css     # Editorial/archival theme
├── app.js         # All logic (CRUD, import/export, photos)
└── README.md      # This file
```

No `node_modules`. No build step. Just open and use.

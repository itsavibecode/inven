/* ============================================================
   The Ledger — Inventory Application
   Pure vanilla JS, localStorage persistence,
   Import/export for JSON, CSV, Poshmark, eBay
   ============================================================ */

const STORAGE_KEY = 'theLedger.inventory.v1';
const SETTINGS_KEY = 'theLedger.settings.v1';

const DEFAULT_FIELDS = {
  id: '', name: '', category: 'Beanie Baby', sku: '',
  brand: '', model: '', size: '', color: '', material: '',
  country: '', location: '', quantity: 1,
  // Beanie-specific
  bb_year: '', bb_birthday: '', bb_poem: '',
  bb_swing_gen: '', bb_tush_gen: '',
  bb_swing_cond: 'Mint (no creases/bends)', bb_tush_cond: 'Mint',
  bb_style_num: '', bb_pellets: '',
  bb_errors: '', bb_rarity: '',
  // Condition
  condition: 'Like New / Excellent Used', condition_notes: '',
  has_packaging: 'No',
  environment: 'Smoke-free & Pet-free home',
  authentication: '',
  // Listing
  listing_title: '', listing_desc: '', tags: '',
  cost: '', price: '', min_price: '', sold_price: '',
  status: 'Draft', sold_platform: '',
  date_listed: '', date_sold: '',
  url_poshmark: '', url_ebay: '',
  // Shipping
  weight_value: '', weight_unit: 'oz', dim_unit: 'in',
  box_length: '', box_width: '', box_height: '',
  package_type: 'Padded Mailer / Bubble Mailer',
  carrier: 'USPS Ground Advantage', ship_cost: '',
  ship_notes: '',
  // Photos & notes
  photos: [], private_notes: '',
  // Meta
  created_at: '', updated_at: ''
};

// ============ STATE ============
let state = {
  items: [],
  settings: { view: 'grid', skuPrefix: 'BB-', skuCounter: 1 },
  currentEditId: null,
  currentPhotos: [],
  filter: { search: '', category: '', status: '', sort: 'created_desc' }
};

// ============ STORAGE ============
function loadState() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) state.items = JSON.parse(saved);
    const settings = localStorage.getItem(SETTINGS_KEY);
    if (settings) state.settings = { ...state.settings, ...JSON.parse(settings) };
  } catch (e) {
    console.error('Load failed:', e);
    toast('Could not load saved data', 'error');
  }
}

function saveState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.items));
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(state.settings));
  } catch (e) {
    console.error('Save failed:', e);
    toast('Save failed — storage may be full. Export a backup and clear photos.', 'error');
  }
}

// ============ UTIL ============
function uid() { return 'it_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8); }
function nowISO() { return new Date().toISOString(); }
function formatMoney(v) {
  const n = parseFloat(v);
  if (!isFinite(n) || n === 0) return '';
  return '$' + n.toFixed(2);
}
function slug(s) { return (s || '').toString().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, ''); }
function csvEscape(v) {
  if (v === null || v === undefined) return '';
  const s = String(v);
  if (/[",\n\r]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
  return s;
}

function toast(msg, type = '') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast show ' + type;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.remove('show'), 3200);
}

function confirmDialog(title, message) {
  return new Promise(resolve => {
    const modal = document.getElementById('confirmModal');
    document.getElementById('confirmTitle').textContent = title;
    document.getElementById('confirmMessage').textContent = message;
    modal.classList.add('open');
    const ok = document.getElementById('confirmOk');
    const cancel = document.getElementById('confirmCancel');
    const cleanup = (result) => {
      modal.classList.remove('open');
      ok.onclick = null; cancel.onclick = null;
      resolve(result);
    };
    ok.onclick = () => cleanup(true);
    cancel.onclick = () => cleanup(false);
    modal.querySelector('.modal-backdrop').onclick = () => cleanup(false);
  });
}

// ============ SKU GEN ============
function nextSku(category) {
  const prefix = (category === 'Beanie Baby') ? 'BB-' : (slug(category).slice(0, 3).toUpperCase() + '-');
  // Find highest with this prefix
  let max = 0;
  state.items.forEach(it => {
    if (it.sku && it.sku.startsWith(prefix)) {
      const num = parseInt(it.sku.slice(prefix.length), 10);
      if (isFinite(num) && num > max) max = num;
    }
  });
  return prefix + String(max + 1).padStart(4, '0');
}

// ============ RENDER ============
function render() {
  renderStats();
  const filtered = applyFilters(state.items);
  const grid = document.getElementById('itemGrid');
  const table = document.getElementById('itemTable');
  const empty = document.getElementById('emptyState');
  const count = document.getElementById('resultCount');
  const view = state.settings.view;

  if (state.items.length === 0) {
    grid.style.display = 'none';
    table.style.display = 'none';
    empty.classList.add('visible');
    count.textContent = '';
    return;
  }

  empty.classList.remove('visible');
  count.textContent = `${filtered.length} of ${state.items.length} items`;

  if (view === 'grid') {
    grid.style.display = '';
    table.style.display = 'none';
    grid.innerHTML = filtered.map(renderCard).join('');
  } else {
    grid.style.display = 'none';
    table.style.display = '';
    table.innerHTML = renderTable(filtered);
  }

  // Attach click handlers
  document.querySelectorAll('[data-edit-id]').forEach(el => {
    el.addEventListener('click', () => openEditor(el.dataset.editId));
  });
  // Populate category filter from data
  populateCategoryFilter();
}

function renderStats() {
  const total = state.items.length;
  const active = state.items.filter(i => ['Listed - Poshmark','Listed - eBay','Listed - Both','Ready to List'].includes(i.status)).length;
  const sold = state.items.filter(i => ['Sold','Shipped'].includes(i.status)).length;
  const value = state.items.reduce((sum, i) => {
    const price = parseFloat(i.price) || 0;
    return (['Sold','Shipped','Archived'].includes(i.status)) ? sum : sum + price;
  }, 0);
  document.getElementById('statTotal').textContent = total;
  document.getElementById('statActive').textContent = active;
  document.getElementById('statSold').textContent = sold;
  document.getElementById('statValue').textContent = '$' + value.toFixed(0);
}

function renderCard(item) {
  const img = (item.photos && item.photos[0])
    ? `<img src="${item.photos[0]}" alt="${escapeHtml(item.name)}" />`
    : `<span class="card-image-placeholder">◈</span>`;
  const metaParts = [];
  if (item.category) metaParts.push(`<span class="card-meta-item">${escapeHtml(item.category)}</span>`);
  if (item.bb_year) metaParts.push(`<span class="card-meta-item">· ${escapeHtml(item.bb_year)}</span>`);
  if (item.brand && item.category !== 'Beanie Baby') metaParts.push(`<span class="card-meta-item">· ${escapeHtml(item.brand)}</span>`);
  if (item.location) metaParts.push(`<span class="card-meta-item">· ${escapeHtml(item.location)}</span>`);

  const statusClass = 'status-' + slug(item.status || 'draft');
  const price = item.status === 'Sold' || item.status === 'Shipped'
    ? (item.sold_price ? `<span class="card-price sold">${formatMoney(item.sold_price)}</span>` : `<span class="card-price no-price">Sold</span>`)
    : (item.price ? `<span class="card-price">${formatMoney(item.price)}</span>` : `<span class="card-price no-price">unpriced</span>`);

  return `
    <div class="item-card" data-edit-id="${item.id}">
      <div class="card-image">${img}</div>
      <div class="card-body">
        <div class="card-sku">${escapeHtml(item.sku || '—')}</div>
        <div class="card-name">${escapeHtml(item.name || 'Untitled')}</div>
        <div class="card-meta">${metaParts.join(' ')}</div>
        <div class="card-footer">
          ${price}
          <span class="status-badge ${statusClass}">${escapeHtml(item.status || 'Draft')}</span>
        </div>
      </div>
    </div>`;
}

function renderTable(items) {
  return `<table><thead><tr>
    <th>SKU</th><th>Name</th><th>Category</th><th>Year</th>
    <th>Condition</th><th>Status</th><th>Price</th><th>Location</th>
  </tr></thead><tbody>${items.map(i => `
    <tr data-edit-id="${i.id}">
      <td class="col-sku">${escapeHtml(i.sku || '—')}</td>
      <td class="col-name">${escapeHtml(i.name || 'Untitled')}</td>
      <td>${escapeHtml(i.category || '')}</td>
      <td>${escapeHtml(i.bb_year || '')}</td>
      <td>${escapeHtml(i.condition || '')}</td>
      <td><span class="status-badge status-${slug(i.status || 'draft')}">${escapeHtml(i.status || 'Draft')}</span></td>
      <td class="col-price">${formatMoney(i.status === 'Sold' || i.status === 'Shipped' ? i.sold_price : i.price) || '—'}</td>
      <td>${escapeHtml(i.location || '')}</td>
    </tr>`).join('')}</tbody></table>`;
}

function escapeHtml(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

function populateCategoryFilter() {
  const sel = document.getElementById('filterCategory');
  const current = sel.value;
  const cats = [...new Set(state.items.map(i => i.category).filter(Boolean))].sort();
  sel.innerHTML = '<option value="">All Categories</option>' + cats.map(c => `<option value="${escapeHtml(c)}"${c === current ? ' selected' : ''}>${escapeHtml(c)}</option>`).join('');
}

// ============ FILTERS ============
function applyFilters(items) {
  const { search, category, status, sort } = state.filter;
  let result = items.filter(i => {
    if (category && i.category !== category) return false;
    if (status && i.status !== status) return false;
    if (search) {
      const q = search.toLowerCase();
      const blob = [i.name, i.sku, i.brand, i.tags, i.location, i.listing_title, i.bb_year, i.category]
        .join(' ').toLowerCase();
      if (!blob.includes(q)) return false;
    }
    return true;
  });
  const sorters = {
    created_desc: (a, b) => (b.created_at || '').localeCompare(a.created_at || ''),
    created_asc: (a, b) => (a.created_at || '').localeCompare(b.created_at || ''),
    name_asc: (a, b) => (a.name || '').localeCompare(b.name || ''),
    name_desc: (a, b) => (b.name || '').localeCompare(a.name || ''),
    price_desc: (a, b) => (parseFloat(b.price) || 0) - (parseFloat(a.price) || 0),
    price_asc: (a, b) => (parseFloat(a.price) || 0) - (parseFloat(b.price) || 0),
    sku_asc: (a, b) => (a.sku || '').localeCompare(b.sku || '', undefined, { numeric: true }),
  };
  result.sort(sorters[sort] || sorters.created_desc);
  return result;
}

// ============ EDITOR ============
function openEditor(id = null) {
  const modal = document.getElementById('itemModal');
  const form = document.getElementById('itemForm');
  form.reset();
  state.currentEditId = id;
  state.currentPhotos = [];

  // Reset tabs
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === 'basics'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.dataset.panel === 'basics'));

  let item;
  if (id) {
    item = state.items.find(i => i.id === id);
    if (!item) return;
    document.getElementById('modalEyebrow').textContent = `Entry · ${item.sku || '—'}`;
    document.getElementById('modalTitle').textContent = item.name || 'Untitled';
    document.getElementById('deleteBtn').style.display = '';
    // Fill form
    Object.entries(item).forEach(([k, v]) => {
      const el = form.elements[k];
      if (el && el.type !== 'file') el.value = v ?? '';
    });
    state.currentPhotos = [...(item.photos || [])];
  } else {
    item = { ...DEFAULT_FIELDS };
    document.getElementById('modalEyebrow').textContent = 'New Entry';
    document.getElementById('modalTitle').textContent = 'Catalogue Item';
    document.getElementById('deleteBtn').style.display = 'none';
    // Apply defaults
    Object.entries(DEFAULT_FIELDS).forEach(([k, v]) => {
      const el = form.elements[k];
      if (el && el.type !== 'file' && v !== '' && v != null) el.value = v;
    });
    // auto-SKU
    form.elements.sku.value = nextSku(form.elements.category.value);
  }

  toggleBeanieTab(form.elements.category.value);
  renderPhotoPreview();
  updateTitleCount();
  modal.classList.add('open');
  setTimeout(() => form.elements.name.focus(), 100);
}

function closeEditor() {
  document.getElementById('itemModal').classList.remove('open');
  state.currentEditId = null;
  state.currentPhotos = [];
}

function toggleBeanieTab(category) {
  const tab = document.getElementById('beanieTab');
  tab.style.display = (category === 'Beanie Baby') ? '' : 'none';
}

function updateTitleCount() {
  const input = document.querySelector('[name="listing_title"]');
  const counter = document.getElementById('titleCount');
  if (input && counter) {
    const len = input.value.length;
    counter.textContent = `${len} / 80${len > 50 ? ' (over Poshmark limit)' : ''}`;
    counter.style.color = len > 80 ? '#7a1e1e' : len > 50 ? '#9a7e29' : '';
  }
}

function saveItem(e) {
  e.preventDefault();
  const form = document.getElementById('itemForm');
  const data = {};
  // Gather all named form fields
  Array.from(form.elements).forEach(el => {
    if (!el.name) return;
    data[el.name] = el.value;
  });

  // Validate
  if (!data.name.trim()) { toast('Name is required', 'error'); return; }
  if (!data.sku.trim()) { toast('SKU is required', 'error'); return; }
  // Check duplicate SKU
  const dup = state.items.find(i => i.sku === data.sku && i.id !== state.currentEditId);
  if (dup) { toast(`SKU "${data.sku}" is already used by "${dup.name}"`, 'error'); return; }

  data.quantity = parseInt(data.quantity, 10) || 1;
  data.photos = state.currentPhotos;

  if (state.currentEditId) {
    const idx = state.items.findIndex(i => i.id === state.currentEditId);
    if (idx >= 0) {
      data.id = state.currentEditId;
      data.created_at = state.items[idx].created_at || nowISO();
      data.updated_at = nowISO();
      state.items[idx] = { ...DEFAULT_FIELDS, ...state.items[idx], ...data };
    }
  } else {
    data.id = uid();
    data.created_at = nowISO();
    data.updated_at = nowISO();
    state.items.unshift({ ...DEFAULT_FIELDS, ...data });
  }
  saveState();
  closeEditor();
  render();
  toast('Saved', 'success');
}

async function deleteCurrentItem() {
  if (!state.currentEditId) return;
  const item = state.items.find(i => i.id === state.currentEditId);
  if (!item) return;
  const ok = await confirmDialog('Delete Item', `Permanently delete "${item.name}"? This cannot be undone.`);
  if (!ok) return;
  state.items = state.items.filter(i => i.id !== state.currentEditId);
  saveState();
  closeEditor();
  render();
  toast('Item deleted', 'success');
}

// ============ PHOTOS ============
function handlePhotoFiles(files) {
  Array.from(files).forEach(file => {
    if (!file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = e => {
      // Downscale to keep storage manageable
      downscaleImage(e.target.result, 900).then(data => {
        state.currentPhotos.push(data);
        renderPhotoPreview();
      });
    };
    reader.readAsDataURL(file);
  });
}

function downscaleImage(dataUrl, maxDim) {
  return new Promise(resolve => {
    const img = new Image();
    img.onload = () => {
      let { width, height } = img;
      if (width > maxDim || height > maxDim) {
        const ratio = Math.min(maxDim / width, maxDim / height);
        width = Math.round(width * ratio);
        height = Math.round(height * ratio);
      }
      const canvas = document.createElement('canvas');
      canvas.width = width; canvas.height = height;
      canvas.getContext('2d').drawImage(img, 0, 0, width, height);
      resolve(canvas.toDataURL('image/jpeg', 0.82));
    };
    img.onerror = () => resolve(dataUrl);
    img.src = dataUrl;
  });
}

function renderPhotoPreview() {
  const el = document.getElementById('photoPreview');
  el.innerHTML = state.currentPhotos.map((src, idx) => `
    <div class="photo-thumb">
      <img src="${src}" alt="photo ${idx + 1}" />
      <button type="button" class="photo-remove" data-idx="${idx}">×</button>
    </div>`).join('');
  el.querySelectorAll('.photo-remove').forEach(btn => {
    btn.onclick = () => {
      state.currentPhotos.splice(parseInt(btn.dataset.idx, 10), 1);
      renderPhotoPreview();
    };
  });
}

// ============ IMPORT / EXPORT ============
function exportJSON() {
  const payload = {
    exported_at: nowISO(),
    app: 'The Ledger',
    version: 1,
    count: state.items.length,
    items: state.items
  };
  downloadBlob(JSON.stringify(payload, null, 2), `ledger-backup-${todayStr()}.json`, 'application/json');
  toast(`Exported ${state.items.length} items`, 'success');
}

function exportCSV() {
  if (!state.items.length) { toast('No items to export', 'error'); return; }
  const fields = Object.keys(DEFAULT_FIELDS).filter(f => f !== 'photos');
  const header = fields.join(',');
  const rows = state.items.map(i => fields.map(f => csvEscape(i[f])).join(','));
  downloadBlob([header, ...rows].join('\n'), `ledger-${todayStr()}.csv`, 'text/csv');
  toast('CSV exported', 'success');
}

function exportPoshmark() {
  // Poshmark is manual-upload: generate rich text listings
  const listable = state.items.filter(i => !['Sold','Shipped','Archived'].includes(i.status));
  if (!listable.length) { toast('No listable items', 'error'); return; }
  const out = listable.map(i => {
    const title = i.listing_title || i.name;
    const lines = [];
    lines.push('═══════════════════════════════════════════');
    lines.push(`TITLE (${(title || '').length}/50): ${title}`);
    lines.push(`SKU: ${i.sku}`);
    lines.push(`CATEGORY: ${i.category}`);
    if (i.brand) lines.push(`BRAND: ${i.brand}`);
    if (i.size) lines.push(`SIZE: ${i.size}`);
    if (i.color) lines.push(`COLOR: ${i.color}`);
    lines.push(`CONDITION: ${i.condition}`);
    lines.push(`PRICE: ${formatMoney(i.price) || '—'}`);
    if (i.min_price) lines.push(`MIN ACCEPT: ${formatMoney(i.min_price)}`);
    lines.push('');
    lines.push('DESCRIPTION:');
    lines.push(buildDescription(i));
    lines.push('');
    if (i.tags) lines.push(`TAGS: ${i.tags}`);
    lines.push('');
    return lines.join('\n');
  }).join('\n\n');
  downloadBlob(out, `poshmark-listings-${todayStr()}.txt`, 'text/plain');
  toast(`${listable.length} Poshmark listings prepared`, 'success');
}

function exportEbay() {
  // eBay File Exchange CSV — simplified template
  const listable = state.items.filter(i => !['Sold','Shipped','Archived'].includes(i.status));
  if (!listable.length) { toast('No listable items', 'error'); return; }
  const header = [
    'Action(SiteID=US|Country=US|Currency=USD|Version=1193)',
    'CustomLabel', 'Category', 'Title', 'ConditionID', 'Description',
    'PicURL', 'Quantity', 'Format', 'StartPrice', 'Duration',
    'Location', 'ShippingService-1:Option', 'ShippingService-1:Cost',
    'DispatchTimeMax', 'ReturnsAcceptedOption', 'Brand', 'UPC',
    'C:Type', 'C:Character', 'C:Year Manufactured', 'C:Country/Region of Manufacture',
    'PackageLength', 'PackageWidth', 'PackageDepth', 'WeightMajor', 'WeightMinor'
  ];

  const conditionMap = {
    'New With Tags (NWT)': '1000', 'New Without Tags (NWOT)': '1500',
    'New With Defects': '1750', 'Like New / Excellent Used': '3000',
    'Very Good': '4000', 'Good': '5000', 'Fair': '6000', 'Poor / For Parts': '7000'
  };

  const rows = listable.map(i => {
    // Convert weight to lb + oz for eBay
    const weightLb = i.weight_unit === 'lb' ? Math.floor(parseFloat(i.weight_value) || 0) : 0;
    const weightOz = i.weight_unit === 'oz' ? (parseFloat(i.weight_value) || 0) :
                     i.weight_unit === 'lb' ? Math.round(((parseFloat(i.weight_value) || 0) - weightLb) * 16) :
                     i.weight_unit === 'g' ? Math.round((parseFloat(i.weight_value) || 0) / 28.3495) :
                     i.weight_unit === 'kg' ? Math.round((parseFloat(i.weight_value) || 0) * 35.274) : '';
    return [
      'Add', i.sku, '', i.listing_title || i.name,
      conditionMap[i.condition] || '3000',
      buildDescription(i).replace(/\n/g, '<br>'),
      '', i.quantity || 1, 'FixedPrice', i.price || '', 'GTC',
      '', 'USPSGroundAdvantage', i.ship_cost || '',
      '1', 'ReturnsAccepted', i.brand || '', '',
      i.category === 'Beanie Baby' ? 'Plush Beanbag' : '',
      i.name || '', i.bb_year || '', i.country || '',
      i.box_length || '', i.box_width || '', i.box_height || '',
      weightLb || '', weightOz || ''
    ].map(csvEscape).join(',');
  });
  downloadBlob([header.join(','), ...rows].join('\n'), `ebay-file-exchange-${todayStr()}.csv`, 'text/csv');
  toast(`${listable.length} eBay listings prepared`, 'success');
}

function buildDescription(i) {
  const parts = [];
  if (i.listing_desc) {
    parts.push(i.listing_desc);
  } else {
    parts.push(`${i.name}${i.brand ? ' by ' + i.brand : ''}`);
  }
  parts.push('');
  parts.push('DETAILS:');
  if (i.category === 'Beanie Baby') {
    if (i.bb_year) parts.push(`• Year: ${i.bb_year}`);
    if (i.bb_birthday) parts.push(`• Date of Birth: ${i.bb_birthday}`);
    if (i.bb_swing_gen) parts.push(`• Heart Tag Generation: ${i.bb_swing_gen}`);
    if (i.bb_tush_gen) parts.push(`• Tush Tag Generation: ${i.bb_tush_gen}`);
    if (i.bb_swing_cond) parts.push(`• Heart Tag Condition: ${i.bb_swing_cond}`);
    if (i.bb_tush_cond) parts.push(`• Tush Tag Condition: ${i.bb_tush_cond}`);
    if (i.bb_style_num) parts.push(`• Style #: ${i.bb_style_num}`);
    if (i.bb_pellets) parts.push(`• Pellet Type: ${i.bb_pellets}`);
    if (i.bb_errors) parts.push(`• Errors/Variations: ${i.bb_errors}`);
    if (i.bb_rarity) parts.push(`• Rarity: ${i.bb_rarity}`);
  } else {
    if (i.brand) parts.push(`• Brand: ${i.brand}`);
    if (i.model) parts.push(`• Model: ${i.model}`);
    if (i.size) parts.push(`• Size: ${i.size}`);
    if (i.color) parts.push(`• Color: ${i.color}`);
    if (i.material) parts.push(`• Material: ${i.material}`);
    if (i.country) parts.push(`• Country of Manufacture: ${i.country}`);
  }
  parts.push(`• Condition: ${i.condition}`);
  if (i.condition_notes) parts.push(`• Flaws/Notes: ${i.condition_notes}`);
  if (i.has_packaging && i.has_packaging !== 'No') parts.push(`• Packaging: ${i.has_packaging}`);
  if (i.environment) parts.push(`• From: ${i.environment}`);
  if (i.authentication) parts.push(`• Authentication: ${i.authentication}`);
  parts.push('');
  const dim = [i.box_length, i.box_width, i.box_height].filter(Boolean);
  if (dim.length === 3) parts.push(`Ships in ${dim.join(' × ')} ${i.dim_unit} package`);
  if (i.weight_value) parts.push(`Weight: ${i.weight_value} ${i.weight_unit}`);
  parts.push('');
  parts.push('Thank you for looking! Message with any questions.');
  return parts.join('\n');
}

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function downloadBlob(content, filename, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ============ IMPORT ============
function openImportModal() {
  document.getElementById('importModal').classList.add('open');
  document.getElementById('importFile').value = '';
}

function doImport() {
  const file = document.getElementById('importFile').files[0];
  if (!file) { toast('Choose a file first', 'error'); return; }
  const mode = document.querySelector('input[name="importMode"]:checked').value;
  const reader = new FileReader();
  reader.onload = e => {
    try {
      let incoming;
      if (file.name.toLowerCase().endsWith('.json')) {
        const data = JSON.parse(e.target.result);
        incoming = Array.isArray(data) ? data : (data.items || []);
      } else {
        incoming = parseCSV(e.target.result);
      }
      if (!incoming.length) throw new Error('No items found in file');

      // Normalize: ensure every item has id & defaults
      incoming = incoming.map(raw => {
        const item = { ...DEFAULT_FIELDS };
        Object.entries(raw).forEach(([k, v]) => {
          if (k in DEFAULT_FIELDS) item[k] = v;
        });
        item.id = item.id || uid();
        item.created_at = item.created_at || nowISO();
        item.updated_at = nowISO();
        item.photos = Array.isArray(item.photos) ? item.photos : [];
        return item;
      });

      if (mode === 'replace') {
        state.items = incoming;
      } else {
        // Merge by SKU/id
        incoming.forEach(imp => {
          const existingIdx = state.items.findIndex(i => i.id === imp.id || (imp.sku && i.sku === imp.sku));
          if (existingIdx >= 0) state.items[existingIdx] = imp;
          else state.items.push(imp);
        });
      }
      saveState();
      render();
      document.getElementById('importModal').classList.remove('open');
      toast(`Imported ${incoming.length} items (${mode})`, 'success');
    } catch (err) {
      console.error(err);
      toast('Import failed: ' + err.message, 'error');
    }
  };
  reader.readAsText(file);
}

function parseCSV(text) {
  // Minimal CSV parser supporting quoted fields & embedded commas/newlines
  const rows = [];
  let cur = [], field = '', inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (inQuotes) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (ch === '"') inQuotes = false;
      else field += ch;
    } else {
      if (ch === '"') inQuotes = true;
      else if (ch === ',') { cur.push(field); field = ''; }
      else if (ch === '\n' || ch === '\r') {
        if (field !== '' || cur.length > 0) { cur.push(field); rows.push(cur); cur = []; field = ''; }
        if (ch === '\r' && text[i + 1] === '\n') i++;
      } else field += ch;
    }
  }
  if (field !== '' || cur.length > 0) { cur.push(field); rows.push(cur); }
  if (!rows.length) return [];
  const header = rows[0];
  return rows.slice(1).map(r => {
    const o = {};
    header.forEach((h, idx) => { o[h.trim()] = r[idx] ?? ''; });
    return o;
  });
}

// ============ WIRE UP ============
function init() {
  loadState();

  // Add
  document.getElementById('addBtn').onclick = () => openEditor();
  // Close / cancel
  document.getElementById('modalClose').onclick = closeEditor;
  document.getElementById('cancelBtn').onclick = closeEditor;
  document.querySelector('#itemModal .modal-backdrop').onclick = closeEditor;
  // Delete
  document.getElementById('deleteBtn').onclick = deleteCurrentItem;
  // Save
  document.getElementById('itemForm').onsubmit = saveItem;
  // Tabs
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.dataset.panel === btn.dataset.tab));
    };
  });

  // Category change -> toggle beanie tab & auto-SKU prefix if new entry
  document.getElementById('categorySelect').onchange = e => {
    toggleBeanieTab(e.target.value);
    if (!state.currentEditId) {
      document.querySelector('[name="sku"]').value = nextSku(e.target.value);
    }
  };
  // Auto-SKU button
  document.getElementById('autoSku').onclick = () => {
    const cat = document.getElementById('categorySelect').value;
    document.querySelector('[name="sku"]').value = nextSku(cat);
  };
  // Title char counter
  document.querySelector('[name="listing_title"]').addEventListener('input', updateTitleCount);

  // Photos
  const photoInput = document.getElementById('photoInput');
  photoInput.onchange = e => handlePhotoFiles(e.target.files);
  const drop = document.getElementById('photoDrop');
  drop.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('dragover'); });
  drop.addEventListener('dragleave', () => drop.classList.remove('dragover'));
  drop.addEventListener('drop', e => {
    e.preventDefault();
    drop.classList.remove('dragover');
    handlePhotoFiles(e.dataTransfer.files);
  });

  // Search / filters
  document.getElementById('searchInput').addEventListener('input', e => {
    state.filter.search = e.target.value;
    render();
  });
  document.getElementById('filterCategory').onchange = e => { state.filter.category = e.target.value; render(); };
  document.getElementById('filterStatus').onchange = e => { state.filter.status = e.target.value; render(); };
  document.getElementById('sortBy').onchange = e => { state.filter.sort = e.target.value; render(); };

  // View toggle
  document.querySelectorAll('.view-btn').forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.settings.view = btn.dataset.view;
      saveState();
      render();
    };
  });

  // Export dropdown
  const exportBtn = document.getElementById('exportBtn');
  const exportMenu = document.getElementById('exportMenu');
  exportBtn.onclick = e => {
    e.stopPropagation();
    exportMenu.classList.toggle('open');
  };
  document.addEventListener('click', () => exportMenu.classList.remove('open'));
  exportMenu.addEventListener('click', e => {
    const btn = e.target.closest('button');
    if (!btn) return;
    const format = btn.dataset.format;
    exportMenu.classList.remove('open');
    if (format === 'json') exportJSON();
    else if (format === 'csv') exportCSV();
    else if (format === 'poshmark') exportPoshmark();
    else if (format === 'ebay') exportEbay();
  });

  // Import
  document.getElementById('importBtn').onclick = openImportModal;
  document.getElementById('importCancel').onclick = () => document.getElementById('importModal').classList.remove('open');
  document.getElementById('importConfirm').onclick = doImport;
  document.querySelector('#importModal .modal-backdrop').onclick = () => document.getElementById('importModal').classList.remove('open');

  // Restore view
  document.querySelectorAll('.view-btn').forEach(b => b.classList.toggle('active', b.dataset.view === state.settings.view));

  // Keyboard
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal.open').forEach(m => m.classList.remove('open'));
    }
    if ((e.metaKey || e.ctrlKey) && e.key === 'n' && !document.querySelector('.modal.open')) {
      e.preventDefault();
      openEditor();
    }
    if ((e.metaKey || e.ctrlKey) && e.key === 's' && document.getElementById('itemModal').classList.contains('open')) {
      e.preventDefault();
      document.getElementById('itemForm').requestSubmit();
    }
  });

  render();
}

document.addEventListener('DOMContentLoaded', init);

"""One-time migration: the owner's Google Sheet inventory tracker -> a CSV that
The Ledger's own Import (JSON/CSV/XLSX) button accepts.

The column list, default values and select options are read from app.js and
index.html at run time, so the output always matches the app's import
template. No sheet data lives in this file.

Usage (from anywhere):
    python sheet-to-ledger.py --out <path>             # re-downloads the sheet
    python sheet-to-ledger.py --csv sheet.csv --out <path>

Write the output OUTSIDE the repo: the sheet holds buyer usernames.

Notes on how the app reads the file (see parseCSV / applyImport in app.js):
- parseCSV does not strip a byte-order mark, so the output is written as
  plain UTF-8 without one (a BOM would turn the first header into an
  unknown key and drop that column).
- applyImport copies every column over DEFAULT_FIELDS, including blanks, so
  a blank cell would wipe a default like condition or carrier. Blank cells
  are therefore filled with the app's own default, except has_variations
  (the string "false" would be truthy in the app).
"""
import argparse
import csv
import html.parser
import io
import os
import re
import sys
import urllib.request
from collections import Counter
from decimal import Decimal, InvalidOperation

SHEET_URL = ('https://docs.google.com/spreadsheets/d/'
             '1Pxso2yUDLQ1CmwTd66K_Rn2d4cO6nM9gBtMr2UE35so/export?format=csv')
IMPORT_DATE = '2026-11-13'
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HEADER_ROW = 5      # 1-based
SUBTOTAL_ROW = 4

# 1-based sheet columns
C_CHECK, C_ID, C_STATUS, C_SITE, C_SOLD_DATE = 1, 2, 3, 4, 5
C_LISTED_DATE, C_ITEM, C_EBAY_NO, C_POSH_NO, C_TRACKING, C_UPC = 8, 9, 10, 11, 12, 13
C_SITE_SOLD, C_BUYER, C_LEN, C_WID, C_HGT, C_LB, C_OZ = 14, 15, 16, 17, 18, 20, 21
C_MATERIAL, C_COST, C_TAX, C_OTHER, C_CRATE = 23, 24, 25, 26, 28
C_PRICE, C_SHIP_CHARGED, C_SALE_TOTAL, C_POSTAGE = 29, 30, 31, 32
C_INSERTION, C_FVF, C_FVF_SHIP, C_POSH_FEE, C_SALES_TAX, C_PAYPAL, C_SELLING = 37, 38, 39, 40, 41, 42, 43
C_GROSS_COSTS, C_GROSS_SALES = 34, 35
C_TOTAL_FEES, C_PROFIT, C_NOTES = 44, 46, 52

# How sold_price is derived for Sold rows (set by --sold-price-rule):
#   brief      sold_price = Sale Price (col 31) - Listing Postage (col 30), always.
#   corrected  same, except two row patterns where col 31 evidently does not
#              hold "total including postage": a blank col 31 (listing price
#              is used, as the sheet's own Gross Sales does) and col 31 equal
#              to the listing price while postage was charged (col 31 is then
#              the item price alone). Every changed row is listed in the output.
SOLD_RULE = 'corrected'

FEE_COLUMNS = {
    'fee_ebay_insertion': C_INSERTION,
    'fee_ebay_fvf': C_FVF,
    'fee_ebay_fvf_shipping': C_FVF_SHIP,
    'fee_poshmark': C_POSH_FEE,
    'fee_paypal': C_PAYPAL,
    'fee_other': C_SELLING,
}

SELECT_FIELDS = ['category', 'condition', 'status', 'sold_platform', 'package_type',
                 'carrier', 'has_packaging', 'environment', 'weight_unit', 'dim_unit']

PACKAGE_MAP = {
    'Blue ValueMailer': 'Poly Mailer',
    'AE Bag': 'Poly Mailer',
    'AE Large Mailer': 'Poly Mailer',
    'Box': 'BOX',
    'Brown Box': 'BOX',
    'Box [ULINE]': 'BOX',
    'Scotch Plastic Bubble Mailer Size 0': 'Padded Mailer / Bubble Mailer',
    'Bubble Envelope': 'Padded Mailer / Bubble Mailer',
    'Padded Envelope': 'Padded Mailer / Bubble Mailer',
    'Envelope': 'Custom',
    'Envelope (32k-75w)': 'Custom',
    # One-off spellings found in the sheet, mapped by the same rules.
    'Reused Lootwear Bag': 'Poly Mailer',
    "Brown Box (Macy's)": 'BOX',
    'U-Line Brown Box': 'BOX',
    '0 Scotch Bubble Mailer': 'Padded Mailer / Bubble Mailer',
    '000 Scotch Bubble Mailer': 'Padded Mailer / Bubble Mailer',
}

LISTED_STATUS = {
    'eBay': 'Listed - eBay',
    'Poshmark': 'Listed - Poshmark',
    'eBay & Poshmark': 'Listed - Both',
    '': 'Ready to List',
}

# Keyword rules, first match wins. Each keyword matches as a whole word,
# optionally plural.
CATEGORY_RULES = [
    ('Beanie Baby', ['beanie']),
    ('Plush / Stuffed Animal', ['plush', 'stuffed']),
    ('Clothing', ['shirt', 'tee', 't-shirt', 'sock', 'hoodie', 'hat', 'jacket', 'apparel']),
    ('Accessories', ['pin', 'patch', 'keychain', 'lanyard', 'wallet', 'bag']),
    ('Toys & Collectibles', ['funko', 'pop!', 'figure', 'vinyl', 'toy', 'statue', 'replica', 'prop']),
    ('Books / Media', ['comic', 'book', 'magazine', 'dvd', 'blu-ray']),
    ('Electronics', ['tv', 'headphone', 'electronic', 'charger', 'cable']),
    ('Home & Decor', ['mug', 'poster', 'print', 'decor', 'coaster', 'glass']),
    ('Trading Cards', ['card']),
]
CATEGORY_FALLBACK = 'Toys & Collectibles'
# "Cards Against Humanity" is a party game, not trading cards.
CATEGORY_OVERRIDES = [(re.compile(r'cards against humanity', re.I), 'Toys & Collectibles')]


def _kw_regex(kw):
    body = re.escape(kw)
    end = '' if kw.endswith('!') else r'\b'
    return re.compile(r'(?<![\w-])' + body + r'(?:s|es)?' + end, re.I)


CATEGORY_REGEX = [(cat, [_kw_regex(k) for k in kws]) for cat, kws in CATEGORY_RULES]


# ---------------------------------------------------------------- app contract

def read_text(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def parse_default_fields(app_js):
    m = re.search(r'const DEFAULT_FIELDS = \{(.*?)\n\};', app_js, re.S)
    if not m:
        sys.exit('Could not find DEFAULT_FIELDS in app.js')
    body = re.sub(r'//[^\n]*', '', m.group(1))
    pairs = re.findall(
        r"(\w+)\s*:\s*('(?:[^'\\]|\\.)*'|-?\d+(?:\.\d+)?|true|false|\[\])", body)
    fields = {}
    for key, raw in pairs:
        if raw.startswith("'"):
            val = raw[1:-1].encode('latin-1', 'backslashreplace').decode('unicode_escape')
        else:
            val = raw
        fields[key] = val
    return fields


def template_columns(defaults):
    skip = {'id', 'created_at', 'updated_at', 'photos'}
    cols = [k for k in defaults if k not in skip]
    # v1.2.1 adds these two; place them where that release puts them.
    if 'buyer' not in cols:
        cols.insert(cols.index('poshmark_order_number') + 1, 'buyer')
    if 'date_shipped' not in cols:
        cols.insert(cols.index('date_sold') + 1, 'date_shipped')
    return cols


class SelectParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.options = {}
        self._select = None
        self._opt = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'select':
            self._select = a.get('name')
            if self._select:
                self.options.setdefault(self._select, [])
        elif tag == 'option' and self._select:
            self._opt = {'value': a.get('value'), 'text': ''}

    def handle_data(self, data):
        if self._opt is not None:
            self._opt['text'] += data

    def handle_endtag(self, tag):
        if tag == 'option' and self._opt is not None:
            v = self._opt['value']
            self.options[self._select].append(v if v is not None else self._opt['text'].strip())
            self._opt = None
        elif tag == 'select':
            self._select = None


def parse_select_options(index_html):
    p = SelectParser()
    p.feed(index_html)
    return p.options


# ---------------------------------------------------------------- sheet values

def money(v):
    """Sheet money cell -> Decimal, or None when blank / '---' / NaN."""
    s = (v or '').strip().replace('$', '').replace(',', '')
    if s in ('', '---', 'NaN', '-'):
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def money_str(d, keep_zero=False):
    if d is None or (d == 0 and not keep_zero):
        return ''
    return str(d.quantize(Decimal('0.01')))


def number(v):
    s = (v or '').strip()
    if s in ('', '---', 'NaN'):
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def num_str(d):
    if d is None:
        return ''
    s = format(d.normalize(), 'f')
    return s


def iso_date(v):
    s = (v or '').strip()
    if not s:
        return ''
    m = re.fullmatch(r'(\d{1,2})/(\d{1,2})/(\d{4})', s)
    if not m:
        raise ValueError('Unexpected date format: %r' % s)
    mo, d, y = (int(x) for x in m.groups())
    return '%04d-%02d-%02d' % (y, mo, d)


def categorize(item, crate):
    text = '%s %s' % (item, crate)
    for rx, cat in CATEGORY_OVERRIDES:
        if rx.search(text):
            return cat
    for cat, regexes in CATEGORY_REGEX:
        if any(r.search(text) for r in regexes):
            return cat
    return CATEGORY_FALLBACK


def crate_brand_tags(crate):
    crate = crate.strip()
    if not crate:
        return '', ''
    if crate.startswith('Loot Crate'):
        brand = 'Loot Crate'
        tags = [t.strip() for t in crate.split(':')]
    elif crate == 'Fallout Crate':
        brand = 'Loot Crate'
        tags = ['Fallout Crate', 'Loot Crate']
    elif crate == 'GeekFuel':
        brand, tags = 'GeekFuel', ['GeekFuel']
    else:
        brand, tags = '', [crate]
    return brand, ', '.join(t for t in tags if t)


# ---------------------------------------------------------------- conversion

def load_rows(args):
    if args.csv:
        with open(args.csv, encoding='utf-8-sig', newline='') as f:
            text = f.read()
    else:
        req = urllib.request.Request(args.url, headers={'User-Agent': 'sheet-to-ledger'})
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode('utf-8-sig')
    return list(csv.reader(io.StringIO(text, newline='')))


def cell(row, col):
    return row[col - 1].strip() if len(row) >= col else ''


def convert(rows, defaults, columns, selects):
    data = []
    for i, r in enumerate(rows[HEADER_ROW:], start=HEADER_ROW + 1):
        if cell(r, C_ID):
            data.append((i, r))

    out, skipped, issues = [], [], []
    sold_rows = []
    for sheet_row, r in data:
        sid = cell(r, C_ID)
        status_raw, site = cell(r, C_STATUS), cell(r, C_SITE)
        if status_raw == 'Duplicate':
            skipped.append(sid)
            continue
        if status_raw == 'Sold':
            status = 'Sold'
        elif status_raw == 'Listed':
            if site not in LISTED_STATUS:
                issues.append('ID %s: unknown Site %r, used Ready to List' % (sid, site))
            status = LISTED_STATUS.get(site, 'Ready to List')
        elif status_raw == 'Ready to Ship':
            status = 'Ready to List'
        elif status_raw == 'Not Packed':
            status = 'Draft'
        else:
            issues.append('ID %s: unknown Status %r, used Draft' % (sid, status_raw))
            status = 'Draft'

        rec = {c: '' for c in columns}
        item = cell(r, C_ITEM)
        crate = cell(r, C_CRATE)
        rec['sku'] = sid
        rec['name'] = item
        rec['listing_title'] = item[:80]
        rec['status'] = status
        rec['quantity'] = '1'
        rec['category'] = categorize(item, crate)
        rec['brand'], rec['tags'] = crate_brand_tags(crate)

        site_sold = cell(r, C_SITE_SOLD)
        if not site_sold and status == 'Sold' and site in ('eBay', 'Poshmark'):
            site_sold = site
        rec['sold_platform'] = site_sold

        rec['date_sold'] = iso_date(cell(r, C_SOLD_DATE))
        rec['date_listed'] = iso_date(cell(r, C_LISTED_DATE))

        ebay_no = cell(r, C_EBAY_NO)
        rec['ebay_item_number'] = ebay_no
        rec['url_ebay'] = 'https://www.ebay.com/itm/' + ebay_no if ebay_no else ''
        rec['poshmark_order_number'] = cell(r, C_POSH_NO)
        rec['upc'] = cell(r, C_UPC)
        rec['buyer'] = cell(r, C_BUYER)

        dims = [number(cell(r, c)) for c in (C_LEN, C_WID, C_HGT)]
        rec['box_length'], rec['box_width'], rec['box_height'] = (num_str(d) for d in dims)
        rec['dim_unit'] = 'in'
        lb, oz = number(cell(r, C_LB)), number(cell(r, C_OZ))
        total_oz = (lb or 0) * 16 + (oz or 0)
        rec['weight_value'] = num_str(total_oz) if total_oz else ''
        rec['weight_unit'] = 'oz'

        ship_notes = []
        material = cell(r, C_MATERIAL)
        if material:
            pkg = PACKAGE_MAP.get(material)
            if pkg is None:
                issues.append('ID %s: unknown Shipping Material %r, used Custom' % (sid, material))
                pkg = 'Custom'
            if pkg == 'BOX':
                longest = max((d for d in dims if d is not None), default=Decimal(0))
                pkg = 'Medium Box' if longest > 12 else 'Small Box'
            rec['package_type'] = pkg
            if material not in selects.get('package_type', []):
                ship_notes.append('Packaging: ' + material)
        tracking = cell(r, C_TRACKING)
        if tracking:
            ship_notes.append('Tracking: ' + tracking)
        rec['ship_notes'] = '; '.join(ship_notes)

        cost, tax, other = (money(cell(r, c)) for c in (C_COST, C_TAX, C_OTHER))
        rec['cost'], rec['item_tax'], rec['other_expenses'] = (money_str(x) for x in (cost, tax, other))

        price = money(cell(r, C_PRICE))
        ship_charged = money(cell(r, C_SHIP_CHARGED))
        sale_total = money(cell(r, C_SALE_TOTAL))
        postage = money(cell(r, C_POSTAGE))
        rec['price'] = money_str(price)
        rec['ship_cost'] = money_str(ship_charged)
        rec['postage_paid'] = money_str(postage)
        sold_price = None
        sold_basis = None
        if status == 'Sold':
            sale_total_v, ship_v, price_v = sale_total or 0, ship_charged or 0, price or 0
            sold_price = Decimal(sale_total_v - ship_v)
            sold_basis = 'sale total - postage'
            if SOLD_RULE == 'corrected':
                if not sale_total_v:
                    # Sale Price left blank on a Sold row. When a platform fee
                    # was recorded the sale happened, and the sheet's own Gross
                    # Sales (col 35) uses the listing price. With no fee there
                    # is no evidence of the amount: leave sold_price blank.
                    any_fee = any(money(cell(r, c)) for c in FEE_COLUMNS.values())
                    if any_fee:
                        sold_price, sold_basis = Decimal(price_v), 'blank sale price -> listing price'
                    else:
                        sold_price, sold_basis = None, 'blank sale price, no fee recorded -> left blank'
                elif ship_v and sale_total_v == price_v:
                    # Sale Price equals the listing price although postage
                    # was charged: the cell holds the item price alone (the
                    # sheet's Gross Sales adds the postage on top).
                    sold_price, sold_basis = Decimal(sale_total_v), 'sale price excludes postage'
            rec['sold_price'] = money_str(sold_price, keep_zero=True)
        elif sale_total:
            issues.append('ID %s: Sale Price %s on a %s row, not mapped' % (sid, sale_total, status_raw))

        fees = {}
        for field, col in FEE_COLUMNS.items():
            fees[field] = money(cell(r, col))
            rec[field] = money_str(fees[field])
        if fees['fee_other']:
            rec['fee_other_notes'] = 'Selling fee (from sheet)'

        notes = []
        if cell(r, C_NOTES):
            notes.append(cell(r, C_NOTES))
        sales_tax = money(cell(r, C_SALES_TAX))
        if sales_tax:
            notes.append('Sales tax on sheet: ' + money_str(sales_tax))
        notes.append('Imported from Google Sheet row ID %s on %s' % (sid, IMPORT_DATE))
        if cell(r, C_CHECK).upper() == 'TRUE':
            notes.append('Sheet checkbox: removed from both sites')
        rec['private_notes'] = '\n'.join(notes)

        # Blank cells would overwrite the app defaults on import; fill them.
        for k in columns:
            if rec[k] == '' and k in defaults and k != 'has_variations':
                d = defaults[k]
                if d not in ('', 'false', 'true', '[]'):
                    rec[k] = d

        out.append(rec)
        if status == 'Sold':
            sold_rows.append({
                'rec': rec, 'sale_total': sale_total or 0, 'ship': ship_charged or 0,
                'postage': postage or 0, 'cost': cost or 0, 'tax': tax or 0,
                'other': other or 0, 'fees': sum((v or 0) for v in fees.values()),
                'sheet_profit': money(cell(r, C_PROFIT)) or 0,
                'sheet_fees': money(cell(r, C_TOTAL_FEES)) or 0, 'sales_tax': sales_tax or 0,
                'sid': sid, 'basis': sold_basis, 'price': price or 0,
                'brief_sold': (sale_total or 0) - (ship_charged or 0),
                'fvf': fees['fee_ebay_fvf'] or 0, 'fvf_ship': fees['fee_ebay_fvf_shipping'] or 0,
                'gross_sales': money(cell(r, C_GROSS_SALES)) or 0,
                'gross_costs': money(cell(r, C_GROSS_COSTS)) or 0,
            })
    return data, out, skipped, issues, sold_rows


def d2(v):
    return Decimal(v or '0')


def report(rows, data, out, skipped, issues, sold_rows, columns, defaults, selects):
    sub = rows[SUBTOTAL_ROW - 1]
    print('== Rows')
    print('data rows read:   %d' % len(data))
    print('rows written:     %d' % len(out))
    print('skipped Duplicate IDs: %s' % (', '.join(skipped) or 'none'))
    print('status:   %s' % dict(Counter(r['status'] for r in out).most_common()))
    print('category: %s' % dict(Counter(r['category'] for r in out).most_common()))
    print('package:  %s' % dict(Counter(r['package_type'] for r in out).most_common()))
    print('sold_platform: %s' % dict(Counter(r['sold_platform'] for r in out).most_common()))
    diff_offer = sum(1 for s in sold_rows if s['rec']['sold_price'] != s['rec']['price'])
    print('Sold rows where sold_price != price: %d' % diff_offer)

    def total(field, rs=out):
        return sum(d2(r[field]) for r in rs)

    sold = [s['rec'] for s in sold_rows]
    fee_fields = list(FEE_COLUMNS)
    checks = [
        ('sum(price) vs col 29', total('price'), C_PRICE),
        ('sum(cost) vs col 24', total('cost'), C_COST),
        ('sum(item_tax) vs col 25', total('item_tax'), C_TAX),
        ('sum(other_expenses) vs col 26', total('other_expenses'), C_OTHER),
        ('Sold sum(sold_price+ship_cost) vs col 31', total('sold_price', sold) + total('ship_cost', sold), C_SALE_TOTAL),
        ('sum(ship_cost) vs col 30', total('ship_cost'), C_SHIP_CHARGED),
        ('sum(postage_paid) vs col 32', total('postage_paid'), C_POSTAGE),
        ('sum(all mapped fees) vs col 44', sum(total(f) for f in fee_fields), C_TOTAL_FEES),
    ]
    profit = sum(d2(r['sold_price']) + d2(r['ship_cost']) - d2(r['postage_paid']) - d2(r['cost'])
                 - d2(r['item_tax']) - d2(r['other_expenses']) - sum(d2(r[f]) for f in fee_fields)
                 for r in sold)
    checks.append(('Sold profit vs col 46 (all rows)', profit, C_PROFIT))
    print('\n== Checksums against Subtotals row %d' % SUBTOTAL_ROW)
    print('%-42s %12s %12s %10s' % ('check', 'ledger', 'sheet', 'delta'))
    for label, ours, col in checks:
        sheet = money(cell(sub, col)) or Decimal(0)
        print('%-42s %12s %12s %10s' % (label, ours.quantize(Decimal('0.01')), sheet,
                                        (ours - sheet).quantize(Decimal('0.01'))))
    sheet_fee_cols = {c: money(cell(sub, c)) for c in (C_INSERTION, C_FVF, C_FVF_SHIP, C_POSH_FEE,
                                                        C_SALES_TAX, C_PAYPAL, C_SELLING)}
    print('fee subtotals on sheet (37..43): %s' % {c: str(v) for c, v in sheet_fee_cols.items()})
    print('sales tax (col 41, kept in notes, not a fee): %s' % sheet_fee_cols[C_SALES_TAX])

    # Where do the deltas sit? Row-level comparisons for Sold rows.
    fee_mismatch = [s['sid'] for s in sold_rows if s['fees'] + s['sales_tax'] != s['sheet_fees'] and s['fees'] != s['sheet_fees']]
    print('Sold rows whose mapped fees (+/- sales tax) differ from col 44: %s' % (fee_mismatch or 'none'))
    nonsold_fees = [r['sku'] for r in out if r['status'] != 'Sold' and any(r[f] for f in fee_fields)]
    print('non-Sold rows carrying fees: %s' % (nonsold_fees or 'none'))
    nonsold_postage = [r['sku'] for r in out if r['status'] != 'Sold' and r['postage_paid']]
    print('non-Sold rows carrying postage_paid: %s' % (nonsold_postage or 'none'))
    nonsold_ship = [r['sku'] for r in out if r['status'] != 'Sold' and r['ship_cost']]
    print('non-Sold rows carrying ship_cost: %s' % (nonsold_ship or 'none'))
    prof_rows = []
    for s in sold_rows:
        r = s['rec']
        ours = (d2(r['sold_price']) + d2(r['ship_cost']) - d2(r['postage_paid']) - d2(r['cost'])
                - d2(r['item_tax']) - d2(r['other_expenses']) - sum(d2(r[f]) for f in fee_fields))
        if abs(ours - s['sheet_profit']) > Decimal('0.005'):
            prof_rows.append((s['sid'], str(ours - s['sheet_profit'])))
    print('Sold rows whose profit differs from col 46 (ID, delta): %s' % (prof_rows or 'none'))
    nonsold_profit = sum((money(cell(r, C_PROFIT)) or 0) for _, r in data
                         if cell(r, C_STATUS) != 'Sold')
    print('col 46 total on non-Sold rows: %s' % nonsold_profit)

    print('\n== sold_price rule: %s' % SOLD_RULE)
    changed = [s for s in sold_rows if d2(s['rec']['sold_price']) != s['brief_sold']
               or not s['rec']['sold_price']]
    for s in changed:
        print(' ID %s: %s (brief rule %s -> %s)' % (s['sid'], s['basis'], s['brief_sold'],
                                                   s['rec']['sold_price']))
    brief_total = sum(s['brief_sold'] for s in sold_rows)
    ours_total = sum(d2(s['rec']['sold_price']) for s in sold_rows)
    print(' sum(sold_price): %s (brief rule would give %s)' % (ours_total, brief_total))
    gross = sum(s['gross_sales'] for s in sold_rows)
    print(' Sold sum(sold_price+ship_cost) vs Sold sum(col 35 Gross Sales): %s vs %s' % (
        ours_total + sum(s['ship'] for s in sold_rows), gross))
    # eBay Final Value Fee was 10% on this sheet; the fee implies what the buyer paid.
    fvf_flags = []
    for s in sold_rows:
        r = s['rec']
        if r['sold_platform'] == 'eBay' and s['fvf']:
            implied_item = (s['fvf'] / Decimal('0.10')).quantize(Decimal('0.01'))
            implied_ship = (s['fvf_ship'] / Decimal('0.10')).quantize(Decimal('0.01'))
            if (abs(implied_item - d2(r['sold_price'])) > Decimal('0.10')
                    or abs(implied_ship - d2(r['ship_cost'])) > Decimal('0.10')):
                fvf_flags.append('%s (fee implies item %s + postage %s; file has %s + %s)' % (
                    s['sid'], implied_item, implied_ship, d2(r['sold_price']), d2(r['ship_cost'])))
    print(' eBay Sold rows where the 10%% FVF disagrees with the file: %s' % (fvf_flags or 'none'))

    # Reconcile Ledger profit with the sheet's col 46 on Sold rows.
    sheet_sold = sum(s['sheet_profit'] for s in sold_rows)
    tax = sum(s['sales_tax'] for s in sold_rows)
    double_cost = sum(s['cost'] + s['tax'] + s['other'] for s in sold_rows
                      if s['gross_costs'] - s['postage'] == s['cost'] + s['tax'] + s['other']
                      and s['cost'] + s['tax'] + s['other'])
    revenue_basis = sum((d2(s['rec']['sold_price']) + s['ship']) - s['gross_sales']
                        for s in sold_rows)
    print('\n== Profit reconciliation (Sold rows)')
    print(' sheet col 46, Sold rows only:              %10s' % sheet_sold)
    print(' + sales tax (sheet counts it as a fee):     %10s' % tax)
    print(' + item cost the sheet subtracts twice:      %10s' % double_cost)
    print(' + revenue: file sale total - sheet col 35:  %10s' % revenue_basis)
    expl = sheet_sold + tax + double_cost + revenue_basis
    print(' = explained Ledger profit                   %10s  (Ledger: %s, residual %s)' % (
        expl, profit.quantize(Decimal('0.01')), (profit - expl).quantize(Decimal('0.01'))))
    print(' col 46 on non-Sold rows (not in Ledger profit): %s' % nonsold_profit)

    print('\n== Sanity')
    expected = template_columns(defaults)
    print('header matches app template order: %s' % (columns == expected))
    bad = []
    for f in SELECT_FIELDS:
        opts = selects.get(f)
        if opts is None:
            bad.append('no <select name=%s> in index.html' % f)
            continue
        for r in out:
            if r[f] not in opts:
                bad.append('%s=%r (sku %s)' % (f, r[f], r['sku']))
    print('select values outside index.html options: %s' % (bad or 'none'))
    date_fields = [c for c in columns if c.startswith('date_') or c.endswith('_date')]
    bad_dates = [(r['sku'], f, r[f]) for r in out for f in date_fields
                 if r[f] and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', r[f])]
    print('non-ISO dates: %s' % (bad_dates or 'none'))
    money_fields = ['cost', 'price', 'min_price', 'sold_price', 'item_tax', 'other_expenses',
                    'ship_cost', 'postage_paid'] + fee_fields + ['fee_ebay_per_order']
    bad_money = [(r['sku'], f) for r in out for f in money_fields
                 if r[f] and not re.fullmatch(r'-?\d+\.\d{2}', r[f])]
    print('money cells not plain 2-decimal: %s' % (bad_money or 'none'))
    upc_len = Counter(len(r['upc']) for r in out if r['upc'])
    print('UPC lengths: %s' % dict(upc_len))
    if issues:
        print('\n== Issues')
        for i in issues:
            print(' - ' + i)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--url', default=SHEET_URL, help='CSV export URL (default: the owner sheet)')
    ap.add_argument('--csv', help='read a saved CSV export instead of downloading')
    ap.add_argument('--out', required=True, help='output CSV path (keep it outside the repo)')
    ap.add_argument('--sold-price-rule', choices=['corrected', 'brief'], default='corrected',
                    help='see SOLD_RULE above (default: corrected)')
    args = ap.parse_args()
    global SOLD_RULE
    SOLD_RULE = args.sold_price_rule

    out_abs = os.path.abspath(args.out)
    try:
        inside = os.path.commonpath([out_abs.lower(), REPO.lower()]) == REPO.lower()
    except ValueError:  # different drives
        inside = False
    if inside:
        sys.exit('Refusing to write inside the repo: the output contains buyer usernames.')

    defaults = parse_default_fields(read_text(os.path.join(REPO, 'app.js')))
    selects = parse_select_options(read_text(os.path.join(REPO, 'index.html')))
    columns = template_columns(defaults)

    rows = load_rows(args)
    header = [c.replace('\n', ' ').strip() for c in rows[HEADER_ROW - 1]]
    if header[C_ID - 1] != 'ID' or header[C_ITEM - 1] != 'Item':
        sys.exit('Sheet layout changed: row %d is not the expected header' % HEADER_ROW)

    data, out, skipped, issues, sold_rows = convert(rows, defaults, columns, selects)

    # No BOM: the app's parseCSV would keep it in the first header name.
    with open(out_abs, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator='\r\n')
        w.writerow(columns)
        for rec in out:
            w.writerow([rec[c] for c in columns])
    print('wrote %s' % out_abs)
    report(rows, data, out, skipped, issues, sold_rows, columns, defaults, selects)


if __name__ == '__main__':
    main()

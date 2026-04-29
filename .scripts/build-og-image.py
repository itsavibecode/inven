"""
Build The Ledger Open Graph image.

Output:
  T:/ClaudeCodeRepo/inven/og-image.png        (1200x630, share-target standard)
  T:/ClaudeCodeRepo/inven/apple-touch-icon.png (180x180, iOS home-screen)

Run from T:\\ClaudeCodeRepo\\inven with:
    python .scripts/build-og-image.py
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_OG = REPO / "og-image.png"
OUT_APPLE = REPO / "apple-touch-icon.png"

# Palette — mirrors styles.css (--bg-0, --accent, etc.)
BG       = (10, 13, 17)        # #0a0d11
PANEL    = (18, 22, 28)        # #12161c
LINE     = (36, 42, 51)        # #242a33
INK      = (240, 243, 247)     # #f0f3f7
INK_DIM  = (184, 194, 207)     # #b8c2cf
INK_FAINT= (124, 135, 148)     # #7c8794
ACCENT   = (45, 212, 191)      # #2dd4bf
HEART    = (239, 68, 68)       # #ef4444
DARK     = (13, 17, 23)        # #0d1117 — favicon's inner-detail color

FONTS = "C:/Windows/Fonts"
def f(name, size):
    return ImageFont.truetype(f"{FONTS}/{name}", size)

def text_size(draw, text, font):
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    return r - l, b - t

def draw_plush_bear(draw, cx, cy, scale):
    """Render the favicon plush bear centered at (cx, cy), 'scale' px tall.
    Mirrors favicon.svg's 0..64 viewBox geometry — ears, head, eyes, nose,
    smile, heart tag.
    """
    s = scale / 64.0  # px per SVG unit
    def t(x, y):
        return (cx + (x - 32) * s, cy + (y - 32) * s)
    def circle(svg_cx, svg_cy, svg_r, fill):
        x, y = t(svg_cx, svg_cy)
        r = svg_r * s
        draw.ellipse([x - r, y - r, x + r, y + r], fill=fill)
    def ellipse(svg_cx, svg_cy, svg_rx, svg_ry, fill):
        x, y = t(svg_cx, svg_cy)
        rx, ry = svg_rx * s, svg_ry * s
        draw.ellipse([x - rx, y - ry, x + rx, y + ry], fill=fill)

    circle(20, 22, 7,    ACCENT)              # Left ear outer
    circle(44, 22, 7,    ACCENT)              # Right ear outer
    circle(20, 22, 3,    DARK)                # Left ear inner
    circle(44, 22, 3,    DARK)                # Right ear inner
    circle(32, 34, 16,   ACCENT)              # Head
    circle(26, 32, 2.2,  DARK)                # Left eye
    circle(38, 32, 2.2,  DARK)                # Right eye
    circle(26.7, 31.3, 0.7, (255, 255, 255))  # Left eye highlight
    circle(38.7, 31.3, 0.7, (255, 255, 255))  # Right eye highlight
    ellipse(32, 38, 2.5, 1.8, DARK)           # Nose

    # Smile: SVG path "M 28 41 Q 32 43.5 36 41" — approx with a flat arc
    al, at_ = t(28, 40)
    ar, ab = t(36, 44)
    draw.arc([al, at_, ar, ab], start=15, end=165,
             fill=DARK, width=max(2, int(1.5 * s)))

    # Heart tag — SVG path "M 47 42 q -2 -3 -4 -1 q -2 -2 -4 1 q 0 3 4 6 q 4 -3 4 -6 z"
    # That's a small heart centered roughly at (43, 45). Approx with two
    # lobes + a triangular bottom point.
    hx, hy = t(43, 44)
    draw.ellipse([hx - 2.7 * s, hy - 1.6 * s,
                  hx - 0.1 * s, hy + 1.4 * s], fill=HEART)
    draw.ellipse([hx + 0.1 * s, hy - 1.6 * s,
                  hx + 2.7 * s, hy + 1.4 * s], fill=HEART)
    draw.polygon([
        (hx - 2.6 * s, hy + 0.4 * s),
        (hx + 2.6 * s, hy + 0.4 * s),
        (hx,            hy + 4.2 * s),
    ], fill=HEART)


# ----------------------------------------------------------------------------
# Open Graph image — 1200 x 630
# ----------------------------------------------------------------------------
W, H = 1200, 630
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img, "RGBA")

PAD = 48
d.rounded_rectangle([PAD, PAD, W - PAD, H - PAD], radius=24,
                    outline=LINE, width=2)

# --- Brand row (top-left) ---------------------------------------------------
brand_x, brand_y = PAD + 36, PAD + 36
draw_plush_bear(d, brand_x + 18, brand_y + 18, 38)
brand_font = f("Inter-SemiBold.ttf", 22)
d.text((brand_x + 52, brand_y + 9), "The Ledger", font=brand_font, fill=INK)

# Status pill (top-right)
status_text = "v0.4.0  ·  COLLECTIBLES INVENTORY"
status_font = f("Inter-SemiBold.ttf", 14)
sw, sh = text_size(d, status_text, status_font)
sp_x2 = W - PAD - 36
sp_y = brand_y
d.rounded_rectangle([sp_x2 - sw - 28, sp_y, sp_x2, sp_y + sh + 14],
                    radius=999, outline=LINE, width=1)
d.ellipse([sp_x2 - sw - 22, sp_y + sh / 2 + 2,
           sp_x2 - sw - 14, sp_y + sh / 2 + 10], fill=ACCENT)
d.text((sp_x2 - sw - 4, sp_y + 6), status_text, font=status_font, fill=ACCENT)

# --- Hero — big bear logo + title ------------------------------------------
draw_plush_bear(d, 280, 320, 280)

title_font = f("ariblk.ttf", 96)
d.text((480, 230), "The Ledger", font=title_font, fill=INK)

sub_font = f("Inter-Medium.ttf", 28)
d.text((480, 348), "Collectibles inventory", font=sub_font, fill=INK_DIM)
sub2_font = f("Inter-Medium.ttf", 22)
d.text((480, 388), "Beanies  ·  Poshmark & eBay listings  ·  Multi-device sync",
       font=sub2_font, fill=INK_FAINT)

# --- Bottom: feature pills + URL --------------------------------------------
pill_y = H - PAD - 88
features = ["UPC scanner", "Photo sync", "Real-time backup"]
pill_x = PAD + 36
pill_font = f("Inter-SemiBold.ttf", 14)
for feature in features:
    fw, fh = text_size(d, feature, pill_font)
    pw = fw + 28
    ph = fh + 14
    d.rounded_rectangle([pill_x, pill_y, pill_x + pw, pill_y + ph],
                        radius=999, fill=PANEL, outline=LINE, width=1)
    d.text((pill_x + 14, pill_y + 7), feature, font=pill_font, fill=ACCENT)
    pill_x += pw + 12

url_font = f("Inter-Medium.ttf", 18)
url_text = "itsavibecode.github.io/inven"
uw, uh = text_size(d, url_text, url_font)
d.text((W - PAD - 36 - uw, H - PAD - 18 - uh),
       url_text, font=url_font, fill=INK_FAINT)

img.save(OUT_OG, "PNG", optimize=True)
print(f"Wrote {OUT_OG}  ({OUT_OG.stat().st_size // 1024} KB)")

# ----------------------------------------------------------------------------
# Apple touch icon — 180 x 180
# ----------------------------------------------------------------------------
S = 180
icon = Image.new("RGB", (S, S), BG)
di = ImageDraw.Draw(icon)
di.rounded_rectangle([0, 0, S - 1, S - 1], radius=34, fill=BG)
draw_plush_bear(di, S / 2, S / 2 + 8, 145)

icon.save(OUT_APPLE, "PNG", optimize=True)
print(f"Wrote {OUT_APPLE}  ({OUT_APPLE.stat().st_size // 1024} KB)")

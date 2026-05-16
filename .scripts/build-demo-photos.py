"""
Build AI-generated product photos for Demo Mode items.

Fetches 12 photos from Pollinations.ai (free, no-auth image-gen service)
and saves them as small JPEGs in ../demo-photos/. The site references
those paths directly — Pollinations is not a runtime dependency, this
script just regenerates the static assets.

Re-run from T:\\ClaudeCodeRepo\\inven with:
    python .scripts/build-demo-photos.py

If a generated image is unsatisfying, tweak the prompt or change the
seed for that entry and re-run; the script overwrites existing files.
"""

import urllib.parse
import urllib.request
from pathlib import Path
from io import BytesIO
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "demo-photos"
OUT_DIR.mkdir(exist_ok=True)

# Reasonable defaults: 512x512 generation, downsized to 400x400 for the
# site, JPEG quality 75 -> ~30-40 KiB per file.
GEN_W, GEN_H = 512, 512
SAVE_W, SAVE_H = 400, 400
JPEG_QUALITY = 75

# (filename, prompt, seed). Seeds are arbitrary; they just make the
# generation reproducible across re-runs.
ITEMS = [
    ("princess.jpg",
     "A purple plush teddy bear with white embroidered rose on chest, vintage plush toy, soft studio lighting, plain neutral background, centered product photography",
     7),
    ("peanut-royal-blue.jpg",
     "A royal blue plush stuffed elephant with floppy ears and curled trunk, small vintage plush toy, soft studio lighting, plain white background, product photography",
     11),
    ("patti-platypus.jpg",
     "A magenta pink plush platypus stuffed animal with duck-like bill and flat tail, small vintage plush toy, soft studio lighting, plain white background",
     19),
    ("halo.jpg",
     "A white plush teddy bear with a small iridescent halo floating above its head, soft cute plush toy, white background, soft studio lighting, product photography",
     23),
    ("rex-trex.jpg",
     "A tie-dye orange red yellow plush stuffed Tyrannosaurus Rex dinosaur toy, soft studio lighting, plain white background, vintage plush product photo",
     31),
    ("iggy-iguana.jpg",
     "A blue plush iguana lizard stuffed animal, long body, small spines on back, soft studio lighting, plain white background, product photography",
     37),
    ("glory.jpg",
     "A white plush teddy bear with American flag embroidered on chest, patriotic plush toy, soft studio lighting, plain white background, product photography",
     41),
    ("holiday-teddy-2000.jpg",
     "A bright red plush teddy bear with embroidered white snowflakes, Christmas holiday plush toy, soft studio lighting, plain white background, product photography",
     43),
    ("spinner-spider.jpg",
     "A black plush spider stuffed toy with orange details and eight short plush legs, Halloween cute plush, soft studio lighting, plain white background",
     47),
    ("lefty-donkey.jpg",
     "A grey plush donkey stuffed animal with American flag patch on side, small vintage plush toy, soft studio lighting, plain white background",
     53),
    ("vintage-levis-jacket.jpg",
     "A vintage Levi's blue denim trucker jacket, medium wash, lay flat product photo on a clean neutral background, professional product photography",
     59),
    ("garcia.jpg",
     "A tie-dye plush teddy bear in swirling rainbow colors purple pink yellow green, soft studio lighting, plain white background, vintage plush product photo",
     61),
]

def gen(prompt, seed):
    """Fetch one image from Pollinations.ai. Returns raw bytes."""
    encoded = urllib.parse.quote(prompt, safe='')
    url = (f"https://image.pollinations.ai/prompt/{encoded}"
           f"?width={GEN_W}&height={GEN_H}&seed={seed}"
           f"&nologo=true&model=flux")
    req = urllib.request.Request(url, headers={"User-Agent": "inven-build-script/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()

def save(raw, out_path):
    """Downsize to SAVE_W x SAVE_H, save as optimized JPEG."""
    img = Image.open(BytesIO(raw)).convert("RGB")
    img = img.resize((SAVE_W, SAVE_H), Image.LANCZOS)
    img.save(out_path, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)

if __name__ == "__main__":
    for name, prompt, seed in ITEMS:
        out_path = OUT_DIR / name
        print(f"-> {name} (seed={seed}) ...", end="", flush=True)
        try:
            raw = gen(prompt, seed)
            save(raw, out_path)
            size_kb = out_path.stat().st_size // 1024
            print(f" ok ({size_kb} KiB)")
        except Exception as e:
            print(f" FAILED: {e}")

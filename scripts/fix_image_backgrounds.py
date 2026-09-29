from pathlib import Path
from PIL import Image

ASSETS_DIR = Path(__file__).resolve().parent.parent / "app" / "assets"

for name in ["printbutton.png", "emailbutton.png"]:
    path = ASSETS_DIR / name
    img = Image.open(path).convert("RGBA")
    pixels = [
        (r, g, b, 0) if r > 240 and g > 240 and b > 240 else (r, g, b, a)
        for r, g, b, a in img.getdata()
    ]
    img.putdata(pixels)
    img.save(path)
    print(f"Fixed: {path}")
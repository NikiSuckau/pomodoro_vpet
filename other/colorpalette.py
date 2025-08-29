# palette_to_png.py
# Usage:
#   python palette_to_png.py input.gpl out.png
#   python palette_to_png.py input.rpl out.png
#
# Requires: Pillow (pip install pillow)

import sys, json, math, pathlib
from PIL import Image, ImageDraw


def parse_gpl(path):
    colors = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if (
                not line
                or line.startswith("GIMP Palette")
                or ":" in line
                or line.startswith("#")
            ):
                # skip header/metadata/comments
                continue
            parts = line.split()
            if len(parts) >= 3:
                try:
                    r, g, b = map(int, parts[:3])
                    colors.append((r, g, b))
                except ValueError:
                    pass
    return colors


def parse_rpl(path):
    """Parse Resprite .rpl (JSON). We accept:
    - {"colors":[{"color":"#RRGGBB", ...}, ...]}
    - {"colors":[{"r":..,"g":..,"b":..}, ...]}
    - or any list of items containing 'color' or r/g/b.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # find a list that looks like colors
    if isinstance(data, dict) and "colors" in data and isinstance(data["colors"], list):
        items = data["colors"]
    elif isinstance(data, list):
        items = data
    else:
        # last resort: look for any list value named 'palette' or 'swatches'
        for key in ("palette", "swatches"):
            if isinstance(data, dict) and isinstance(data.get(key), list):
                items = data[key]
                break
        else:
            items = []

    def as_rgb(item):
        if isinstance(item, dict):
            if (
                "color" in item
                and isinstance(item["color"], str)
                and item["color"].startswith("#")
                and len(item["color"]) in (7, 9)
            ):
                hexv = item["color"][1:7]
                return tuple(int(hexv[i : i + 2], 16) for i in (0, 2, 4))
            if all(k in item for k in ("r", "g", "b")):
                return (int(item["r"]), int(item["g"]), int(item["b"]))
        if isinstance(item, str) and item.startswith("#") and len(item) >= 7:
            hexv = item[1:7]
            return tuple(int(hexv[i : i + 2], 16) for i in (0, 2, 4))
        return None

    colors = []
    for it in items:
        rgb = as_rgb(it)
        if rgb:
            colors.append(rgb)
    return colors


def load_colors(path):
    ext = pathlib.Path(path).suffix.lower()
    if ext == ".gpl":
        return parse_gpl(path)
    elif ext == ".rpl":
        return parse_rpl(path)
    else:
        raise SystemExit(f"Unsupported extension: {ext}")


def make_palette_png(colors, out_path, cell=32, cols=None, margin=8, gap=4):
    if not colors:
        raise SystemExit("No colors found.")

    n = len(colors)
    cols = cols or min(16, n)  # 16 per row by default (similar to many Lospec PNGs)
    rows = math.ceil(n / cols)

    W = margin * 2 + cols * cell + (cols - 1) * gap
    H = margin * 2 + rows * cell + (rows - 1) * gap

    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    for idx, (r, g, b) in enumerate(colors):
        r_i = idx // cols
        c_i = idx % cols
        x0 = margin + c_i * (cell + gap)
        y0 = margin + r_i * (cell + gap)
        draw.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], fill=(r, g, b))
    img.save(out_path)


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: python palette_to_png.py input.(gpl|rpl) out.png [cell=32] [cols=16]"
        )
        sys.exit(1)
    inp, outp = sys.argv[1], sys.argv[2]
    cell = int(sys.argv[3]) if len(sys.argv) > 3 else 32
    cols = int(sys.argv[4]) if len(sys.argv) > 4 else None

    colors = load_colors(inp)
    make_palette_png(colors, outp, cell=cell, cols=cols)


if __name__ == "__main__":
    main()

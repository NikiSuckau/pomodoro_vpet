import argparse
from PIL import Image

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Slice a sprite sheet of 48x48 px tiles into individual PNG sprites.",
        epilog="""
Example usage:
  python spriteslicer.py SHEET.png ROWS COLS OUTDIR
Where SHEET.png is your input sprite sheet, ROWS and COLS are the grid size, and OUTDIR is the output directory. Use -h for help.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("sheet", help="Path to the sprite sheet image")
    parser.add_argument("rows", type=int, help="Number of rows in the sprite sheet")
    parser.add_argument("cols", type=int, help="Number of columns in the sprite sheet")
    parser.add_argument("outdir", help="Output directory for the sprites")
    args = parser.parse_args()

    # Open the sprite sheet image
    img = Image.open(args.sheet)

    sprite_width = 48
    sprite_height = 48

    import os
    os.makedirs(args.outdir, exist_ok=True)

    index = 0
    for row in range(args.rows):
        for col in range(args.cols):
            left = col * sprite_width
            upper = row * sprite_height
            right = left + sprite_width
            lower = upper + sprite_height
            sprite = img.crop((left, upper, right, lower))
            out_path = os.path.join(args.outdir, f"{index}.png")
            sprite.save(out_path, format="PNG")
            index += 1

# import PIL

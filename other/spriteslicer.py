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
        formatter_class=argparse.RawDescriptionHelpFormatter,
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

    # Define actions and output file names
    action_to_filename = {
        "walk 1": "0.png",
        "walk 2": "1.png",
        "happy 1": "3.png",
        "happy 2": "7.png",
        "attack 1": "6.png",
        "attack 2": "11.png",
    }
    actions = list(action_to_filename.keys())

    # Map from action to grid index
    print("Grid positions are indexed as: row,col (0-based)")
    print("Sprite grid:")
    for r in range(args.rows):
        row_str = []
        for c in range(args.cols):
            idx = r * args.cols + c
            row_str.append(f"{r},{c} [{idx}]")
        print("  ".join(row_str))
    print()
    grid_choices = {}
    for action in actions:
        while True:
            user_input = input(
                f"For action '{action}', enter sprite position as row,col (e.g., 0,2): "
            ).strip()
            try:
                row, col = map(int, user_input.split(","))
                if 0 <= row < args.rows and 0 <= col < args.cols:
                    idx = row * args.cols + col
                    if idx in grid_choices.values():
                        print("This sprite is already assigned. Choose another.")
                        continue
                    grid_choices[action] = idx
                    break
                else:
                    print("Invalid row or col. Try again.")
            except Exception:
                print("Invalid format. Use row,col with integers.")

    # Now slice only the selected sprites
    for action, idx in grid_choices.items():
        row = idx // args.cols
        col = idx % args.cols
        left = col * sprite_width
        upper = row * sprite_height
        right = left + sprite_width
        lower = upper + sprite_height
        sprite = img.crop((left, upper, right, lower))
        out_path = os.path.join(args.outdir, action_to_filename[action])
        sprite.save(out_path, format="PNG")
        print(f"Saved {action} sprite to {out_path}")

# import PIL

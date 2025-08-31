# Prototype: Animated Wallpaper Engine (multiple sprites, random animation events)
# Uses PIL (Pillow) and imageio for video output
# Sprites: PNGs in other/ (Gekkomon, hyokomon, sheomon, input_spritesheet)
# Output: output_wallpaper.mp4 (to be set as wallpaper via Hidamari)

import os
import random

import imageio.v2 as imageio
from PIL import Image, ImageSequence

SPRITE_PATHS = [
    "Gekkomon.png",
    "hyokomon.png",
    "sheomon.png",
]
BG_COLOR = (200, 220, 255, 255)  # light blue
WIDTH, HEIGHT = 640, 360
FPS = 15
DURATION_SEC = 15  # total duration
N_FRAMES = FPS * DURATION_SEC
N_SPRITES = len(SPRITE_PATHS)


# Helper: load and scale sprite
def load_sprite(path, scale=2):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    return im.resize((w * scale, h * scale), resample=Image.Resampling.NEAREST)


class Sprite:
    def __init__(self, image, bounds):
        self.image = image
        self.w, self.h = image.size
        self.bounds = bounds
        self.x = random.randint(0, bounds[0] - self.w)
        self.y = random.randint(0, bounds[1] - self.h)
        self.vx = random.choice([-2, 2])
        self.vy = 0
        self.event = "walk"
        self.event_timer = random.randint(15, 90)
        self.flip = False

    def random_event(self):
        r = random.random()
        if r < 0.2:
            self.event = "idle"
            self.event_timer = random.randint(10, 40)
        elif r < 0.4:
            self.event = "attack"
            self.event_timer = random.randint(10, 25)
        else:
            self.event = "walk"
            self.event_timer = random.randint(20, 60)
            self.vx = random.choice([-2, 2])
            self.flip = self.vx < 0

    def update(self):
        self.event_timer -= 1
        if self.event_timer <= 0:
            self.random_event()
        if self.event == "walk":
            self.x += self.vx
            # Bounce on edges
            if self.x < 0:
                self.x = 0
                self.vx = abs(self.vx)
                self.flip = False
            elif self.x > self.bounds[0] - self.w:
                self.x = self.bounds[0] - self.w
                self.vx = -abs(self.vx)
                self.flip = True
        # Attack/idle: maybe do a little bounce or blink (future)

    def render(self, bg):
        im = (
            self.image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if self.flip
            else self.image
        )
        bg.paste(im, (int(self.x), int(self.y)), im)


# Load all sprites
sprites = [Sprite(load_sprite(p), (WIDTH, HEIGHT)) for p in SPRITE_PATHS]

frames = []
for t in range(N_FRAMES):
    bg = Image.new("RGBA", (WIDTH, HEIGHT), BG_COLOR)
    for sprite in sprites:
        sprite.update()
        sprite.render(bg)
    frames.append(bg)

# Write as mp4
fname = "output_wallpaper.mp4"
with imageio.get_writer(fname, fps=FPS, codec="libx264", quality=8) as w:
    for f in frames:
        w.append_data(imageio.core.util.Array(f.convert("RGB")))

print(f"Wrote {fname}.")

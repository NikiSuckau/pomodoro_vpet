# The file input_spritesheet.png contains a sprite sheet with 6 Frames (1 row, 6 columns). Its 48x48 per frame.
# Frame 1 and 2 are walking left
# Frame 3 and 4 are standing and being happy
# Frame 5 and 6 are attacking left.

# Goal for this code is to create a gif that animates the sprite sheet
# The sprite shall enter the screen from the right, walk to the middle, be happy, attack, be happy again and walk out of the screen to the left.
# For walking towards right mirror Frame 1&2

from PIL import Image
from PIL.Image import Transpose

# Load the sprite sheet
sheet = Image.open("input_spritesheet.png").convert("RGBA")

FRAME_WIDTH = 48
FRAME_HEIGHT = 48
N_FRAMES = 8

# Slice out the 6 frames in a list
frames = []
for i in range(N_FRAMES):
    left = i * FRAME_WIDTH
    upper = 0
    right = left + FRAME_WIDTH
    lower = FRAME_HEIGHT
    frame = sheet.crop((left, upper, right, lower))
    frames.append(frame)
# frames[0] = walk left 1
# frames[1] = walk left 2
# frames[2] = happy 1
# frames[3] = happy 2
# frames[4] = sleep 1
# frames[5] = sleep 2
# frames[6] = attack 1
# frames[7] = attack 2


# --- Next: mirror walk frames for walking right, implement action sequence logic, composite on background, export gif.


# --- Animation sequence parameters ---
BG_WIDTH = 96  # Background width (enough space for movement)
BG_HEIGHT = 48
SPRITE_Y = -1  # y position is fixed (top-aligned)

frames_out = []

# Define the animation sequence as (type, frame_image, x_offset)

# 1. Walk in from left to center (step length sync mechanics)
STEP_LENGTH = 24  # pixels covered per walk cycle (left+right)
WALKING_FPS = 10  # walking animation frames per second
CYCLE_FRAMES = 2  # Number of unique frames in a cycle (here 2: left and right)
CYCLE_DURATION = CYCLE_FRAMES / WALKING_FPS  # seconds for one cycle

walk_right_1 = frames[4].transpose(Transpose.FLIP_LEFT_RIGHT)
walk_right_2 = frames[5].transpose(Transpose.FLIP_LEFT_RIGHT)
walk_anim_frames = [walk_right_1, walk_right_2]

start_x = -FRAME_WIDTH
center_x = BG_WIDTH // 2 - FRAME_WIDTH // 2
walk_distance = center_x - start_x
n_cycles = int(walk_distance // STEP_LENGTH) + 1
frames_per_cycle = int(WALKING_FPS * CYCLE_FRAMES / CYCLE_FRAMES)  # =WALKING_FPS
walk_total_frames = n_cycles * CYCLE_FRAMES
move_per_frame = STEP_LENGTH / CYCLE_FRAMES

for i in range(walk_total_frames):
    anim_idx = i % 2
    walk_frame = walk_anim_frames[anim_idx]
    x = int(start_x + (i * move_per_frame))
    bg = Image.new("RGBA", (BG_WIDTH, BG_HEIGHT), (255, 255, 255, 0))
    bg.paste(walk_frame, (x, SPRITE_Y), walk_frame)
    frames_out.append(bg)

# 1.5 Pause a bit at center
idle_frames = [frames[1], frames[0]]
idle_steps = 2
for i in range(idle_steps):
    happy_frame = idle_frames[i % 2]
    bg = Image.new("RGBA", (BG_WIDTH, BG_HEIGHT), (255, 255, 255, 0))
    bg.paste(happy_frame, (center_x, SPRITE_Y), happy_frame)
    frames_out.append(bg)

# 1.5 Pause a bit at center
idle_frames = [frames[0], frames[0]]
idle_steps = 1
for i in range(idle_steps):
    happy_frame = idle_frames[i % 2]
    bg = Image.new("RGBA", (BG_WIDTH, BG_HEIGHT), (255, 255, 255, 0))
    bg.paste(happy_frame, (center_x, SPRITE_Y), happy_frame)
    frames_out.append(bg)

# 2. Stand happy (center)
happy_frames = [frames[2], frames[3]]
happy_steps = 8
for i in range(happy_steps):
    happy_frame = happy_frames[i % 2]
    bg = Image.new("RGBA", (BG_WIDTH, BG_HEIGHT), (255, 255, 255, 0))
    bg.paste(happy_frame, (center_x, SPRITE_Y), happy_frame)
    frames_out.append(bg)

# 2.5 Pause a bit at center
idle_frames = [frames[0], frames[0]]
idle_steps = 2
for i in range(idle_steps):
    happy_frame = idle_frames[i % 2]
    bg = Image.new("RGBA", (BG_WIDTH, BG_HEIGHT), (255, 255, 255, 0))
    bg.paste(happy_frame, (center_x, SPRITE_Y), happy_frame)
    frames_out.append(bg)


# 3. Attack (center)
attack_frames = [frames[6], frames[7]]
attack_steps = 6
for i in range(attack_steps):
    attack_frame = attack_frames[i % 2]
    bg = Image.new("RGBA", (BG_WIDTH, BG_HEIGHT), (255, 255, 255, 0))
    bg.paste(attack_frame, (center_x, SPRITE_Y), attack_frame)
    frames_out.append(bg)

# 3.5 Pause a bit at center
idle_frames = [frames[0], frames[0]]
idle_steps = 2
for i in range(idle_steps):
    happy_frame = idle_frames[i % 2]
    bg = Image.new("RGBA", (BG_WIDTH, BG_HEIGHT), (255, 255, 255, 0))
    bg.paste(happy_frame, (center_x, SPRITE_Y), happy_frame)
    frames_out.append(bg)


# # 4. sleep (center)
# sleep_frames = [frames[4], frames[5]]
# sleep_steps = 8
# for i in range(sleep_steps):
#     sleep_frame = sleep_frames[i % 2]
#     bg = Image.new("RGBA", (BG_WIDTH, BG_HEIGHT), (255, 255, 255, 0))
#     bg.paste(sleep_frame, (center_x, SPRITE_Y), sleep_frame)
#     frames_out.append(bg)

# # 4.5 Pause a bit at center
# idle_frames = [frames[1]]
# idle_steps = 1
# for i in range(idle_steps):
#     happy_frame = idle_frames[i % 2]
#     bg = Image.new("RGBA", (BG_WIDTH, BG_HEIGHT), (255, 255, 255, 0))
#     bg.paste(happy_frame, (center_x, SPRITE_Y), happy_frame)
#     frames_out.append(bg)

# 5. Happy (center again)
happy_steps_2 = 4
for i in range(happy_steps_2):
    happy_frame = happy_frames[i % 2]
    bg = Image.new("RGBA", (BG_WIDTH, BG_HEIGHT), (255, 255, 255, 0))
    bg.paste(happy_frame, (center_x, SPRITE_Y), happy_frame)
    frames_out.append(bg)

# 5.5 Pause a bit at center

idle_frames = [frames[0]]
idle_steps = 1
for i in range(idle_steps):
    happy_frame = idle_frames[i % 2]
    bg = Image.new("RGBA", (BG_WIDTH, BG_HEIGHT), (255, 255, 255, 0))
    bg.paste(happy_frame, (center_x, SPRITE_Y), happy_frame)
    frames_out.append(bg)

# 1.5 Pause a bit at center
idle_frames = [frames[0], frames[1]]
idle_steps = 2
for i in range(idle_steps):
    happy_frame = idle_frames[i % 2]
    bg = Image.new("RGBA", (BG_WIDTH, BG_HEIGHT), (255, 255, 255, 0))
    bg.paste(happy_frame, (center_x, SPRITE_Y), happy_frame)
    frames_out.append(bg)

# 5. Walk out to left (step length sync mechanics)
end_x = -FRAME_WIDTH
walk_distance_out = center_x - end_x
n_cycles_out = int(walk_distance_out // STEP_LENGTH) + 1
walk_total_frames_out = n_cycles_out * CYCLE_FRAMES
move_per_frame_out = STEP_LENGTH / CYCLE_FRAMES

for i in range(walk_total_frames_out):
    anim_idx = i % 2
    walk_frame = frames[4] if anim_idx == 0 else frames[5]  # walk left
    x = int(center_x - (i * move_per_frame_out))
    bg = Image.new("RGBA", (BG_WIDTH, BG_HEIGHT), (255, 255, 255, 0))
    bg.paste(walk_frame, (x, SPRITE_Y), walk_frame)
    frames_out.append(bg)

# --- Magnification option ---
MAGNIFICATION = 2  # Set to 1, 2, 4, or 8
if MAGNIFICATION > 1:
    scaled_frames = [
        f.resize(
            (f.width * MAGNIFICATION, f.height * MAGNIFICATION),
            resample=Image.Resampling.NEAREST,
        )
        for f in frames_out
    ]
else:
    scaled_frames = frames_out

# --- Save as gif (after all frames have been generated) ---
scaled_frames[0].save(
    "output_animation.gif",
    save_all=True,
    append_images=scaled_frames[1:],
    duration=700,  # 300 ms per frame (about 3 fps, adjust as needed)
    loop=0,
    disposal=2,
    transparency=0,
)

import os
from typing import Tuple

import pygame


class TimerDisplay:
    """Render the current mode and remaining time."""

    def __init__(self, center: Tuple[int, int], font: pygame.font.Font) -> None:
        self.center = center
        self.font = font
        self.mode_text = "WORK"
        self.time_text = "25:00"

    def update_time(self, time_text: str) -> None:
        self.time_text = time_text

    def update_mode(self, mode: str) -> None:
        self.mode_text = mode.upper()

    def draw(self, surface: pygame.Surface) -> None:
        mode_surf = self.font.render(self.mode_text, True, (255, 255, 255))
        time_surf = self.font.render(self.time_text, True, (255, 255, 255))
        mode_rect = mode_surf.get_rect(center=(self.center[0], self.center[1] - 30))
        time_rect = time_surf.get_rect(center=self.center)
        surface.blit(mode_surf, mode_rect)
        surface.blit(time_surf, time_rect)


class VPet:
    """Simple walking pet animation."""

    def __init__(self, sprite_directory: str, y: int) -> None:
        frames = []
        for idx in [0, 1]:
            path = os.path.join(sprite_directory, f"{idx}.png")
            frames.append(pygame.image.load(path).convert_alpha())
        self.frames = frames
        self.index = 0
        self.x = 0
        self.y = y
        self.direction = 1
        self.speed = 2
        self.frame_time = 0.0
        self.frame_delay = 0.3

    def update(self, dt: float, screen_width: int) -> None:
        self.frame_time += dt
        if self.frame_time >= self.frame_delay:
            self.frame_time = 0
            self.index = (self.index + 1) % len(self.frames)
        self.x += self.direction * self.speed
        if self.x < 0 or self.x + self.frames[0].get_width() > screen_width:
            self.direction *= -1

    def draw(self, surface: pygame.Surface) -> None:
        frame = self.frames[self.index]
        if self.direction < 0:
            frame = pygame.transform.flip(frame, True, False)
        surface.blit(frame, (self.x, self.y))

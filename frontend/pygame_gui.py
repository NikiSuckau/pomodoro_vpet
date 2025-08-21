"""Pygame-based GUI components for Pomodoro VPet.

This module provides reusable classes for rendering the timer, buttons and
virtual pet using pygame.  It replaces the old tkinter implementation with a
clean, object-oriented pygame approach.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import pygame

# Helper data class ---------------------------------------------------------

@dataclass
class ButtonStyle:
    """Visual style for :class:`Button`."""

    bg_color: Tuple[int, int, int]
    text_color: Tuple[int, int, int]


class Button:
    """Simple clickable rectangle button."""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        font: pygame.font.Font,
        style: ButtonStyle,
        callback: Optional[Callable[[], None]] = None,
    ) -> None:
        self.rect = rect
        self.text = text
        self.font = font
        self.style = style
        self.callback = callback

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.style.bg_color, self.rect, border_radius=4)
        label = self.font.render(self.text, True, self.style.text_color)
        surface.blit(label, label.get_rect(center=self.rect.center))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()

    def set_text(self, text: str) -> None:
        self.text = text


# Timer display -------------------------------------------------------------

class TimerDisplay:
    """Render the current mode and remaining time."""

    def __init__(self, font_large: pygame.font.Font, font_small: pygame.font.Font) -> None:
        self.font_large = font_large
        self.font_small = font_small
        self.mode = "work"
        self.time_remaining = 25 * 60

    # ------------------------------------------------------------------
    def set_time(self, seconds: int) -> None:
        self.time_remaining = max(0, seconds)

    def set_mode(self, mode: str) -> None:
        self.mode = mode

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface, position: Tuple[int, int]) -> None:
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        time_text = f"{minutes:02d}:{seconds:02d}"
        mode_text = "WORK" if self.mode == "work" else "BREAK"
        color = (231, 76, 60) if self.mode == "work" else (39, 174, 96)

        mode_surf = self.font_small.render(f"{mode_text} TIME", True, (255, 255, 255))
        time_surf = self.font_large.render(time_text, True, color)

        x, y = position
        surface.blit(mode_surf, (x - mode_surf.get_width() // 2, y))
        surface.blit(time_surf, (x - time_surf.get_width() // 2, y + mode_surf.get_height()))


# VPet rendering ------------------------------------------------------------

class VPetRenderer:
    """Convert backend sprite data to pygame surfaces and render them."""

    def __init__(self, surface: pygame.Surface, engine) -> None:  # type: ignore[valid-type]
        self.surface = surface
        self.engine = engine
        self.sprite_cache: Dict[str, pygame.Surface] = {}
        self.projectile_cache: Dict[str, pygame.Surface] = {}

        self.x = 0
        self.y = 0
        self.sprite: Optional[pygame.Surface] = None
        self.projectiles: List[Tuple[int, int, Optional[pygame.Surface]]] = []

    # ------------------------------------------------------------------
    def _convert_sprite(self, sprite_data, sprite_key: str, cache: Dict[str, pygame.Surface]) -> Optional[pygame.Surface]:
        if sprite_data is None:
            return None
        if sprite_key in cache:
            return cache[sprite_key]
        try:
            if hasattr(sprite_data, "tobytes") and hasattr(sprite_data, "size"):
                mode = sprite_data.mode
                size = sprite_data.size
                data = sprite_data.tobytes()
                surf = pygame.image.fromstring(data, size, mode).convert_alpha()
            else:
                surf = pygame.image.load(sprite_data).convert_alpha()
            cache[sprite_key] = surf
            return surf
        except Exception:
            return None

    # ------------------------------------------------------------------
    def update_from_engine(self, x: int, y: int, frame: int, key: str, projectiles: list) -> None:
        sprite_data = self.engine.get_sprite(key)
        self.sprite = self._convert_sprite(sprite_data, key, self.sprite_cache)
        self.x = x
        self.y = y
        self.projectiles = []
        for proj in projectiles:
            psprite_data = self.engine.get_projectile_sprite(proj.get("sprite_key", ""))
            psurf = self._convert_sprite(psprite_data, proj.get("sprite_key", ""), self.projectile_cache)
            self.projectiles.append((proj.get("x", 0), proj.get("y", 0), psurf))

    # ------------------------------------------------------------------
    def draw(self) -> None:
        # clear background rectangle for pet area
        pygame.draw.rect(self.surface, (52, 73, 94), pygame.Rect(10, 220, 230, 70))
        if self.sprite:
            self.surface.blit(self.sprite, (self.x, self.y - self.sprite.get_height() // 2))
        else:
            # fallback rectangle
            pygame.draw.rect(
                self.surface,
                (231, 76, 60) if self.engine.current_mode == "work" else (39, 174, 96),
                pygame.Rect(self.x, self.y - 10, 20, 20),
            )
        for px, py, surf in self.projectiles:
            if surf:
                self.surface.blit(surf, (px, py - surf.get_height() // 2))


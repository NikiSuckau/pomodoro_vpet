"""Pygame based GUI components for the Pomodoro VPet app."""
from __future__ import annotations

import pygame
from typing import Callable, List


class Button:
    """Simple clickable button used throughout the interface."""

    def __init__(self, rect: pygame.Rect, text: str, callback: Callable[[], None]):
        self.rect = rect
        self.text = text
        self.callback = callback
        self.font = pygame.font.Font(None, 20)
        self.bg_color = (200, 200, 200)
        self.fg_color = (0, 0, 0)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.bg_color, self.rect)
        text_surf = self.font.render(self.text, True, self.fg_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class PomodoroGUI:
    """Displays timer information and control buttons."""

    def __init__(self, screen: pygame.Surface, engine, y_offset: int = 10) -> None:
        self.screen = screen
        self.engine = engine
        self.font = pygame.font.Font(None, 32)
        self.y_offset = y_offset

        # Buttons ------------------------------------------------------
        self.buttons: List[Button] = []
        w, h = 60, 25
        margin = 10
        start_x = (screen.get_width() - (w * 4 + margin * 3)) // 2
        btn_y = y_offset + 60

        self.buttons.append(Button(pygame.Rect(start_x, btn_y, w, h), "Start", self.engine.start))
        self.buttons.append(Button(pygame.Rect(start_x + (w + margin), btn_y, w, h), "Pause", self.engine.pause))
        self.buttons.append(Button(pygame.Rect(start_x + 2 * (w + margin), btn_y, w, h), "Resume", self.engine.resume))
        self.buttons.append(Button(pygame.Rect(start_x + 3 * (w + margin), btn_y, w, h), "Reset", self.engine.reset))

    def handle_event(self, event: pygame.event.Event) -> None:
        for btn in self.buttons:
            btn.handle_event(event)

    def draw(self) -> None:
        state = self.engine.get_state()
        time_text = self.engine.format_time(state["time_remaining"])
        mode = state["current_mode"].upper()
        mode_color = (200, 50, 50) if mode == "WORK" else (50, 200, 50)

        # Draw mode and time
        mode_surf = self.font.render(f"{mode} TIME", True, mode_color)
        time_surf = self.font.render(time_text, True, (255, 255, 255))
        mode_rect = mode_surf.get_rect(center=(self.screen.get_width() // 2, self.y_offset + 10))
        time_rect = time_surf.get_rect(center=(self.screen.get_width() // 2, self.y_offset + 40))
        self.screen.blit(mode_surf, mode_rect)
        self.screen.blit(time_surf, time_rect)

        for btn in self.buttons:
            btn.draw(self.screen)


class VPetGUI:
    """Responsible for drawing the virtual pet and its projectiles."""

    def __init__(self, screen: pygame.Surface, engine, y_pos: int) -> None:
        self.screen = screen
        self.engine = engine
        self.y_pos = y_pos

    def draw(self) -> None:
        # Draw pet
        sprite = self.engine.get_current_sprite()
        y = self.y_pos + (self.engine.canvas_height - self.engine.sprite_height) // 2
        self.screen.blit(sprite, (self.engine.x_position, y))

        # Draw projectiles as simple rectangles
        for proj in self.engine.projectiles:
            pygame.draw.rect(self.screen, (255, 255, 0), pygame.Rect(proj["x"], y + proj["y"], 5, 2))

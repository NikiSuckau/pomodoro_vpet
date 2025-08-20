"""Main application window using pygame."""

from __future__ import annotations

import pygame
from backend.pomodoro_engine import PomodoroEngine
from frontend.pygame_gui import Button, TimerDisplay, ToggleButton, VPet


class MainWindow:
    """Coordinate the Pomodoro engine with pygame rendering."""

    def __init__(self) -> None:
        pygame.init()
        self.size = (400, 300)
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption("Pomodoro VPet")
        self.clock = pygame.time.Clock()

        font = pygame.font.SysFont("arial", 24)
        center = (self.size[0] // 2, 80)
        self.timer_display = TimerDisplay(center, font)
        self.vpet = VPet("sprites/Agumon_penc", y=180)

        self.engine = PomodoroEngine()
        self.engine.set_callbacks(
            on_tick=self._on_tick,
            on_mode_change=self._on_mode_change,
        )

        btn_font = pygame.font.SysFont("arial", 18)
        self.start_btn = Button(pygame.Rect(20, 220, 80, 30), "Start", btn_font, self._toggle_timer)
        self.reset_btn = Button(pygame.Rect(110, 220, 80, 30), "Reset", btn_font, self._reset_timer)
        self.pet_toggle = ToggleButton(
            pygame.Rect(200, 220, 100, 30),
            "Pet On",
            "Pet Off",
            btn_font,
            self._set_pet_visible,
        )
        self.buttons = [self.start_btn, self.reset_btn, self.pet_toggle]
        self.show_pet = True

    # ------------------------------------------------------------------
    # Engine callbacks
    def _on_tick(self, remaining: int) -> None:
        self.timer_display.update_time(self.engine.format_time(remaining))

    def _on_mode_change(self, old: str, new: str) -> None:
        self.timer_display.update_mode(new)

    # ------------------------------------------------------------------
    # Event loop
    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self._toggle_timer()
                    elif event.key == pygame.K_r:
                        self._reset_timer()
                else:
                    for btn in self.buttons:
                        btn.handle_event(event)
            if self.show_pet:
                self.vpet.update(dt, self.size[0])
            self._draw()
        pygame.quit()

    def _toggle_timer(self) -> None:
        state = self.engine.get_state()
        if not state["is_running"] and not state["is_paused"]:
            self.engine.start()
            self.start_btn.set_text("Pause")
        elif state["is_running"]:
            self.engine.pause()
            self.start_btn.set_text("Resume")
        elif state["is_paused"]:
            self.engine.resume()
            self.start_btn.set_text("Pause")

    def _reset_timer(self) -> None:
        self.engine.reset()
        self.start_btn.set_text("Start")

    def _set_pet_visible(self, visible: bool) -> None:
        self.show_pet = visible

    def _draw(self) -> None:
        self.screen.fill((30, 30, 30))
        self.timer_display.draw(self.screen)
        if self.show_pet:
            self.vpet.draw(self.screen)
        for btn in self.buttons:
            btn.draw(self.screen)
        pygame.display.flip()

"""Main application window using pygame."""

from __future__ import annotations

import pygame
from backend.pomodoro_engine import PomodoroEngine
from frontend.pygame_gui import TimerDisplay, VPet


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
                        self.engine.reset()
            self.vpet.update(dt, self.size[0])
            self._draw()
        pygame.quit()

    def _toggle_timer(self) -> None:
        state = self.engine.get_state()
        if not state["is_running"] and not state["is_paused"]:
            self.engine.start()
        elif state["is_running"]:
            self.engine.pause()
        elif state["is_paused"]:
            self.engine.resume()

    def _draw(self) -> None:
        self.screen.fill((30, 30, 30))
        self.timer_display.draw(self.screen)
        self.vpet.draw(self.screen)
        pygame.display.flip()

"""Pygame application tying together the timer engine and the VPet."""
from __future__ import annotations

import pygame

from backend.pomodoro_engine import PomodoroEngine
from backend.vpet_engine import VPetEngine
from frontend.pygame_gui import PomodoroGUI, VPetGUI


class PomodoroApp:
    """Main controller running the Pygame event loop."""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((250, 300))
        pygame.display.set_caption("Pomodoro VPet")
        self.clock = pygame.time.Clock()

        # Engines ------------------------------------------------------
        self.timer = PomodoroEngine()
        self.vpet = VPetEngine()
        self.vpet.set_canvas_size(230, 60)

        # GUI layers ---------------------------------------------------
        self.pomodoro_gui = PomodoroGUI(self.screen, self.timer, y_offset=10)
        vpet_y = self.screen.get_height() - self.vpet.canvas_height
        self.vpet_gui = VPetGUI(self.screen, self.vpet, vpet_y)

        self.running = True

    # ------------------------------------------------------------------
    def run(self) -> None:
        """Run the main game loop."""
        while self.running:
            dt = self.clock.tick(30) / 1000.0
            self._handle_events()

            # Update engine state
            self.vpet.current_mode = self.timer.current_mode
            self.vpet.is_timer_running = self.timer.is_running and not self.timer.is_paused
            self.vpet.update(dt)

            # Draw everything
            self.screen.fill((1, 2, 3))
            self.pomodoro_gui.draw()
            self.vpet_gui.draw()
            pygame.display.flip()

        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.pomodoro_gui.handle_event(event)


__all__ = ["PomodoroApp"]

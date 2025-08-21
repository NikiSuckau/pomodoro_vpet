"""Pygame front-end application controller for Pomodoro VPet.

This module replaces the previous tkinter based ``MainWindow`` with a pygame
implementation.  It wires together the backend engines with the new GUI classes
found in :mod:`frontend.pygame_gui`.
"""

from __future__ import annotations

from typing import Dict

import pygame

from backend.pomodoro_engine import PomodoroEngine
from backend.vpet_engine import VPetEngine
from frontend.pygame_gui import Button, ButtonStyle, TimerDisplay, VPetRenderer


class PygameApp:
    """Main pygame application."""

    def __init__(self) -> None:
        pygame.init()
        self.size = (250, 300)
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption("Pomodoro VPet")
        self.clock = pygame.time.Clock()

        # Engines -------------------------------------------------------
        self.vpet_engine = VPetEngine()
        vpet_name = self._extract_vpet_name()
        self.pomodoro_engine = PomodoroEngine(vpet_name=vpet_name)

        # GUI components ------------------------------------------------
        font_large = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 20)
        self.timer_display = TimerDisplay(font_large, font_small)

        btn_font = pygame.font.Font(None, 20)
        style_green = ButtonStyle((78, 205, 196), (44, 62, 80))
        style_red = ButtonStyle((255, 118, 117), (44, 62, 80))
        style_yellow = ButtonStyle((255, 224, 102), (44, 62, 80))
        style_gray = ButtonStyle((149, 165, 166), (44, 62, 80))

        self.buttons: Dict[str, Button] = {}
        self.buttons["start"] = Button(
            pygame.Rect(20, 110, 60, 30), "Start", btn_font, style_green, self._on_start_pause
        )
        self.buttons["reset"] = Button(
            pygame.Rect(95, 110, 60, 30), "Reset", btn_font, style_red, self._on_reset
        )
        self.buttons["skip"] = Button(
            pygame.Rect(170, 110, 60, 30), "Skip", btn_font, style_yellow, self._on_skip
        )
        self.buttons["exit"] = Button(
            pygame.Rect(95, 150, 60, 30), "Exit", btn_font, style_gray, self._on_exit
        )

        self.vpet_renderer = VPetRenderer(self.screen, self.vpet_engine)

        # Callbacks -----------------------------------------------------
        self.pomodoro_engine.set_callbacks(
            on_tick=self._on_tick,
            on_mode_change=self._on_mode_change,
            on_session_complete=self._on_session_complete,
        )
        self.vpet_engine.set_callbacks(
            on_position_update=self.vpet_renderer.update_from_engine
        )

        self.vpet_engine.start_animation()
        self.timer_display.set_time(self.pomodoro_engine.time_remaining)

        self.running = True

    # ------------------------------------------------------------------
    def _extract_vpet_name(self) -> str:
        sprite_dir = self.vpet_engine.sprite_directory
        name = sprite_dir.split("/")[-1]
        if name.endswith("_penc"):
            name = name[:-5]
        return name

    # Callbacks from engines -------------------------------------------
    def _on_tick(self, remaining: int) -> None:
        self.timer_display.set_time(remaining)

    def _on_mode_change(self, old_mode: str, new_mode: str) -> None:
        self.timer_display.set_mode(new_mode)
        self.vpet_engine.set_mode(new_mode)

    def _on_session_complete(self, completed_mode: str) -> None:
        pass

    # Button callbacks -------------------------------------------------
    def _on_start_pause(self) -> None:
        state = self.pomodoro_engine.get_state()
        if not state["is_running"] and not state["is_paused"]:
            if self.pomodoro_engine.start():
                self.buttons["start"].set_text("Pause")
                self.vpet_engine.set_timer_running(True)
        elif state["is_running"]:
            if self.pomodoro_engine.pause():
                self.buttons["start"].set_text("Resume")
                self.vpet_engine.set_timer_running(False)
        elif state["is_paused"]:
            if self.pomodoro_engine.resume():
                self.buttons["start"].set_text("Pause")
                self.vpet_engine.set_timer_running(True)

    def _on_reset(self) -> None:
        self.pomodoro_engine.reset()
        self.buttons["start"].set_text("Start")
        self.vpet_engine.set_timer_running(False)
        self.timer_display.set_time(self.pomodoro_engine.time_remaining)
        self.timer_display.set_mode("work")

    def _on_skip(self) -> None:
        self.pomodoro_engine.skip_session()

    def _on_exit(self) -> None:
        self.running = False

    # Main loop --------------------------------------------------------
    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    for btn in self.buttons.values():
                        btn.handle_event(event)

            self.screen.fill((1, 2, 3))
            self.timer_display.draw(self.screen, (self.size[0] // 2, 20))
            for btn in self.buttons.values():
                btn.draw(self.screen)
            self.vpet_renderer.draw()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


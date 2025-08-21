"""Pygame based virtual pet engine.

This module provides a small engine that keeps track of the virtual
pet's position, animation frame and custom events.  It is purposely
free of any rendering code so it can be used in tests or different
front ends.  Rendering is handled separately by the Pygame GUI layer.

The implementation is intentionally lightweight compared to the
original tkinter version but keeps the same public API that is used in
our tests.  Only a subset of the features are implemented which keeps
it easy to understand and extend.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Dict, List, Optional

import pygame

from .pet_events import (
    AttackTrainingEvent,
    HappyEvent,
    PetEvent,
    collect_event_frames,
)


class VPetEngine:
    """Core logic for the virtual pet.

    The engine keeps track of the pet's walking animation, queued
    events and projectiles fired during the *attack* event.  It does not
    depend on any GUI framework which makes it straightforward to unit
    test.  Sprites are loaded as :class:`pygame.Surface` objects but the
    engine itself never blits them to the screen.
    """

    def __init__(self, sprite_directory: str = "sprites/Agumon_penc") -> None:
        self.sprite_directory = sprite_directory

        # Loaded sprites keyed by their numeric filename (``"0"``, ``"1"`` ...)
        self.sprites: Dict[str, pygame.Surface] = {}
        self.projectile_sprites: Dict[str, pygame.Surface] = {}
        self._load_sprites()

        # Position and movement state
        self.x_position = 10
        self.direction = 1  # 1 -> right, -1 -> left
        self.canvas_width = 230
        self.canvas_height = 60
        self.sprite_width = 48
        self.sprite_height = 48
        self.margin = 12

        # Walking animation frames (facing left in sprite sheet)
        self.walk_frames = [0, 1]
        self.walk_frame_index = 0
        self.current_frame = self.walk_frames[self.walk_frame_index]

        # Projectile handling for attack event
        self.projectiles: List[dict] = []
        self.projectile_speed = 12
        self.projectile_width = 20

        # Event system -------------------------------------------------
        self.events: Dict[str, PetEvent] = {}
        self.active_event: Optional[PetEvent] = None
        self.event_queue: List[str] = []
        self._register_default_events()

        # Random walk behaviour
        self.distance_walked = 0
        self.minimum_walk_distance = 25
        self.direction_change_probability = 0.07

        # Behaviour flags updated by the Pomodoro timer
        self.current_mode = "work"  # "work" or "break"
        self.is_timer_running = False

    # ------------------------------------------------------------------
    # Sprite handling
    # ------------------------------------------------------------------
    def _load_sprites(self) -> None:
        """Load all sprite frames from ``self.sprite_directory``."""
        if not pygame.get_init():
            pygame.init()
        if not pygame.display.get_surface():  # ensure a display for convert_alpha
            pygame.display.set_mode((1, 1))

        sprite_dir = Path(self.sprite_directory)
        if sprite_dir.exists():
            for img_path in sprite_dir.glob("*.png"):
                self.sprites[img_path.stem] = pygame.image.load(str(img_path)).convert_alpha()

        attack_dir = Path("sprites/attacks")
        if attack_dir.exists():
            for img_path in attack_dir.glob("*.png"):
                self.projectile_sprites[img_path.stem] = pygame.image.load(str(img_path)).convert_alpha()

        # Determine sprite size from first loaded sprite
        if self.sprites:
            sample = next(iter(self.sprites.values()))
            self.sprite_width, self.sprite_height = sample.get_size()

    # ------------------------------------------------------------------
    # Event registration and queueing
    # ------------------------------------------------------------------
    def _register_default_events(self) -> None:
        """Register built-in events used by the application."""
        self.register_event(AttackTrainingEvent())
        self.register_event(HappyEvent())

    def register_event(self, event: PetEvent) -> None:
        self.events[event.name] = event

    def queue_event(self, name: str) -> None:
        """Queue an event by name.

        If no event is currently active the new event starts immediately.
        Otherwise it will be executed once the current event finishes.
        """
        if self.active_event is None:
            self._activate_event(name)
        else:
            self.event_queue.append(name)

    def _activate_event(self, name: str) -> None:
        event = self.events.get(name)
        if event:
            self.active_event = event
            event.start(self)

    # ------------------------------------------------------------------
    # Movement and animation
    # ------------------------------------------------------------------
    def set_canvas_size(self, width: int, height: int) -> None:
        self.canvas_width = width
        self.canvas_height = height

    def update(self, dt: float = 0.1) -> None:
        """Advance the animation by ``dt`` seconds."""
        if self.active_event:
            frame, finished = self.active_event.update(self)
            self.current_frame = frame
            if finished:
                next_event = self.active_event.complete(self)
                self.active_event = None
                if next_event:
                    self._activate_event(next_event)
                elif self.event_queue:
                    self._activate_event(self.event_queue.pop(0))
        else:
            self._walk(dt)
            # Randomly trigger events when none is active
            for event in self.events.values():
                if event.should_trigger(self):
                    self._activate_event(event.name)
                    break

        self._update_projectiles()

    def _walk(self, dt: float) -> None:
        move_speed = 3 if self.current_mode == "work" else 1
        distance = move_speed * dt * self.direction
        self.x_position += distance
        self.distance_walked += abs(distance)

        right_boundary = self.canvas_width - self.sprite_width - self.margin
        left_boundary = self.margin
        if self.x_position >= right_boundary:
            self.direction = -1
            self.x_position = right_boundary
            self.distance_walked = 0
        elif self.x_position <= left_boundary:
            self.direction = 1
            self.x_position = left_boundary
            self.distance_walked = 0
        elif (
            self.distance_walked >= self.minimum_walk_distance
            and random.random() < self.direction_change_probability
        ):
            self.direction *= -1
            self.distance_walked = 0

        # Alternate walking frames
        self.walk_frame_index = 1 - self.walk_frame_index
        self.current_frame = self.walk_frames[self.walk_frame_index]

    # ------------------------------------------------------------------
    # Projectile management
    # ------------------------------------------------------------------
    def launch_projectile(self) -> None:
        """Spawn a projectile travelling in the current direction."""
        start_x = self.x_position + (self.sprite_width if self.direction == 1 else 0)
        start_y = self.canvas_height - self.sprite_height // 2
        self.projectiles.append({"x": start_x, "y": start_y, "dir": self.direction})

    def _update_projectiles(self, step: Optional[float] = None) -> None:
        """Advance existing projectiles and remove those that left the canvas."""
        if step is None:
            step = self.projectile_speed
        for proj in list(self.projectiles):
            proj["x"] += step * proj["dir"]
            if (
                proj["x"] < -self.projectile_width
                or proj["x"] > self.canvas_width + self.projectile_width
            ):
                self.projectiles.remove(proj)

    # ------------------------------------------------------------------
    # Utility helpers for the GUI layer
    # ------------------------------------------------------------------
    def get_current_sprite(self) -> pygame.Surface:
        """Return the current sprite frame as a Pygame surface."""
        key = str(self.current_frame)
        image = self.sprites[key]
        if self.direction == 1:
            return image
        return pygame.transform.flip(image, True, False)

    def required_frames(self) -> set[int]:
        """Return all frame indices required by registered events."""
        return collect_event_frames(self.events)

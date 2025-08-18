"""
VPet Backend Engine

This module contains the core logic for the virtual pet,
including sprite management, animation state, and behavior logic.
"""

import random
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from .pet_events import (AttackTrainingEvent, HappyEvent, PetEvent,
                         collect_event_frames)

# Enhanced imports with fallbacks
try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageTk

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.info("PIL not available - using basic sprite loading")


class VPetEngine:
    """
    Core VPet engine handling sprite management, animation logic, and pet behavior.

    This class is responsible for:
    - Loading and managing sprite assets
    - Animation state and timing
    - Movement and behavior logic
    - Pet state based on timer mode
    """

    def __init__(
        self,
        sprite_directory: str = "sprites/Agumon_penc",
        root_window: Optional[object] = None,
    ):
        """
        Initialize the VPet engine.

        Args:
            sprite_directory: Path to the directory containing sprite files
            root_window: Reference to the main tkinter window for thread-safe updates
        """
        self.sprite_directory = sprite_directory
        self.sprites: Dict[str, any] = {}
        self.projectile_sprites: Dict[str, any] = {}
        self.root_window = root_window

        # Animation state
        self.x_position = 10
        self.direction = 1  # 1 for right, -1 for left
        self.canvas_width = 230
        self.canvas_height = 60
        self.sprite_width = 48
        self.sprite_height = 48
        self.margin = 12
        # Projectile state
        self.projectiles: list[dict] = []
        self.projectile_speed = 12
        self.projectile_width = 20

        # Walking animation frames (facing left by default)
        self.walk_frames = [0, 1]
        self.walk_frame_index = 0
        self.current_frame = self.walk_frames[self.walk_frame_index]

        # Registered animation events
        self.events: Dict[str, PetEvent] = {}
        self.active_event: Optional[PetEvent] = None

        # Register default events (attack training and happy celebration)
        self._register_default_events()

        # Random walk state
        self.distance_walked = 0  # Distance walked in current direction
        self.minimum_walk_distance = (
            25  # Minimum pixels to walk before considering direction change
        )
        self.direction_change_probability = (
            0.07  # Chance per frame to change direction (7%)
        )

        # Behavior state
        self.current_mode = "work"  # "work" or "break"
        self.is_active = False

        # Animation thread
        self.animation_thread: Optional[threading.Thread] = None
        self.animation_running = False

        # Pomodoro timer running state (must be set False by default)
        self.is_timer_running = False

        # Callbacks
        self.on_position_update_callback: Optional[
            Callable[[int, int, int, str, list], None]
        ] = None

        # Load sprites
        self.load_sprites()

    def set_callbacks(
        self,
        on_position_update: Optional[Callable[[int, int, int, str, list], None]] = None,
    ):
        """
        Set callback functions for VPet events.

        Args:
            on_position_update: Called when pet position updates
                (x, y, frame, direction_key, projectiles)
        """
        self.on_position_update_callback = on_position_update

    # ------------------------------------------------------------------
    # Event registration helpers

    def register_event(self, event: PetEvent) -> None:
        """Register a new animation event with the engine."""
        self.events[event.name] = event

    def _activate_event(self, name: str) -> None:
        """Start an event by name if it exists."""
        event = self.events.get(name)
        if event is not None:
            event.start(self)
            self.active_event = event

    def _register_default_events(self) -> None:
        """Register built-in events used by the engine."""
        # Happy event may be triggered manually after other events
        happy = HappyEvent()
        # Attack training automatically triggers the happy event when done
        attack = AttackTrainingEvent(on_complete=lambda eng: "happy")
        self.register_event(attack)
        self.register_event(happy)

    def set_sprite_directory(self, sprite_directory: str):
        """
        Set the sprite directory to a new path.

        Args:
            sprite_directory: New path to the sprite directory.
        """
        self.sprite_directory = sprite_directory
        self.sprites.clear()  # Clear all cached sprites before reloading
        self.load_sprites()

    def load_sprites(self) -> bool:
        """
        Load VPet sprites from the sprite directory.

        Returns:
            bool: True if sprites loaded successfully, False otherwise
        """
        sprite_dir = Path(self.sprite_directory)

        # Determine which sprite frames are required by walking and events
        required = set(self.walk_frames)
        required.update(collect_event_frames(self.events))
        self._required_frame_ids = sorted(required)

        if not sprite_dir.exists():
            logger.warning(f"Sprite directory not found: {sprite_dir}")
            self._create_fallback_sprites()
            return False

        try:
            if PIL_AVAILABLE:
                success = self._load_sprites_with_pil()
            else:
                success = self._load_sprites_basic()

            # Load projectile sprite regardless of general sprite success
            self._load_projectile_sprite()
            return success
        except Exception as e:
            logger.error(f"Error loading sprites: {e}")
            self._create_fallback_sprites()
            return False

    def _load_sprites_with_pil(self) -> bool:
        """Load sprites using PIL for better handling and flipping."""
        loaded_count = 0

        # Load all required frames for walking and registered events
        for frame_id in self._required_frame_ids:
            sprite_path = Path(self.sprite_directory) / f"{frame_id}.png"

            if sprite_path.exists():
                try:
                    # Load original sprite
                    pil_image = Image.open(sprite_path)
                    self.sprites[f"frame_{frame_id}"] = pil_image.copy()

                    # Create flipped version for right-facing movement
                    flipped_image = pil_image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    self.sprites[f"frame_{frame_id}_flipped"] = flipped_image

                    loaded_count += 1
                    logger.info(f"Loaded sprite: {sprite_path}")

                except Exception as e:
                    logger.error(f"Failed to load sprite {sprite_path}: {e}")
            else:
                logger.warning(f"Sprite not found: {sprite_path}")

        # Also load projectile sprite
        self._load_projectile_sprite()
        return loaded_count > 0

    def _load_sprites_basic(self) -> bool:
        """Load sprites using basic method without PIL."""
        loaded_count = 0

        # Load all required frames for walking and registered events
        for frame_id in self._required_frame_ids:
            sprite_path = Path(self.sprite_directory) / f"{frame_id}.png"

            if sprite_path.exists():
                try:
                    # Store path for later loading by GUI
                    self.sprites[f"frame_{frame_id}"] = str(sprite_path)

                    # Create flipped version for right-facing movement (handled by GUI)
                    self.sprites[f"frame_{frame_id}_flipped"] = str(sprite_path)

                    loaded_count += 1
                    logger.info(f"Registered sprite: {sprite_path}")

                except Exception as e:
                    logger.error(f"Failed to register sprite {sprite_path}: {e}")
            else:
                logger.warning(f"Sprite not found: {sprite_path}")

        # Also load projectile sprite
        self._load_projectile_sprite()
        return loaded_count > 0

    def _load_projectile_sprite(self) -> None:
        """Load the projectile sprite used for attack projectiles."""
        sprite_path = Path("sprites/attacks/fireball_20x18.png")
        if not sprite_path.exists():
            logger.warning(f"Projectile sprite not found: {sprite_path}")
            return

        try:
            if PIL_AVAILABLE:
                pil_image = Image.open(sprite_path)
                self.projectile_sprites["fireball"] = pil_image.copy()
                self.projectile_sprites["fireball_flipped"] = pil_image.transpose(
                    Image.Transpose.FLIP_LEFT_RIGHT
                )
            else:
                path = str(sprite_path)
                self.projectile_sprites["fireball"] = path
                self.projectile_sprites["fireball_flipped"] = path
            logger.info(f"Loaded projectile sprite: {sprite_path}")
        except Exception as e:
            logger.error(f"Failed to load projectile sprite {sprite_path}: {e}")

    def _create_fallback_sprites(self) -> None:
        """Create fallback sprites when loading fails."""
        # Create placeholder sprite data
        for frame_id in self._required_frame_ids:
            self.sprites[f"frame_{frame_id}"] = None
            self.sprites[f"frame_{frame_id}_flipped"] = None

        logger.info("Using fallback sprites")
        self.projectile_sprites["fireball"] = None
        self.projectile_sprites["fireball_flipped"] = None

    def start_animation(self) -> None:
        """Start the VPet animation."""
        self.animation_running = True
        self.is_active = True

        if self.animation_thread is None or not self.animation_thread.is_alive():
            self.animation_thread = threading.Thread(target=self._animation_loop)
            self.animation_thread.daemon = True
            self.animation_thread.start()

        logger.info("VPet animation started")

    def stop_animation(self) -> None:
        """Stop the VPet animation."""
        self.animation_running = False
        self.is_active = False
        logger.info("VPet animation stopped")

    def set_mode(self, mode: str) -> None:
        """
        Set the VPet behavior mode.

        Args:
            mode: "work" or "break" - affects animation speed and behavior
        """
        self.current_mode = mode

        # --- Reset any ongoing event when switching mode ---
        if self.active_event and self.active_event.active:
            self.active_event.active = False
            self.active_event = None
            logger.info(
                "VPet mode switch: forcibly ending active event, resuming normal behavior"
            )

        logger.info(f"VPet mode set to: {mode}")

    def set_timer_running(self, is_running: bool) -> None:
        """
        Inform the VPet engine if the Pomodoro timer is running (True) or paused/stopped (False).
        This is used to control when attack training (and possibly other behaviors) should be allowed.
        """
        self.is_timer_running = is_running
        logger.info(f"VPet notified: timer running = {is_running}")

    def get_state(self) -> dict:
        """
        Get the current VPet state.

        Returns:
            dict: Current VPet state information
        """
        return {
            "x_position": self.x_position,
            "direction": self.direction,
            "current_frame": self.current_frame,
            "current_mode": self.current_mode,
            "is_active": self.is_active,
            "animation_running": self.animation_running,
            "sprites_loaded": len(self.sprites) > 0,
        }

    def get_current_sprite_key(self) -> str:
        """
        Get the current sprite key based on frame and direction.

        Returns:
            str: Sprite key for current state
        """
        base_key = f"frame_{self.current_frame}"
        # Use flipped sprite if moving right (since default sprite faces left)
        if self.direction == 1:
            return f"{base_key}_flipped"
        return base_key

    def get_sprite(self, sprite_key: str):
        """
        Get sprite data for the given key.

        Args:
            sprite_key: Key identifying the sprite

        Returns:
            Sprite data (PIL Image, file path, or None)
        """
        return self.sprites.get(sprite_key)

    def get_projectile_sprite(self, sprite_key: str):
        """Return projectile sprite data for the given key."""
        return self.projectile_sprites.get(sprite_key)

    def launch_projectile(self) -> None:
        """Spawn a new projectile in front of the pet with 10% overlap."""
        y_pos = self.canvas_height - self.sprite_height // 2
        overlap = self.sprite_width * 0.2  # Calculate 20% overlap

        if self.direction == 1:  # moving right
            start_x = self.x_position + self.sprite_width - overlap
            sprite_key = "fireball_flipped"
        else:
            start_x = self.x_position - self.projectile_width + overlap
            sprite_key = "fireball"

        projectile = {
            "x": start_x,
            "y": y_pos,
            "direction": self.direction,
            "sprite_key": sprite_key,
        }
        self.projectiles.append(projectile)

    def _update_projectiles(self, step: float | None = None) -> None:
        """Move projectiles and remove those leaving the canvas.

        Args:
            step: Distance each projectile travels for this update. If
                ``None``, ``self.projectile_speed`` is used.
        """
        if step is None:
            step = self.projectile_speed
        remaining = []
        for proj in self.projectiles:
            proj["x"] += proj["direction"] * step
            if 0 <= proj["x"] <= self.canvas_width:
                remaining.append(proj)
        self.projectiles = remaining

    def set_canvas_size(self, width: int, height: int) -> None:
        """
        Set the canvas dimensions for movement calculations.

        Args:
            width: Canvas width in pixels
            height: Canvas height in pixels
        """
        self.canvas_width = width
        self.canvas_height = height

        # Recalculate boundaries
        self._ensure_within_boundaries()

    def set_random_walk_parameters(
        self,
        minimum_walk_distance: Optional[int] = None,
        direction_change_probability: Optional[float] = None,
    ) -> None:
        """
        Configure random walk behavior parameters.

        Args:
            minimum_walk_distance: Minimum pixels to walk before considering direction change
            direction_change_probability: Chance per frame to change direction (0.0 to 1.0)
        """
        if minimum_walk_distance is not None and isinstance(minimum_walk_distance, int):
            self.minimum_walk_distance = max(
                10, minimum_walk_distance
            )  # Minimum of 10 pixels

        if direction_change_probability is not None and isinstance(
            direction_change_probability, float
        ):
            # Clamp between 0.001 and 0.1 for reasonable behavior
            self.direction_change_probability = max(
                0.001, min(0.1, direction_change_probability)
            )

        logger.info(
            f"Random walk parameters updated: min_distance={self.minimum_walk_distance}, "
            f"change_prob={self.direction_change_probability}"
        )

    def _animation_loop(self) -> None:
        """Main animation loop running in separate thread with random walk behavior."""
        while self.animation_running:
            # Get animation parameters based on mode
            move_speed, animation_delay = self._get_animation_parameters()

            if self.active_event and self.active_event.active:
                # An event is running – update its animation
                frame, finished = self.active_event.update(self)
                self.current_frame = frame
                if finished:
                    next_event = self.active_event.complete(self)
                    self.active_event = None
                    if next_event:
                        self._activate_event(next_event)
            else:
                # Normal walking behaviour
                old_position = self.x_position
                self.x_position += self.direction * move_speed

                # Update distance walked and possibly change direction
                distance_moved = abs(self.x_position - old_position)
                self.distance_walked += distance_moved
                boundary_hit = self._check_boundaries()
                if boundary_hit:
                    self.distance_walked = 0
                elif self._should_change_direction():
                    self._change_direction_randomly()
                    self.distance_walked = 0

                # Alternate walking frames
                self.walk_frame_index = 1 - self.walk_frame_index
                self.current_frame = self.walk_frames[self.walk_frame_index]

                # Attempt to trigger any event
                for event in self.events.values():
                    if event.should_trigger(self):
                        self.active_event = event
                        event.start(self)
                        break

            # Prepare for rendering and smoother projectile motion
            callback = self.on_position_update_callback
            root = self.root_window
            sprite_key = self.get_current_sprite_key()
            y_position = self.canvas_height // 2  # Center vertically

            # Number of projectile updates within this frame
            projectile_steps = 3
            step_delay = animation_delay / projectile_steps
            step_distance = self.projectile_speed / projectile_steps

            for _ in range(projectile_steps):
                # Update active projectiles in small increments
                self._update_projectiles(step_distance)

                # Runtime type checks to guarantee safe usage
                if (
                    callback is not None
                    and callable(callback)
                    and root is not None
                    and hasattr(root, "after")
                    and callable(getattr(root, "after", None))
                ):
                    projectiles_snapshot = [p.copy() for p in self.projectiles]

                    def _cb(
                        x=self.x_position,
                        y=y_position,
                        frame=self.current_frame,
                        key=sprite_key,
                        projs=projectiles_snapshot,
                        cb=callback,
                    ) -> None:
                        cb(x, y, frame, key, projs)  # type: ignore[operator]

                    root.after(0, _cb)

                time.sleep(step_delay)

    def _get_animation_parameters(self) -> Tuple[int, float]:
        """
        Get animation parameters based on current mode.

        Returns:
            Tuple[int, float]: (move_speed, animation_delay)
        """
        if self.current_mode == "work":
            # Faster movement during work time (pet is training/active)
            return 3, 0.3
        else:
            # Slower movement during break time (pet is relaxing)
            return 1, 0.7

    def _check_boundaries(self) -> bool:
        """Check boundaries and reverse direction if needed.

        Returns:
            bool: True if boundary was hit and direction changed, False otherwise
        """
        # Calculate boundaries based on canvas width and sprite width
        right_boundary = self.canvas_width - self.sprite_width - self.margin
        left_boundary = self.margin

        if self.x_position >= right_boundary:
            self.direction = -1
            self.x_position = right_boundary
            return True
        elif self.x_position <= left_boundary:
            self.direction = 1
            self.x_position = left_boundary
            return True

        return False

    def _should_change_direction(self) -> bool:
        """Determine if direction should change based on random walk logic.

        Returns:
            bool: True if direction should change, False otherwise
        """
        # Only consider changing direction if we've walked the minimum distance
        if self.distance_walked >= self.minimum_walk_distance:
            # Random chance to change direction
            if random.random() < self.direction_change_probability:
                return True
        return False

    def _change_direction_randomly(self) -> None:
        """Change direction randomly."""
        # Reverse current direction
        self.direction = -self.direction
        logger.debug(
            f"Random direction change: now moving {'right' if self.direction == 1 else 'left'}"
        )

    def _ensure_within_boundaries(self) -> None:
        """Ensure current position is within valid boundaries."""
        right_boundary = self.canvas_width - self.sprite_width - self.margin
        left_boundary = self.margin

        if self.x_position > right_boundary:
            self.x_position = right_boundary
        elif self.x_position < left_boundary:
            self.x_position = left_boundary

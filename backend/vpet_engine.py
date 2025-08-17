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
        self.root_window = root_window

        # Animation state
        self.x_position = 10
        self.direction = 1  # 1 for right, -1 for left
        self.current_frame = 0  # Current animation frame (0 or 1 for walking)
        self.canvas_width = 230
        self.canvas_height = 60
        self.sprite_width = 48
        self.margin = 12

        # Happy event state
        self.is_in_happy_event = False
        self.happy_cycles_remaining = 0
        self.happy_frame_counter = 0  # Alternates between 0 (frame 3) and 1 (frame 7)
        self.happy_event_probability = 0.03  # 3% chance per animation frame
        self.happy_animation_delay_counter = 0  # Counter to slow down happy animation
        self.happy_animation_delay_threshold = (
            2  # Number of animation cycles before switching happy frame
        )

        # Attack training (new)
        self.is_attack_training = False
        self.attack_frames_remaining = 0
        self.attack_animation_length = 0
        self.attack_training_probability = (
            0.8  # 10% chance per animation frame (tunable)
        )
        # Attack now alternates between frame 6 and 11
        self.attack_frames = [6, 11]  # 6 = attack 1, 11 = attack 2
        self.attack_frame_counter = 0  # Used to alternate between frames
        self.attack_animation_delay_counter = 0
        self.attack_animation_delay_threshold = 3  # can be used to slow attack anim
        self.attack_just_finished = False  # To signal happy after attack

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
            Callable[[int, int, int, str], None]
        ] = None

        # Load sprites
        self.load_sprites()

    def set_callbacks(
        self, on_position_update: Optional[Callable[[int, int, int, str], None]] = None
    ):
        """
        Set callback functions for VPet events.

        Args:
            on_position_update: Called when pet position updates (x, y, frame, direction_key)
        """
        self.on_position_update_callback = on_position_update

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

        if not sprite_dir.exists():
            logger.warning(f"Sprite directory not found: {sprite_dir}")
            self._create_fallback_sprites()
            return False

        try:
            if PIL_AVAILABLE:
                return self._load_sprites_with_pil()
            else:
                return self._load_sprites_basic()
        except Exception as e:
            logger.error(f"Error loading sprites: {e}")
            self._create_fallback_sprites()
            return False

    def _load_sprites_with_pil(self) -> bool:
        """Load sprites using PIL for better handling and flipping."""
        loaded_count = 0

        # Load walking animation frames (0, 1), happy frames (3, 7), attack frames (6, 11)
        for frame_id in [0, 1, 3, 7, 6, 11]:
            sprite_path = Path(self.sprite_directory) / f"{frame_id}.png"

            if sprite_path.exists():
                try:
                    # Load original sprite
                    pil_image = Image.open(sprite_path)
                    self.sprites[f"frame_{frame_id}"] = pil_image.copy()

                    # Create flipped version for walking, happy, and attack frames
                    if frame_id in [0, 1, 3, 7, 6, 11]:
                        flipped_image = pil_image.transpose(
                            Image.Transpose.FLIP_LEFT_RIGHT
                        )
                        self.sprites[f"frame_{frame_id}_flipped"] = flipped_image

                    loaded_count += 1
                    logger.info(f"Loaded sprite: {sprite_path}")

                except Exception as e:
                    logger.error(f"Failed to load sprite {sprite_path}: {e}")
            else:
                logger.warning(f"Sprite not found: {sprite_path}")

        return loaded_count > 0

    def _load_sprites_basic(self) -> bool:
        """Load sprites using basic method without PIL."""
        loaded_count = 0

        # Load walking animation frames (0, 1), happy animation frames (3, 7), and attack frames (6, 11)
        for frame_id in [0, 1, 3, 7, 6, 11]:
            sprite_path = Path(self.sprite_directory) / f"{frame_id}.png"

            if sprite_path.exists():
                try:
                    # Store path for later loading by GUI
                    self.sprites[f"frame_{frame_id}"] = str(sprite_path)

                    # Create flipped version for walking, happy, and attack frames
                    if frame_id in [0, 1, 3, 7, 6, 11]:
                        self.sprites[f"frame_{frame_id}_flipped"] = str(
                            sprite_path
                        )  # Same file, flipping handled by GUI

                    loaded_count += 1
                    logger.info(f"Registered sprite: {sprite_path}")

                except Exception as e:
                    logger.error(f"Failed to register sprite {sprite_path}: {e}")
            else:
                logger.warning(f"Sprite not found: {sprite_path}")

        return loaded_count > 0

    def _create_fallback_sprites(self) -> None:
        """Create fallback sprites when loading fails."""
        # Create placeholder sprite data
        for frame_id in [0, 1, 3, 7, 6, 11]:
            self.sprites[f"frame_{frame_id}"] = None
            if frame_id in [0, 1, 3, 7, 6, 11]:
                self.sprites[f"frame_{frame_id}_flipped"] = None

        logger.info("Using fallback sprites")

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

        # --- Reset any ongoing happy or attack event when switching mode ---
        if self.is_in_happy_event or self.is_attack_training:
            self.is_in_happy_event = False
            self.happy_cycles_remaining = 0
            self.happy_frame_counter = 0
            self.happy_animation_delay_counter = 0
            self.is_attack_training = False
            self.attack_frames_remaining = 0
            self.attack_frame_counter = 0
            self.attack_animation_delay_counter = 0
            self.attack_just_finished = False
            logger.info("VPet mode switch: forcibly ending happy/attack animation, resuming normal behavior")

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
        # Attack animation in training
        if self.is_attack_training:
            # Alternate between frame 6 and 11 for attack
            attack_frame = self.attack_frames[
                self.attack_frame_counter % len(self.attack_frames)
            ]
            base_key = f"frame_{attack_frame}"
            # Use flipped sprite if moving right, else normal (left-facing)
            if self.direction == 1:
                return f"{base_key}_flipped"
            else:
                return base_key

        # If in happy event, use happy animation frames with direction consideration
        if self.is_in_happy_event:
            if self.happy_frame_counter == 0:
                base_key = "frame_7"  # Happy 1 (switched)
            else:
                base_key = "frame_3"  # Happy 2 (switched)

            # Use flipped sprite if moving right (since default sprite faces left)
            if self.direction == 1:  # Moving right
                return f"{base_key}_flipped"
            else:  # Moving left
                return base_key

        # Normal walking animation
        base_key = f"frame_{self.current_frame}"

        # Use flipped sprite if moving right (since default sprite faces left)
        if self.direction == 1:  # Moving right
            return f"{base_key}_flipped"
        else:  # Moving left
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

            # ---- Attack training logic (only in work mode, timer running, and active) ----
            # Attack training only triggers in work mode and if timer is running
            # (requires MainWindow to call set_timer_running accordingly)
            is_timer_running = getattr(
                self, "is_timer_running", True
            )  # default True for backward compat
            if (
                self.current_mode == "work"
                and self.animation_running
                and is_timer_running
                and not self.is_in_happy_event
            ):
                if self.is_attack_training:
                    self.attack_animation_delay_counter += 1
                    if (
                        self.attack_animation_delay_counter
                        >= self.attack_animation_delay_threshold
                    ):
                        self.attack_frames_remaining -= 1
                        self.attack_animation_delay_counter = 0
                        # Alternate attack frame (cycles between 6 and 11)
                        self.attack_frame_counter = (
                            self.attack_frame_counter + 1
                        ) % len(self.attack_frames)

                    if self.attack_frames_remaining <= 0:
                        self.is_attack_training = False
                        self.attack_just_finished = True
                        self.attack_frame_counter = 0  # Reset for next attack
                        logger.info(
                            "Attack training finished, will trigger happy animation next"
                        )
                elif (
                    random.random() < self.attack_training_probability
                    and not self.attack_just_finished
                ):
                    self.is_attack_training = True
                    self.attack_frames_remaining = random.randint(5, 10)
                    self.attack_animation_delay_counter = 0
                    logger.info(
                        f"Attack training triggered for {self.attack_frames_remaining} frames!"
                    )

            # ---- Happy event after attack training ----
            if self.attack_just_finished:
                self._trigger_happy_event()
                self.attack_just_finished = False

            # Handle happy event logic
            if self.is_in_happy_event:
                # During happy event, pet stands still and alternates happy frames slowly
                self.happy_animation_delay_counter += 1

                # Only switch frames after delay threshold is reached
                if (
                    self.happy_animation_delay_counter
                    >= self.happy_animation_delay_threshold
                ):
                    self.happy_frame_counter = (
                        1 - self.happy_frame_counter
                    )  # Alternate between 0 and 1
                    self.happy_cycles_remaining -= (
                        0.5  # Each frame change is half a cycle
                    )
                    self.happy_animation_delay_counter = 0  # Reset delay counter

                # Check if happy event is finished
                if self.happy_cycles_remaining <= 0:
                    self.is_in_happy_event = False
                    self.happy_frame_counter = 0
                    self.happy_animation_delay_counter = 0  # Reset delay counter
                    logger.info("Happy event finished, resuming normal walking")
            elif self.is_attack_training:
                # During attack, no walking, just show attack frame
                pass
            else:
                # Normal walking behavior
                # Check for random happy event trigger
                if random.random() < self.happy_event_probability:
                    self._trigger_happy_event()
                else:
                    # Move the pet
                    old_position = self.x_position
                    self.x_position += self.direction * move_speed

                    # Update distance walked
                    distance_moved = abs(self.x_position - old_position)
                    self.distance_walked += distance_moved

                    # Check boundaries and handle mandatory direction change
                    boundary_hit = self._check_boundaries()

                    # If boundary was hit, reset distance counter
                    if boundary_hit:
                        self.distance_walked = 0
                    # Otherwise, check for random direction change
                    elif self._should_change_direction():
                        self._change_direction_randomly()
                        self.distance_walked = 0

                    # Alternate walking frames
                    self.current_frame = 1 - self.current_frame

            # Use main thread to trigger position update callback
            callback = self.on_position_update_callback
            root = self.root_window
            # Runtime type checks to guarantee safe usage
            if (
                callback is not None
                and callable(callback)
                and root is not None
                and hasattr(root, "after")
                and callable(getattr(root, "after", None))
            ):
                sprite_key = self.get_current_sprite_key()
                y_position = self.canvas_height // 2  # Center vertically
                root.after(  # type: ignore[attr-defined]
                    0,
                    lambda: callback(  # type: ignore[operator]
                        self.x_position, y_position, self.current_frame, sprite_key
                    ),
                )

            # Wait based on animation speed
            time.sleep(animation_delay)

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

    def _trigger_happy_event(self) -> None:
        """Trigger a happy animation event."""
        # Random number of cycles between 2 and 4
        self.happy_cycles_remaining = random.randint(1, 3)
        self.is_in_happy_event = True
        self.happy_frame_counter = 0  # Start with happy frame 1 (frame 3)
        logger.info(
            f"Happy event triggered! Will play {self.happy_cycles_remaining} cycles"
        )

    def _ensure_within_boundaries(self) -> None:
        """Ensure current position is within valid boundaries."""
        right_boundary = self.canvas_width - self.sprite_width - self.margin
        left_boundary = self.margin

        if self.x_position > right_boundary:
            self.x_position = right_boundary
        elif self.x_position < left_boundary:
            self.x_position = left_boundary

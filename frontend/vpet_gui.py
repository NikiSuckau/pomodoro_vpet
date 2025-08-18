"""
VPet Frontend GUI

This module contains the GUI components for the virtual pet display,
separated from business logic for better maintainability.
"""

import tkinter as tk
from typing import Callable, Optional

# Enhanced imports with fallbacks
try:
    from PIL import Image, ImageTk

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class VPetGUI:
    """
    GUI component for VPet display and rendering.

    This class is responsible for:
    - Canvas creation and management
    - Sprite rendering and animation display
    - Visual effects and fallback graphics
    """

    def __init__(
        self, parent_frame: tk.Frame, canvas_width: int = 230, canvas_height: int = 60
    ):
        """
        Initialize the VPet GUI component.

        Args:
            parent_frame: Parent tkinter frame to contain this component
            canvas_width: Width of the VPet canvas
            canvas_height: Height of the VPet canvas
        """
        self.parent_frame = parent_frame
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

        # GUI elements
        self.vpet_frame: Optional[tk.Frame] = None
        self.vpet_canvas: Optional[tk.Canvas] = None

        # Sprite cache for tkinter PhotoImage objects
        self.tk_sprites = {}

        # Current display state
        self.current_mode = "work"

        self.create_widgets()

    def create_widgets(self) -> None:
        """Create the GUI elements for the VPet display."""
        # VPet display area - Keep this colored as requested
        self.vpet_frame = tk.Frame(
            self.parent_frame, bg="#2c3e50", relief="sunken", bd=2
        )
        self.vpet_frame.pack(pady=(10, 0), fill="x")

        # VPet canvas for animation - Keep colored
        self.vpet_canvas = tk.Canvas(
            self.vpet_frame,
            width=self.canvas_width,
            height=self.canvas_height,
            bg="#34495e",
            highlightthickness=0,
        )
        self.vpet_canvas.pack(padx=5, pady=5)

    def load_sprite_for_display(self, sprite_data, sprite_key: str):
        """
        Load sprite data into a format suitable for tkinter display.

        Args:
            sprite_data: Sprite data (PIL Image, file path, or None)
            sprite_key: Key to cache the sprite under

        Returns:
            PhotoImage object or None
        """
        if sprite_data is None:
            return None

        # Check if already cached
        if sprite_key in self.tk_sprites:
            return self.tk_sprites[sprite_key]

        try:
            if PIL_AVAILABLE and hasattr(sprite_data, "save"):
                # PIL Image object
                tk_image = ImageTk.PhotoImage(sprite_data)
                self.tk_sprites[sprite_key] = tk_image
                return tk_image
            elif isinstance(sprite_data, str):
                # File path
                tk_image = tk.PhotoImage(file=sprite_data)
                self.tk_sprites[sprite_key] = tk_image
                return tk_image
            else:
                # Unknown format
                return None
        except Exception as e:
            print(f"Error loading sprite {sprite_key}: {e}")
            return None

    def update_vpet_display(
        self,
        x_position: int,
        y_position: int,
        sprite_data,
        sprite_key: str,
        current_mode: str,
        projectiles: Optional[list] = None,
    ) -> None:
        """
        Update the VPet display with new position and sprite.

        Args:
            x_position: X coordinate for the sprite
            y_position: Y coordinate for the sprite
            sprite_data: Sprite data to display
            sprite_key: Key identifying the sprite
            current_mode: Current timer mode ("work" or "break")
            projectiles: Optional list of projectile tuples
        """
        if not self.vpet_canvas:
            return

        self.current_mode = current_mode

        # Clear canvas
        self.vpet_canvas.delete("all")

        # Try to load and display sprite
        tk_sprite = self.load_sprite_for_display(sprite_data, sprite_key)

        if tk_sprite:
            # Display the sprite
            self.vpet_canvas.create_image(
                x_position, y_position, image=tk_sprite, anchor="w"
            )
        else:
            # Fallback: draw a simple shape
            self._draw_fallback_vpet(x_position, y_position)

        # Draw projectiles if any
        if projectiles:
            for px, py, psprite_data, psprite_key in projectiles:
                tk_proj = self.load_sprite_for_display(psprite_data, psprite_key)
                if tk_proj:
                    self.vpet_canvas.create_image(px, py, image=tk_proj, anchor="w")

    def _draw_fallback_vpet(self, x_position: int, y_position: int) -> None:
        """
        Draw a simple fallback VPet when sprites are not available.

        Args:
            x_position: X coordinate for the fallback shape
            y_position: Y coordinate for the fallback shape
        """
        if not self.vpet_canvas:
            return

        # Color based on mode
        rect_color = "#e74c3c" if self.current_mode == "work" else "#27ae60"

        # Draw main body (rectangle)
        body_width = 20
        body_height = 20
        self.vpet_canvas.create_rectangle(
            x_position,
            y_position - body_height // 2,
            x_position + body_width,
            y_position + body_height // 2,
            fill=rect_color,
            outline="white",
            width=2,
        )

        # Draw direction indicator (triangle)
        triangle_size = 5
        if (
            hasattr(self, "_last_direction") and self._last_direction == 1
        ):  # Moving right
            points = [
                x_position + body_width - triangle_size,
                y_position - triangle_size,
                x_position + body_width - triangle_size,
                y_position + triangle_size,
                x_position + body_width,
                y_position,
            ]
        else:  # Moving left or unknown
            points = [
                x_position + triangle_size,
                y_position - triangle_size,
                x_position + triangle_size,
                y_position + triangle_size,
                x_position,
                y_position,
            ]

        self.vpet_canvas.create_polygon(points, fill="white", outline="white")

        # Draw eyes
        eye_size = 2
        eye_y = y_position - 5
        self.vpet_canvas.create_oval(
            x_position + 5 - eye_size,
            eye_y - eye_size,
            x_position + 5 + eye_size,
            eye_y + eye_size,
            fill="white",
            outline="white",
        )
        self.vpet_canvas.create_oval(
            x_position + 15 - eye_size,
            eye_y - eye_size,
            x_position + 15 + eye_size,
            eye_y + eye_size,
            fill="white",
            outline="white",
        )

    def set_direction_hint(self, direction: int) -> None:
        """
        Set direction hint for fallback drawing.

        Args:
            direction: Direction indicator (1 for right, -1 for left)
        """
        self._last_direction = direction

    def clear_display(self) -> None:
        """Clear the VPet display."""
        if self.vpet_canvas:
            self.vpet_canvas.delete("all")

    def set_mode_colors(self, mode: str) -> None:
        """
        Update colors based on timer mode.

        Args:
            mode: Current timer mode ("work" or "break")
        """
        self.current_mode = mode

        # You could add mode-specific visual effects here
        # For example, changing canvas background color slightly
        if self.vpet_canvas:
            if mode == "work":
                # Slightly more intense background during work
                self.vpet_canvas.config(bg="#2c3e50")
            else:
                # Calmer background during break
                self.vpet_canvas.config(bg="#34495e")

    def clear_sprite_cache(self) -> None:
        """
        Clear the cached PhotoImage sprites to force reload from new sprite data.
        """
        self.tk_sprites.clear()

    def get_canvas_size(self) -> tuple:
        """
        Get the canvas dimensions.

        Returns:
            tuple: (width, height) of the canvas
        """
        return (self.canvas_width, self.canvas_height)

    def resize_canvas(self, width: int, height: int) -> None:
        """
        Resize the VPet canvas.

        Args:
            width: New canvas width
            height: New canvas height
        """
        self.canvas_width = width
        self.canvas_height = height

        if self.vpet_canvas:
            self.vpet_canvas.config(width=width, height=height)

    def get_state(self) -> dict:
        """
        Get the current GUI state.

        Returns:
            dict: Current VPet GUI state information
        """
        return {
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "current_mode": self.current_mode,
            "sprites_cached": len(self.tk_sprites),
            "canvas_created": self.vpet_canvas is not None,
        }

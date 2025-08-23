"""
Main Window Controller

This module contains the main window setup and coordinates
between backend engines and frontend GUI components.
"""

import os
import tkinter as tk
from typing import Optional

from backend.digimon_importer import DigimonImporter
# Backend imports
from backend.pomodoro_engine import PomodoroEngine
from backend.vpet_engine import VPetEngine
# Frontend imports
from frontend.pomodoro_gui import PomodoroGUI
from frontend.vpet_gui import VPetGUI

# Enhanced imports with fallbacks
try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

try:
    from playsound import playsound

    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

try:
    from plyer import notification

    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

try:
    import colorama
    from colorama import Fore, Style

    colorama.init()
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False


class MainWindow:
    """
    Main application window controller.

    This class coordinates between backend engines and frontend GUI components,
    handling the overall application lifecycle and inter-component communication.
    """

    def __init__(self):
        """Initialize the main application window and components."""
        # Create main window
        self.root = tk.Tk()
        self.transparent_color = "#010203"

        # Initialize backend engines
        self.vpet_engine = VPetEngine(root_window=self.root)

        # Initialize Digimon importer
        self.digimon_importer = DigimonImporter()

        # Extract vpet name from sprite directory
        vpet_name = self._extract_vpet_name_from_engine()

        # Initialize Pomodoro engine with vpet name
        self.pomodoro_engine = PomodoroEngine(vpet_name=vpet_name)

        # GUI components (will be initialized in setup)
        self.pomodoro_gui: Optional[PomodoroGUI] = None
        self.vpet_gui: Optional[VPetGUI] = None
        self.events_window: Optional[tk.Toplevel] = None

        # Setup everything
        self.setup_window()
        self.create_gui_components()
        self.setup_callbacks()
        self.start_engines()

        logger.info("Main application initialized")

    def _extract_vpet_name_from_engine(self) -> str:
        """
        Extract the vpet name from the VPet engine's sprite directory.

        Returns:
            str: The vpet name extracted from the sprite directory path
        """
        try:
            # Extract name from sprite directory path like "sprites/Agumon_penc"
            sprite_dir = self.vpet_engine.sprite_directory
            # Split by '/' and get the last part, then remove '_penc' suffix
            dir_name = sprite_dir.split("/")[-1]
            if dir_name.endswith("_penc"):
                vpet_name = dir_name[:-5]  # Remove '_penc' suffix
            else:
                vpet_name = dir_name

            logger.info(f"Extracted vpet name: {vpet_name}")
            return vpet_name
        except Exception as e:
            logger.warning(f"Failed to extract vpet name: {e}, using default 'Agumon'")
            return "Agumon"

    def setup_window(self) -> None:
        """Configure the main window properties."""
        self.root.title("Pomodoro Timer")
        self.base_width = 250
        self.base_height = 300
        self.root.geometry(f"{self.base_width}x{self.base_height}")  # Increased height for vpet area
        self.root.resizable(False, False)

        # Make window always stay on top
        self.root.attributes("-topmost", True)

        # Remove window decorations for minimalist look
        self.root.overrideredirect(True)

        # Position window in top-right corner
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"+{screen_width - 270}+20")

        # Set background color
        self.root.configure(bg=self.transparent_color)

        # Set up transparency
        self._setup_transparency()

    def _setup_transparency(self) -> None:
        """Set up window transparency."""
        try:
            # Try Windows-specific transparency
            self.root.wm_attributes("-transparentcolor", self.transparent_color)
        except tk.TclError:
            try:
                # Fallback for Linux/Unix systems
                self.root.attributes("-alpha", 0.9)
            except tk.TclError:
                # No transparency support
                logger.info("Transparency not supported on this system")

    def create_gui_components(self) -> None:
        """Create and layout the GUI components."""
        # Main frame with transparent background
        main_frame = tk.Frame(self.root, bg=self.transparent_color)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Top frame for Pomodoro GUI (timer, controls)
        top_frame = tk.Frame(main_frame, bg=self.transparent_color)
        top_frame.pack(side="top", fill="x", expand=False)
        self.pomodoro_gui = PomodoroGUI(top_frame, self.transparent_color)

        # Bottom frame for VPet GUI (pet display area)
        bottom_frame = tk.Frame(main_frame, bg=self.transparent_color)
        bottom_frame.pack(side="bottom", fill="x", expand=False)
        self.vpet_gui = VPetGUI(bottom_frame)
        self.vpet_gui.set_scale_callback(self._on_vpet_scale_change)

        logger.info("GUI components created")

    def setup_callbacks(self) -> None:
        """Set up callbacks between components."""
        # Pomodoro engine callbacks
        self.pomodoro_engine.set_callbacks(
            on_tick=self._on_timer_tick,
            on_mode_change=self._on_mode_change,
            on_session_complete=self._on_session_complete,
        )

        # Pomodoro GUI callbacks
        if self.pomodoro_gui:
            self.pomodoro_gui.set_callbacks(
                on_start_pause=self._on_start_pause_clicked,
                on_reset=self._on_reset_clicked,
                on_exit=self._on_exit_clicked,
                on_events=self._open_events_window,
            )

            # Set Digimon-related callbacks
            self.pomodoro_gui.set_digimon_callbacks(
                on_import=self._on_import_clicked,
                on_digimon_change=self._on_digimon_changed,
            )

            # Initialize Digimon list
            self._update_digimon_list()

        # VPet engine callbacks
        self.vpet_engine.set_callbacks(on_position_update=self._on_vpet_position_update)

        logger.info("Callbacks configured")

    def start_engines(self) -> None:
        """Start the backend engines."""
        # Start VPet animation
        self.vpet_engine.start_animation()

        # Update initial display
        self._update_all_displays()

        logger.info("Engines started")

    def _on_timer_tick(self, time_remaining: int) -> None:
        """
        Handle timer tick from Pomodoro engine.

        Args:
            time_remaining: Seconds remaining in current session
        """
        if self.pomodoro_gui:
            time_text = self.pomodoro_engine.format_time(time_remaining)
            self.pomodoro_gui.update_time_display(time_text)

    def _on_mode_change(self, old_mode: str, new_mode: str) -> None:
        """
        Handle mode change from Pomodoro engine.

        Args:
            old_mode: Previous mode ("work" or "break")
            new_mode: New mode ("work" or "break")
        """
        # Update Pomodoro GUI
        if self.pomodoro_gui:
            self.pomodoro_gui.update_mode_display(new_mode)
            self.pomodoro_gui.update_button_state(False, False)

        # Update VPet engine and GUI
        self.vpet_engine.set_mode(new_mode)
        if self.vpet_gui:
            self.vpet_gui.set_mode_colors(new_mode)

        logger.info(f"Mode changed: {old_mode} -> {new_mode}")

    def _on_session_complete(self, completed_mode: str) -> None:
        """
        Handle session completion from Pomodoro engine.

        Args:
            completed_mode: The mode that just completed ("work" or "break")
        """
        # Flash the display for attention
        if self.pomodoro_gui:
            self.pomodoro_gui.flash_display()

        # Send notifications
        self._send_notifications(completed_mode)

        logger.info(f"Session completed: {completed_mode}")

    def _on_vpet_scale_change(self, scale: float) -> None:
        """Handle scale changes from the VPet GUI."""
        self.vpet_engine.set_scale(scale)
        canvas_width, canvas_height = self.vpet_gui.get_canvas_size()
        self.vpet_engine.set_canvas_size(canvas_width, canvas_height)

        # Adjust main window size to accommodate new canvas dimensions
        new_width = self.base_width + (canvas_width - self.vpet_gui.base_canvas_width)
        new_height = self.base_height + (canvas_height - self.vpet_gui.base_canvas_height)
        self.root.geometry(f"{new_width}x{new_height}")

        # Refresh displays with new sizing
        self._update_all_displays()

    def _on_vpet_position_update(
        self, x: int, y: int, frame: int, sprite_key: str, projectiles: list
    ) -> None:
        """
        Handle VPet position update.

        Args:
            x: X position
            y: Y position
            frame: Animation frame
            sprite_key: Key for the sprite to display
            projectiles: List of active projectile dictionaries
        """
        if self.vpet_gui:
            # Get sprite data from VPet engine
            sprite_data = self.vpet_engine.get_sprite(sprite_key)
            current_mode = self.vpet_engine.current_mode

            projectile_sprites = []
            for proj in projectiles:
                psprite_data = self.vpet_engine.get_projectile_sprite(
                    proj.get("sprite_key", "")
                )
                projectile_sprites.append(
                    (
                        proj.get("x", 0),
                        proj.get("y", 0),
                        psprite_data,
                        proj.get("sprite_key", ""),
                    )
                )

            # Update VPet display
            self.vpet_gui.update_vpet_display(
                x, y, sprite_data, sprite_key, current_mode, projectile_sprites
            )

            # Set direction hint for fallback rendering
            direction = self.vpet_engine.direction
            self.vpet_gui.set_direction_hint(direction)

    def _on_start_pause_clicked(self) -> None:
        """Handle start/pause button click from Pomodoro GUI."""
        engine_state = self.pomodoro_engine.get_state()

        if not engine_state["is_running"] and not engine_state["is_paused"]:
            # Start timer
            success = self.pomodoro_engine.start()
            if success and self.pomodoro_gui:
                self.pomodoro_gui.update_button_state(True, False)
            # Inform VPet engine timer is running
            self.vpet_engine.set_timer_running(True)
        elif engine_state["is_running"]:
            # Pause timer
            success = self.pomodoro_engine.pause()
            if success and self.pomodoro_gui:
                self.pomodoro_gui.update_button_state(False, True)
            # Inform VPet engine timer is paused
            self.vpet_engine.set_timer_running(False)
        elif engine_state["is_paused"]:
            # Resume timer
            success = self.pomodoro_engine.resume()
            if success and self.pomodoro_gui:
                self.pomodoro_gui.update_button_state(True, False)
            # Inform VPet engine timer is running again
            self.vpet_engine.set_timer_running(True)

    def _on_reset_clicked(self) -> None:
        """Handle reset button click from Pomodoro GUI."""
        self.pomodoro_engine.reset()

        if self.pomodoro_gui:
            self.pomodoro_gui.update_button_state(False, False)
            self.pomodoro_gui.update_mode_display("work")

        # Reset VPet mode
        self.vpet_engine.set_mode("work")
        # Inform VPet engine timer is not running
        self.vpet_engine.set_timer_running(False)
        if self.vpet_gui:
            self.vpet_gui.set_mode_colors("work")

    def _on_exit_clicked(self) -> None:
        """Handle exit button click from Pomodoro GUI."""
        logger.info("Exit button clicked - shutting down application")
        self.cleanup()
        self.root.quit()
        self.root.destroy()

    def _on_import_clicked(self) -> None:
        """Handle import button click from Pomodoro GUI."""
        from tkinter import Toplevel, filedialog, messagebox

        # Create a hidden dummy window just below the main window to act as parent
        self.root.update_idletasks()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        dummy = Toplevel(self.root)
        dummy.withdraw()  # Hide the dummy window
        # Place dummy window just below the main window
        dialog_w = 600  # Typical dialog width
        x = root_x + (root_w - dialog_w) // 2
        y = root_y + root_h + 10
        if x < 0:
            x = 0
        dummy.geometry(f"{dialog_w}x100+{x}+{y}")
        dummy.update_idletasks()
        # Open file dialog for zip files, using dummy as parent
        zip_file = filedialog.askopenfilename(
            title="Select Digimon Sprite Pack",
            filetypes=[("Zip files", "*.zip"), ("All files", "*.*")],
            parent=dummy,
        )
        dummy.destroy()

        if not zip_file:
            return  # User cancelled

        # Import the Digimon
        success, message = self.digimon_importer.import_digimon(zip_file)

        if success:
            messagebox.showinfo("Import Successful", message, parent=self.root)
            # Update the Digimon list in GUI
            self._update_digimon_list()
            logger.info(f"Successfully imported Digimon from {zip_file}")
        else:
            messagebox.showerror("Import Failed", message, parent=self.root)
            logger.error(f"Failed to import Digimon from {zip_file}: {message}")

    def _on_digimon_changed(self, selected_digimon: str) -> None:
        """
        Handle Digimon selection change from Pomodoro GUI.

        Args:
            selected_digimon: Name of the selected Digimon
        """
        # Get sprite path for the selected Digimon
        sprite_path = self.digimon_importer.get_digimon_sprite_path(selected_digimon)

        if sprite_path:
            # Update VPet engine with new sprite directory
            self.vpet_engine.set_sprite_directory(sprite_path)

            # Clear GUI sprite cache to ensure new Digimon is displayed
            if self.vpet_gui:
                self.vpet_gui.clear_sprite_cache()

            # Update Pomodoro engine with new vpet name
            self.pomodoro_engine.set_vpet_name(selected_digimon)

            logger.info(f"Switched to Digimon: {selected_digimon}")
        else:
            logger.warning(
                f"Could not find sprite path for Digimon: {selected_digimon}"
            )

    def _update_digimon_list(self) -> None:
        """Update the Digimon selector dropdown with available Digimon."""
        available_digimon = self.digimon_importer.get_available_digimon()
        digimon_names = [digimon["name"] for digimon in available_digimon]

        if self.pomodoro_gui:
            self.pomodoro_gui.update_digimon_list(digimon_names)

        logger.info(f"Updated Digimon list: {digimon_names}")

    def _open_events_window(self) -> None:
        """Open a window listing all available VPet events."""
        if self.events_window and self.events_window.winfo_exists():
            self.events_window.destroy()
        self.events_window = tk.Toplevel(self.root)
        self.events_window.title("Events")
        self.events_window.protocol("WM_DELETE_WINDOW", self._on_events_window_closed)
        self.events_window.lift()
        self.events_window.attributes("-topmost", True)

        try:
            # Find root window
            # root = self.parent_frame.winfo_toplevel()
            root = self.root
            root.update_idletasks()
            root_x = root.winfo_rootx()
            root_y = root.winfo_rooty()
            root_w = root.winfo_width()
            root_h = root.winfo_height()
            # Place config window to the left of the main window, vertically centered
            config_w = 200
            config_h = 80
            x = root_x - config_w - 10
            y = root_y + (root_h - config_h) // 2
            if x < 0:
                x = 0  # Prevent the config window from being off-screen to the left
            self.events_window.geometry(f"{config_w}x{config_h}+{x}+{y}")
        except Exception:
            pass

        frame = tk.Frame(self.events_window, bg=self.transparent_color)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        for name in sorted(self.vpet_engine.events.keys()):
            btn = tk.Button(
                frame,
                text=name,
                command=lambda n=name: self._queue_event(n),
                font=("Arial", 8),
                bg="#95a5a6",
                fg="#2c3e50",
                relief="flat",
                activebackground="#7f8c8d",
                activeforeground="#2c3e50",
            )
            btn.pack(fill="x", pady=2)

    def _queue_event(self, name: str) -> None:
        """Queue an event in the VPet engine."""
        logger.debug(f"Event '{name}' queued")
        self.vpet_engine.queue_event(name)

    def _on_events_window_closed(self) -> None:
        """Handle closing of the events window."""
        if self.events_window:
            self.events_window.destroy()
            self.events_window = None

    def _update_all_displays(self) -> None:
        """Update all display components with current state."""
        # Update Pomodoro display
        if self.pomodoro_gui:
            engine_state = self.pomodoro_engine.get_state()
            time_text = self.pomodoro_engine.format_time()
            self.pomodoro_gui.update_time_display(time_text)
            self.pomodoro_gui.update_mode_display(engine_state["current_mode"])
            self.pomodoro_gui.update_button_state(
                engine_state["is_running"], engine_state["is_paused"]
            )

        # Update VPet canvas size
        if self.vpet_gui:
            canvas_width, canvas_height = self.vpet_gui.get_canvas_size()
            self.vpet_engine.set_canvas_size(canvas_width, canvas_height)

    def _send_notifications(self, completed_mode: str) -> None:
        """
        Send notifications when a session completes.

        Args:
            completed_mode: The mode that just completed
        """
        if completed_mode == "work":
            title = "Work Session Complete!"
            message = "Time for a 5-minute break! Your Agumon is relaxing."
        else:
            title = "Break Time Over!"
            message = "Time to get back to work! Your Agumon is ready to train."

        # Desktop notification
        if NOTIFICATIONS_AVAILABLE:
            try:
                notification.notify(title=title, message=message, timeout=10)
            except Exception as e:
                logger.info(f"Desktop notification failed: {e}")

        # Sound notification
        if SOUND_AVAILABLE:
            try:
                sound_file = (
                    "assets/notification.wav"
                    if completed_mode == "work"
                    else "assets/break_end.wav"
                )
                if os.path.exists(sound_file):
                    playsound(sound_file, block=False)
                else:
                    print("\a")  # System bell sound
            except Exception as e:
                logger.info(f"Sound notification failed: {e}")
                print("\a")  # Fallback to system bell

        # Terminal output with colors if available
        if COLORS_AVAILABLE:
            if completed_mode == "work":
                print(f"{Fore.GREEN}✓ Work session completed!{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⏰ Break time over!{Style.RESET_ALL}")
        else:
            print(f"✓ {completed_mode.title()} session completed!")

    def run(self) -> None:
        """Start the application main loop."""
        logger.info("Starting application")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
            raise
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Clean up resources before exit."""
        # Stop any active work session logging
        if self.pomodoro_engine and hasattr(self.pomodoro_engine, "time_logger"):
            self.pomodoro_engine.time_logger.cleanup_on_exit()

        # Stop VPet animation
        self.vpet_engine.stop_animation()

        logger.info("Application cleanup completed")

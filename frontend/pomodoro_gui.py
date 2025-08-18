"""
Pomodoro Timer Frontend GUI

This module contains the GUI components for the Pomodoro timer,
separated from business logic for better maintainability.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, Callable


class PomodoroGUI:
    """
    GUI component for Pomodoro timer display and controls.
    
    This class is responsible for:
    - Timer display (time remaining, mode)
    - Control buttons (start/pause, reset)
    - Visual feedback and styling
    """
    
    def __init__(self, parent_frame: tk.Frame, transparent_color: str = "#010203"):
        """
        Initialize the Pomodoro GUI component.
        
        Args:
            parent_frame: Parent tkinter frame to contain this component
            transparent_color: Color to use for transparency
        """
        self.parent_frame = parent_frame
        self.transparent_color = transparent_color
        
        # Callbacks
        self.on_start_pause_callback: Optional[Callable[[], None]] = None
        self.on_reset_callback: Optional[Callable[[], None]] = None
        self.on_exit_callback: Optional[Callable[[], None]] = None
        self.on_import_callback: Optional[Callable[[], None]] = None
        self.on_digimon_change_callback: Optional[Callable[[str], None]] = None
        
        # GUI elements
        self.mode_label: Optional[tk.Label] = None
        self.time_label: Optional[tk.Label] = None
        self.start_pause_btn: Optional[tk.Button] = None
        self.reset_btn: Optional[tk.Button] = None
        self.exit_btn: Optional[tk.Button] = None
        self.config_btn: Optional[tk.Button] = None

        # Digimon related widgets
        self.digimon_var = tk.StringVar(value="Agumon")
        self.digimon_selector: Optional[tk.OptionMenu] = None
        self.import_btn: Optional[tk.Button] = None
        self.config_window: Optional[tk.Toplevel] = None
        self._digimon_list: list = []
        
        # Current state for display
        self.current_mode = "work"
        self.is_running = False
        self.is_paused = False
        
        self.create_widgets()
    
    def set_callbacks(self, 
                      on_start_pause: Optional[Callable[[], None]] = None,
                      on_reset: Optional[Callable[[], None]] = None,
                      on_exit: Optional[Callable[[], None]] = None):
        """
        Set callback functions for user interactions.
        
        Args:
            on_start_pause: Called when start/pause button is clicked
            on_reset: Called when reset button is clicked
            on_exit: Called when exit button is clicked
        """
        self.on_start_pause_callback = on_start_pause
        self.on_reset_callback = on_reset
        self.on_exit_callback = on_exit
    
    def create_widgets(self) -> None:
        """Create the GUI elements for the Pomodoro timer."""
        # Mode label with transparent background and white text
        self.mode_label = tk.Label(
            self.parent_frame,
            text="WORK TIME",
            font=("Arial", 10, "bold"),
            fg="#ffffff",
            bg=self.transparent_color,
        )
        self.mode_label.pack()
        
        # Timer display with transparent background and white text
        self.time_label = tk.Label(
            self.parent_frame,
            text="25:00",
            font=("Arial", 20, "bold"),
            fg="#ffffff",
            bg=self.transparent_color,
        )
        self.time_label.pack(pady=(5, 10))
        
        # Control buttons frame with transparent background
        button_frame = tk.Frame(self.parent_frame, bg=self.transparent_color)
        button_frame.pack()
        
        # Start/Pause button
        self.start_pause_btn = tk.Button(
            button_frame,
            text="Start",
            command=self._on_start_pause_clicked,
            font=("Arial", 9),
            bg="#4ecdc4",
            fg="#2c3e50",
            relief="flat",
            width=8,
            activebackground="#45b7aa",
            activeforeground="#2c3e50",
        )
        self.start_pause_btn.pack(side="left", padx=(0, 5))
        
        # Reset button
        self.reset_btn = tk.Button(
            button_frame,
            text="Reset",
            command=self._on_reset_clicked,
            font=("Arial", 9),
            bg="#ff7675",
            fg="#2c3e50",
            relief="flat",
            width=8,
            activebackground="#fd6c6c",
            activeforeground="#2c3e50",
        )
        self.reset_btn.pack(side="left", padx=(0, 5))
        
        # Exit button
        self.exit_btn = tk.Button(
            button_frame,
            text="Exit",
            command=self._on_exit_clicked,
            font=("Arial", 9),
            bg="#95a5a6",
            fg="#2c3e50",
            relief="flat",
            width=8,
            activebackground="#7f8c8d",
            activeforeground="#2c3e50",
        )
        self.exit_btn.pack(side="left")

        # Configuration button to access Digimon settings
        self.config_btn = tk.Button(
            button_frame,
            text="Config",
            command=self._open_config_window,
            font=("Arial", 9),
            bg="#3498db",
            fg="#ffffff",
            relief="flat",
            width=8,
            activebackground="#2980b9",
            activeforeground="#ffffff",
        )
        self.config_btn.pack(side="left", padx=(5, 0))

    def _open_config_window(self) -> None:
        """Open a configuration window for Digimon settings."""
        if self.config_window and self.config_window.winfo_exists():
            self.config_window.lift()
            return

        self.config_window = tk.Toplevel(self.parent_frame)
        self.config_window.title("Configuration")
        self.config_window.protocol("WM_DELETE_WINDOW", self._on_config_closed)

        digimon_frame = tk.Frame(self.config_window, bg=self.transparent_color)
        digimon_frame.pack(padx=10, pady=10)

        self.digimon_selector = tk.OptionMenu(
            digimon_frame,
            self.digimon_var,
            self.digimon_var.get(),
            command=self._on_digimon_changed,
        )
        self.digimon_selector.config(
            font=("Arial", 8),
            bg="#34495e",
            fg="#ffffff",
            activebackground="#2c3e50",
            activeforeground="#ffffff",
            relief="flat",
            width=10,
        )
        self.digimon_selector["menu"].config(
            bg="#34495e",
            fg="#ffffff",
            activebackground="#2c3e50",
            activeforeground="#ffffff",
        )
        self.digimon_selector.pack(side="left", padx=(0, 5))

        self.import_btn = tk.Button(
            digimon_frame,
            text="Import",
            command=self._on_import_clicked,
            font=("Arial", 8),
            bg="#9b59b6",
            fg="#ffffff",
            relief="flat",
            width=8,
            activebackground="#8e44ad",
            activeforeground="#ffffff",
        )
        self.import_btn.pack(side="left")

        # Populate selector with available Digimon
        self.update_digimon_list(self._digimon_list)

    def _on_config_closed(self) -> None:
        """Handle closing of the configuration window."""
        if self.config_window:
            self.config_window.destroy()
            self.config_window = None
        self.digimon_selector = None
        self.import_btn = None
    
    def update_time_display(self, time_text: str) -> None:
        """
        Update the time display.
        
        Args:
            time_text: Formatted time string to display
        """
        if self.time_label:
            self.time_label.config(text=time_text)
    
    def update_mode_display(self, mode: str) -> None:
        """
        Update the mode display.
        
        Args:
            mode: Current mode ("work" or "break")
        """
        self.current_mode = mode
        
        if self.mode_label:
            if mode == "work":
                self.mode_label.config(text="WORK TIME", fg="#ffffff")
            else:
                self.mode_label.config(text="BREAK TIME", fg="#ffffff")
    
    def update_button_state(self, is_running: bool, is_paused: bool) -> None:
        """
        Update button appearance based on timer state.
        
        Args:
            is_running: Whether timer is currently running
            is_paused: Whether timer is currently paused
        """
        self.is_running = is_running
        self.is_paused = is_paused
        
        if self.start_pause_btn:
            if not is_running and not is_paused:
                # Timer is stopped
                self.start_pause_btn.config(text="Start", bg="#4ecdc4")
            elif is_running:
                # Timer is running
                self.start_pause_btn.config(text="Pause", bg="#f39c12")
            elif is_paused:
                # Timer is paused
                self.start_pause_btn.config(text="Resume", bg="#27ae60")
    
    def flash_display(self, duration: int = 500) -> None:
        """
        Flash the time display to get user's attention.
        
        Args:
            duration: Flash duration in milliseconds
        """
        if self.time_label:
            original_color = self.time_label.cget("fg")
            self.time_label.config(fg="#f1c40f")
            
            # Restore original color after duration
            self.parent_frame.after(
                duration, 
                lambda: self.time_label.config(fg=original_color) if self.time_label else None
            )
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the GUI controls.
        
        Args:
            enabled: Whether controls should be enabled
        """
        state = "normal" if enabled else "disabled"
        
        if self.start_pause_btn:
            self.start_pause_btn.config(state=state)
        if self.reset_btn:
            self.reset_btn.config(state=state)
    
    def get_state(self) -> dict:
        """
        Get the current GUI state.
        
        Returns:
            dict: Current GUI state information
        """
        return {
            "current_mode": self.current_mode,
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "time_display": self.time_label.cget("text") if self.time_label else "",
            "mode_display": self.mode_label.cget("text") if self.mode_label else ""
        }
    
    def _on_start_pause_clicked(self) -> None:
        """Handle start/pause button click."""
        if self.on_start_pause_callback:
            self.on_start_pause_callback()
    
    def _on_reset_clicked(self) -> None:
        """Handle reset button click."""
        if self.on_reset_callback:
            self.on_reset_callback()
    
    def _on_exit_clicked(self) -> None:
        """Handle exit button click."""
        if self.on_exit_callback:
            self.on_exit_callback()
    
    def _on_import_clicked(self) -> None:
        """Handle import button click."""
        if self.on_import_callback:
            self.on_import_callback()
    
    def _on_digimon_changed(self, selected_digimon: str) -> None:
        """Handle Digimon selection change."""
        if self.on_digimon_change_callback:
            self.on_digimon_change_callback(selected_digimon)
    
    def update_digimon_list(self, digimon_list: list) -> None:
        """
        Update the Digimon selector dropdown with available Digimon.

        Args:
            digimon_list: List of available Digimon names
        """
        self._digimon_list = digimon_list
        if not self.digimon_selector:
            return

        # Clear existing options
        menu = self.digimon_selector['menu']
        menu.delete(0, 'end')

        # Add new options
        for digimon in digimon_list:
            menu.add_command(
                label=digimon,
                command=tk._setit(self.digimon_var, digimon, self._on_digimon_changed)
            )

        # Set default if current selection is not in the list
        current_selection = self.digimon_var.get()
        if current_selection not in digimon_list and digimon_list:
            self.digimon_var.set(digimon_list[0])
    
    def set_digimon_callbacks(self, 
                             on_import: Optional[Callable[[], None]] = None,
                             on_digimon_change: Optional[Callable[[str], None]] = None):
        """
        Set callback functions for Digimon-related interactions.
        
        Args:
            on_import: Called when import button is clicked
            on_digimon_change: Called when Digimon selection changes
        """
        self.on_import_callback = on_import
        self.on_digimon_change_callback = on_digimon_change


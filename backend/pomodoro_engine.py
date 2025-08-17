"""
Pomodoro Timer Backend Engine

This module contains the core business logic for the Pomodoro timer,
separated from GUI concerns for better maintainability.
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Optional

# Enhanced imports with fallbacks
try:
    from loguru import logger
    # Configure loguru for better logging
    logger.add("pomodoro.log", rotation="1 MB", retention="10 days", level="INFO")
    ENHANCED_LOGGING = True
except ImportError:
    import logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    ENHANCED_LOGGING = False

# Import time logger
from .time_logger import TimeLogger


class PomodoroEngine:
    """
    Core Pomodoro timer engine handling timer logic and state management.
    
    This class is responsible for:
    - Timer state management (running, paused, stopped)
    - Mode switching (work/break)
    - Time counting and callbacks
    - Session tracking
    """
    
    def __init__(self, work_duration: int = 25 * 60, break_duration: int = 5 * 60, vpet_name: str = "Agumon"):
        """
        Initialize the Pomodoro engine.
        
        Args:
            work_duration: Work session duration in seconds (default: 25 minutes)
            break_duration: Break session duration in seconds (default: 5 minutes)
            vpet_name: Name of the virtual pet companion (default: "Agumon")
        """
        self.work_duration = work_duration
        self.break_duration = break_duration
        self.vpet_name = vpet_name
        
        # Timer state
        self.is_running = False
        self.is_paused = False
        self.current_mode = "work"  # "work" or "break"
        self.time_remaining = self.work_duration
        
        # Session tracking
        self.sessions_completed = 0
        self.current_session_start = None
        
        # Timer thread
        self.timer_thread: Optional[threading.Thread] = None
        
        # Callbacks for events
        self.on_tick_callback: Optional[Callable[[int], None]] = None
        self.on_mode_change_callback: Optional[Callable[[str, str], None]] = None
        self.on_session_complete_callback: Optional[Callable[[str], None]] = None
        
        # Time logger for work session tracking
        self.time_logger = TimeLogger()
        
    def set_callbacks(self, 
                      on_tick: Optional[Callable[[int], None]] = None,
                      on_mode_change: Optional[Callable[[str, str], None]] = None,
                      on_session_complete: Optional[Callable[[str], None]] = None):
        """
        Set callback functions for timer events.
        
        Args:
            on_tick: Called every second with time_remaining
            on_mode_change: Called when mode changes (old_mode, new_mode)
            on_session_complete: Called when a session completes (completed_mode)
        """
        self.on_tick_callback = on_tick
        self.on_mode_change_callback = on_mode_change
        self.on_session_complete_callback = on_session_complete
    
    def start(self) -> bool:
        """
        Start the timer.
        
        Returns:
            bool: True if timer started successfully, False if already running
        """
        if self.is_running:
            return False
            
        self.is_running = True
        self.is_paused = False
        self.current_session_start = datetime.now()
        
        # Start work session logging only for work mode
        if self.current_mode == "work":
            self.time_logger.start_work_session(self.vpet_name)
        
        if self.timer_thread is None or not self.timer_thread.is_alive():
            self.timer_thread = threading.Thread(target=self._run_timer)
            self.timer_thread.daemon = True
            self.timer_thread.start()
            
        logger.info(f"Timer started: {self.current_mode} mode, {self.time_remaining}s remaining")
        return True
    
    def pause(self) -> bool:
        """
        Pause the timer.
        
        Returns:
            bool: True if timer paused successfully, False if not running
        """
        if not self.is_running:
            return False
            
        self.is_running = False
        self.is_paused = True
        
        # Stop work session logging if in work mode
        if self.current_mode == "work" and self.time_logger.is_session_active():
            self.time_logger.pause_work_session()
        
        logger.info(f"Timer paused: {self.time_remaining}s remaining")
        return True
    
    def resume(self) -> bool:
        """
        Resume the paused timer.
        
        Returns:
            bool: True if timer resumed successfully, False if not paused
        """
        if not self.is_paused:
            return False
            
        return self.start()
    
    def reset(self) -> None:
        """Reset the timer to initial state."""
        # Stop any active work session before resetting
        if self.time_logger.is_session_active():
            self.time_logger.stop_work_session(completed=False)
        
        self.is_running = False
        self.is_paused = False
        self.current_mode = "work"
        self.time_remaining = self.work_duration
        self.current_session_start = None
        
        logger.info("Timer reset")
        
        # Trigger tick callback to update display
        if self.on_tick_callback:
            self.on_tick_callback(self.time_remaining)
    
    def skip_session(self) -> None:
        """Skip the current session and switch to the next mode."""
        old_mode = self.current_mode
        self._switch_mode()
        
        logger.info(f"Session skipped: {old_mode} -> {self.current_mode}")
    
    def get_state(self) -> dict:
        """
        Get the current timer state.
        
        Returns:
            dict: Current timer state information
        """
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "current_mode": self.current_mode,
            "time_remaining": self.time_remaining,
            "sessions_completed": self.sessions_completed,
            "work_duration": self.work_duration,
            "break_duration": self.break_duration,
            "current_session_start": self.current_session_start
        }
    
    def set_durations(self, work_duration: int, break_duration: int) -> None:
        """
        Update work and break durations.
        
        Args:
            work_duration: New work duration in seconds
            break_duration: New break duration in seconds
        """
        self.work_duration = work_duration
        self.break_duration = break_duration
        
        # Update current time remaining if not running
        if not self.is_running:
            if self.current_mode == "work":
                self.time_remaining = self.work_duration
            else:
                self.time_remaining = self.break_duration
                
        logger.info(f"Durations updated: work={work_duration}s, break={break_duration}s")
    
    def _run_timer(self) -> None:
        """Main timer loop running in separate thread."""
        while self.time_remaining > 0 and self.is_running:
            time.sleep(1)
            if self.is_running:
                self.time_remaining -= 1
                
                # Trigger tick callback
                if self.on_tick_callback:
                    self.on_tick_callback(self.time_remaining)
        
        if self.time_remaining <= 0 and self.is_running:
            # Timer finished, handle completion
            self._handle_session_complete()
    
    def _handle_session_complete(self) -> None:
        """Handle timer completion and mode switching."""
        completed_mode = self.current_mode
        
        # Log work session completion if in work mode
        if completed_mode == "work" and self.time_logger.is_session_active():
            self.time_logger.stop_work_session(completed=True)
        
        # Update session count
        if completed_mode == "work":
            self.sessions_completed += 1
            
        # Trigger session complete callback
        if self.on_session_complete_callback:
            self.on_session_complete_callback(completed_mode)
        
        # Switch modes
        old_mode = self.current_mode
        self._switch_mode()
        
        # Stop timer
        self.is_running = False
        self.is_paused = False
        
        logger.info(f"Session completed: {completed_mode} (#{self.sessions_completed})")
        
        # Trigger mode change callback
        if self.on_mode_change_callback:
            self.on_mode_change_callback(old_mode, self.current_mode)
    
    def _switch_mode(self) -> None:
        """Switch between work and break modes."""
        if self.current_mode == "work":
            self.current_mode = "break"
            self.time_remaining = self.break_duration
        else:
            self.current_mode = "work"
            self.time_remaining = self.work_duration
    
    def set_vpet_name(self, vpet_name: str) -> None:
        """
        Set the name of the virtual pet companion.

        Args:
            vpet_name: The new name for the virtual pet
        """
        old_name = self.vpet_name
        self.vpet_name = vpet_name
        logger.info(f"VPet name changed from {old_name} to {vpet_name}")

    def format_time(self, seconds: Optional[int] = None) -> str:
        """
        Format time in MM:SS format.
        
        Args:
            seconds: Time in seconds (uses current time_remaining if None)
            
        Returns:
            str: Formatted time string
        """
        if seconds is None:
            seconds = self.time_remaining
            
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


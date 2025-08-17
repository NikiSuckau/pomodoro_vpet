"""
Time Logger Backend Module

This module handles logging of work session timings for productivity tracking.
It logs start/stop times of work sessions to help calculate actual work time.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# Enhanced imports with fallbacks
try:
    from loguru import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


class TimeLogger:
    """
    Time logger for tracking work session durations.

    This class is responsible for:
    - Logging work session start and stop times
    - Persisting session data to file
    - Calculating session durations
    - Providing session statistics
    """

    def __init__(self, log_file: str = "data/work_sessions.json"):
        """
        Initialize the time logger.

        Args:
            log_file: Path to the JSON file for storing session data
        """
        self.log_file = log_file
        self.current_session: Optional[Dict] = None
        self.sessions: List[Dict] = []

        # Load existing session data
        self._load_sessions()

        logger.info(f"TimeLogger initialized with log file: {log_file}")

    def start_work_session(self, vpet_name: str = "Agumon") -> bool:
        """
        Start logging a new work session.

        Args:
            vpet_name: Name of the virtual pet companion

        Returns:
            bool: True if session started successfully, False if already active
        """
        if self.current_session is not None:
            logger.warning(
                "Attempted to start work session while one is already active"
            )
            return False

        self.current_session = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_minutes": None,
            "session_type": "work",
            "completed": False,
            "vpet_name": vpet_name,
        }

        logger.info(f"Work session started at {self.current_session['start_time']} with {vpet_name}")
        return True

    def stop_work_session(self, completed: bool = True) -> Optional[Dict]:
        """
        Stop the current work session and save it.

        Args:
            completed: Whether the session was completed normally or interrupted

        Returns:
            Optional[Dict]: Session data if stopped successfully, None if no active session
        """
        if self.current_session is None:
            logger.warning("Attempted to stop work session but none is active")
            return None

        end_time = datetime.now()
        self.current_session["end_time"] = end_time.isoformat()
        self.current_session["completed"] = completed

        # Calculate duration
        start_time = datetime.fromisoformat(self.current_session["start_time"])
        duration = end_time - start_time
        self.current_session["duration_minutes"] = round(
            duration.total_seconds() / 60, 2
        )

        # Add to sessions list
        self.sessions.append(self.current_session.copy())

        # Save to file
        self._save_sessions()

        session_data = self.current_session.copy()
        self.current_session = None

        status = "completed" if completed else "interrupted"
        logger.info(
            f"Work session stopped ({status}): {session_data['duration_minutes']} minutes"
        )

        return session_data

    def pause_work_session(self) -> bool:
        """
        Pause the current work session (stops and marks as interrupted).

        Returns:
            bool: True if paused successfully, False if no active session
        """
        if self.current_session is None:
            return False

        self.stop_work_session(completed=False)
        logger.info("Work session paused")
        return True

    def is_session_active(self) -> bool:
        """
        Check if there's an active work session.

        Returns:
            bool: True if a session is currently active
        """
        return self.current_session is not None

    def get_current_session_duration(self) -> Optional[float]:
        """
        Get the duration of the current active session in minutes.

        Returns:
            Optional[float]: Duration in minutes, or None if no active session
        """
        if self.current_session is None:
            return None

        start_time = datetime.fromisoformat(self.current_session["start_time"])
        current_time = datetime.now()
        duration = current_time - start_time
        return round(duration.total_seconds() / 60, 2)

    def get_today_stats(self) -> Dict:
        """
        Get statistics for today's work sessions.

        Returns:
            Dict: Statistics including total time, session count, etc.
        """
        today = datetime.now().date()
        today_sessions = [
            session
            for session in self.sessions
            if datetime.fromisoformat(session["start_time"]).date() == today
        ]

        total_minutes = sum(
            session.get("duration_minutes", 0) for session in today_sessions
        )
        completed_sessions = sum(
            1 for session in today_sessions if session.get("completed", False)
        )

        return {
            "date": today.isoformat(),
            "total_minutes": round(total_minutes, 2),
            "total_hours": round(total_minutes / 60, 2),
            "session_count": len(today_sessions),
            "completed_sessions": completed_sessions,
            "interrupted_sessions": len(today_sessions) - completed_sessions,
        }

    def get_all_sessions(self) -> List[Dict]:
        """
        Get all logged sessions.

        Returns:
            List[Dict]: All session data
        """
        return self.sessions.copy()

    def get_stats_by_vpet(self) -> Dict:
        """
        Get statistics grouped by vpet name.

        Returns:
            Dict: Statistics for each vpet name
        """
        vpet_stats = {}
        
        for session in self.sessions:
            vpet_name = session.get("vpet_name", "Unknown")
            
            if vpet_name not in vpet_stats:
                vpet_stats[vpet_name] = {
                    "total_minutes": 0,
                    "session_count": 0,
                    "completed_sessions": 0,
                    "interrupted_sessions": 0
                }
            
            stats = vpet_stats[vpet_name]
            stats["total_minutes"] += session.get("duration_minutes", 0)
            stats["session_count"] += 1
            
            if session.get("completed", False):
                stats["completed_sessions"] += 1
            else:
                stats["interrupted_sessions"] += 1
        
        # Round total minutes and add derived stats
        for vpet_name, stats in vpet_stats.items():
            stats["total_minutes"] = round(stats["total_minutes"], 2)
            stats["total_hours"] = round(stats["total_minutes"] / 60, 2)
            if stats["session_count"] > 0:
                stats["success_rate"] = round(
                    (stats["completed_sessions"] / stats["session_count"]) * 100, 1
                )
            else:
                stats["success_rate"] = 0.0
        
        return vpet_stats

    def get_today_stats_by_vpet(self) -> Dict:
        """
        Get today's statistics grouped by vpet name.

        Returns:
            Dict: Today's statistics for each vpet name
        """
        today = datetime.now().date()
        today_sessions = [
            session
            for session in self.sessions
            if datetime.fromisoformat(session["start_time"]).date() == today
        ]
        
        vpet_stats = {}
        
        for session in today_sessions:
            vpet_name = session.get("vpet_name", "Unknown")
            
            if vpet_name not in vpet_stats:
                vpet_stats[vpet_name] = {
                    "total_minutes": 0,
                    "session_count": 0,
                    "completed_sessions": 0,
                    "interrupted_sessions": 0
                }
            
            stats = vpet_stats[vpet_name]
            stats["total_minutes"] += session.get("duration_minutes", 0)
            stats["session_count"] += 1
            
            if session.get("completed", False):
                stats["completed_sessions"] += 1
            else:
                stats["interrupted_sessions"] += 1
        
        # Round total minutes and add derived stats
        for vpet_name, stats in vpet_stats.items():
            stats["date"] = today.isoformat()
            stats["total_minutes"] = round(stats["total_minutes"], 2)
            stats["total_hours"] = round(stats["total_minutes"] / 60, 2)
            if stats["session_count"] > 0:
                stats["success_rate"] = round(
                    (stats["completed_sessions"] / stats["session_count"]) * 100, 1
                )
            else:
                stats["success_rate"] = 0.0
        
        return vpet_stats

    def cleanup_on_exit(self) -> None:
        """
        Clean up any active session when the application exits.
        Should be called before application shutdown.
        """
        if self.current_session is not None:
            logger.info(
                "Application exiting with active work session - stopping session"
            )
            self.stop_work_session(completed=False)

    def _load_sessions(self) -> None:
        """Load existing session data from file."""
        if not os.path.exists(self.log_file):
            logger.info(f"No existing log file found: {self.log_file}")
            return

        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.sessions = data.get("sessions", [])

            logger.info(
                f"Loaded {len(self.sessions)} existing sessions from {self.log_file}"
            )

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading session data: {e}")
            self.sessions = []

    def _save_sessions(self) -> None:
        """Save session data to file."""
        try:
            data = {
                "sessions": self.sessions,
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved {len(self.sessions)} sessions to {self.log_file}")

        except IOError as e:
            logger.error(f"Error saving session data: {e}")

    def export_sessions_csv(self, output_file: str = "work_sessions.csv") -> bool:
        """
        Export sessions to CSV format for analysis.

        Args:
            output_file: Path to the CSV output file

        Returns:
            bool: True if export successful, False otherwise
        """
        try:
            import csv

            with open(output_file, "w", newline="", encoding="utf-8") as f:
                if not self.sessions:
                    logger.info("No sessions to export")
                    return True

                fieldnames = [
                    "start_time",
                    "end_time",
                    "duration_minutes",
                    "session_type",
                    "completed",
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                writer.writeheader()
                for session in self.sessions:
                    writer.writerow(
                        {
                            "start_time": session.get("start_time"),
                            "end_time": session.get("end_time"),
                            "duration_minutes": session.get("duration_minutes"),
                            "session_type": session.get("session_type"),
                            "completed": session.get("completed"),
                        }
                    )

            logger.info(f"Exported {len(self.sessions)} sessions to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error exporting sessions to CSV: {e}")
            return False

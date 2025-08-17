import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.pomodoro_engine import PomodoroEngine


def test_initial_state():
    engine = PomodoroEngine()
    state = engine.get_state()
    assert state["current_mode"] == "work"
    assert state["time_remaining"] == engine.work_duration
    assert state["is_running"] is False


def test_time_format():
    engine = PomodoroEngine()
    assert engine.format_time(1500) == "25:00"
    assert engine.format_time(65) == "01:05"


def test_reset_stops_logging():
    engine = PomodoroEngine(work_duration=3)
    engine.start()
    time.sleep(0.1)
    engine.reset()
    assert engine.time_logger.is_session_active() is False
    state = engine.get_state()
    assert state["current_mode"] == "work"
    assert state["time_remaining"] == engine.work_duration

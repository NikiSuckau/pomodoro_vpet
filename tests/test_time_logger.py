import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.time_logger import TimeLogger


def test_start_stop_session(tmp_path):
    log_file = tmp_path / "sessions.json"
    logger = TimeLogger(log_file=str(log_file))
    assert logger.start_work_session("Test") is True
    time.sleep(0.1)
    data = logger.stop_work_session(completed=True)
    assert data["completed"] is True
    assert data["vpet_name"] == "Test"
    assert logger.is_session_active() is False


def test_data_persistence(tmp_path):
    log_file = tmp_path / "persist.json"
    logger1 = TimeLogger(log_file=str(log_file))
    logger1.start_work_session("A")
    time.sleep(0.1)
    logger1.stop_work_session(completed=True)
    logger2 = TimeLogger(log_file=str(log_file))
    sessions = logger2.get_all_sessions()
    assert len(sessions) == 1

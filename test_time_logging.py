#!/usr/bin/env python3
"""
Test script for time logging functionality

This script tests the TimeLogger integration with the Pomodoro engine
to ensure work sessions are properly logged.
"""

import time
import json
import os
from datetime import datetime
from backend.time_logger import TimeLogger
from backend.pomodoro_engine import PomodoroEngine


def test_time_logger_basic():
    """Test basic TimeLogger functionality."""
    print("Testing TimeLogger basic functionality...")
    
    # Create a test logger with a temporary file
    test_file = "test_sessions.json"
    logger = TimeLogger(log_file=test_file)
    
    # Test starting a session with vpet name
    assert logger.start_work_session("TestVPet") == True
    assert logger.is_session_active() == True
    print("✓ Session started successfully with vpet name")
    
    # Test attempting to start another session (should fail)
    assert logger.start_work_session() == False
    print("✓ Cannot start multiple sessions")
    
    # Wait a bit to accumulate some time
    time.sleep(2)
    
    # Check current session duration
    duration = logger.get_current_session_duration()
    assert duration is not None and duration > 0
    print(f"✓ Current session duration: {duration:.2f} minutes")
    
    # Test stopping the session
    session_data = logger.stop_work_session(completed=True)
    assert session_data is not None
    assert session_data["completed"] == True
    assert session_data["duration_minutes"] > 0
    print(f"✓ Session stopped: {session_data['duration_minutes']:.2f} minutes")
    
    # Test that session is no longer active
    assert logger.is_session_active() == False
    print("✓ Session properly deactivated")
    
    # Test getting today's stats
    stats = logger.get_today_stats()
    assert stats["session_count"] == 1
    assert stats["completed_sessions"] == 1
    assert stats["total_minutes"] > 0
    print(f"✓ Today's stats: {stats}")
    
    # Clean up test file
    if os.path.exists(test_file):
        os.remove(test_file)
    
    print("✓ Basic TimeLogger tests passed!\n")


def test_pomodoro_engine_integration():
    """Test TimeLogger integration with PomodoroEngine."""
    print("Testing PomodoroEngine integration...")
    
    # Create engine with short durations for testing
    engine = PomodoroEngine(work_duration=3, break_duration=2)
    
    # Test that TimeLogger is initialized
    assert hasattr(engine, 'time_logger')
    assert isinstance(engine.time_logger, TimeLogger)
    print("✓ TimeLogger properly integrated")
    
    # Start a work session
    assert engine.start() == True
    time.sleep(0.5)  # Give it a moment
    
    # Check that work session is being logged
    assert engine.time_logger.is_session_active() == True
    print("✓ Work session logging started")
    
    # Pause the session
    assert engine.pause() == True
    
    # Check that session was stopped
    assert engine.time_logger.is_session_active() == False
    print("✓ Session paused and logged")
    
    # Resume the session
    assert engine.resume() == True
    time.sleep(0.5)
    
    # Check that new session is active
    assert engine.time_logger.is_session_active() == True
    print("✓ Session resumed and logging restarted")
    
    # Reset the engine
    engine.reset()
    
    # Check that session was stopped
    assert engine.time_logger.is_session_active() == False
    print("✓ Session stopped on reset")
    
    # Test that break mode doesn't start logging
    engine.current_mode = "break"
    assert engine.start() == True
    time.sleep(0.5)
    
    # Should not be logging during break
    assert engine.time_logger.is_session_active() == False
    print("✓ Break mode doesn't trigger logging")
    
    engine.reset()
    print("✓ PomodoroEngine integration tests passed!\n")


def test_session_completion():
    """Test logging during automatic session completion."""
    print("Testing session completion logging...")
    
    # Create engine with very short work duration
    engine = PomodoroEngine(work_duration=1, break_duration=1)
    
    # Set up a callback to track completion
    completion_data = {"completed": False}
    
    def on_session_complete(mode):
        completion_data["completed"] = True
        completion_data["mode"] = mode
    
    engine.set_callbacks(on_session_complete=on_session_complete)
    
    # Start work session
    assert engine.start() == True
    assert engine.time_logger.is_session_active() == True
    
    # Wait for completion
    start_time = time.time()
    while not completion_data["completed"] and (time.time() - start_time) < 5:
        time.sleep(0.1)
    
    # Check that session completed and was logged
    assert completion_data["completed"] == True
    assert completion_data["mode"] == "work"
    assert engine.time_logger.is_session_active() == False
    
    # Check that session was recorded
    stats = engine.time_logger.get_today_stats()
    assert stats["session_count"] >= 1
    assert stats["completed_sessions"] >= 1
    
    print("✓ Session completion logging works")
    print(f"✓ Today's stats after completion: {stats}")
    print("✓ Session completion tests passed!\n")


def test_exit_cleanup():
    """Test cleanup on exit functionality."""
    print("Testing exit cleanup...")
    
    logger = TimeLogger(log_file="test_exit_cleanup.json")
    
    # Start a session
    assert logger.start_work_session() == True
    time.sleep(1)
    
    # Simulate exit cleanup
    logger.cleanup_on_exit()
    
    # Check that session was stopped and marked as incomplete
    assert logger.is_session_active() == False
    
    # Check the logged session
    sessions = logger.get_all_sessions()
    assert len(sessions) > 0
    last_session = sessions[-1]
    assert last_session["completed"] == False  # Should be marked as interrupted
    assert last_session["duration_minutes"] > 0
    
    print("✓ Exit cleanup properly stops active sessions")
    print(f"✓ Last session: {last_session}")
    
    # Clean up test file
    if os.path.exists("test_exit_cleanup.json"):
        os.remove("test_exit_cleanup.json")
    
    print("✓ Exit cleanup tests passed!\n")


def test_vpet_name_tracking():
    """Test vpet name tracking functionality."""
    print("Testing vpet name tracking...")
    
    test_file = "test_vpet_tracking.json"
    logger = TimeLogger(log_file=test_file)
    
    # Test session with first vpet
    assert logger.start_work_session("Agumon") == True
    time.sleep(1)
    session1 = logger.stop_work_session(completed=True)
    assert session1["vpet_name"] == "Agumon"
    print("✓ First vpet session logged correctly")
    
    # Test session with second vpet
    assert logger.start_work_session("Gabumon") == True
    time.sleep(1)
    session2 = logger.stop_work_session(completed=False)
    assert session2["vpet_name"] == "Gabumon"
    print("✓ Second vpet session logged correctly")
    
    # Test another session with first vpet
    assert logger.start_work_session("Agumon") == True
    time.sleep(1)
    session3 = logger.stop_work_session(completed=True)
    assert session3["vpet_name"] == "Agumon"
    print("✓ Third vpet session logged correctly")
    
    # Test vpet-specific statistics
    vpet_stats = logger.get_stats_by_vpet()
    assert "Agumon" in vpet_stats
    assert "Gabumon" in vpet_stats
    
    agumon_stats = vpet_stats["Agumon"]
    gabumon_stats = vpet_stats["Gabumon"]
    
    assert agumon_stats["session_count"] == 2, f"Expected 2 Agumon sessions, got {agumon_stats['session_count']}"
    assert agumon_stats["completed_sessions"] == 2, f"Expected 2 completed Agumon sessions, got {agumon_stats['completed_sessions']}"
    assert agumon_stats["success_rate"] == 100.0, f"Expected 100% Agumon success rate, got {agumon_stats['success_rate']}"
    
    assert gabumon_stats["session_count"] == 1, f"Expected 1 Gabumon session, got {gabumon_stats['session_count']}"
    assert gabumon_stats["completed_sessions"] == 0, f"Expected 0 completed Gabumon sessions, got {gabumon_stats['completed_sessions']}"
    assert gabumon_stats["success_rate"] == 0.0, f"Expected 0% Gabumon success rate, got {gabumon_stats['success_rate']}"
    
    print(f"✓ Agumon stats: {agumon_stats}")
    print(f"✓ Gabumon stats: {gabumon_stats}")
    
    # Test today's vpet-specific statistics
    today_vpet_stats = logger.get_today_stats_by_vpet()
    assert "Agumon" in today_vpet_stats
    assert "Gabumon" in today_vpet_stats
    
    today_agumon = today_vpet_stats["Agumon"]
    today_gabumon = today_vpet_stats["Gabumon"]
    
    assert today_agumon["session_count"] == 2
    assert today_gabumon["session_count"] == 1
    
    print(f"✓ Today's Agumon stats: {today_agumon}")
    print(f"✓ Today's Gabumon stats: {today_gabumon}")
    
    # Clean up test file
    if os.path.exists(test_file):
        os.remove(test_file)
    
    print("✓ VPet name tracking tests passed!\n")


def test_data_persistence():
    """Test that session data persists between logger instances."""
    print("Testing data persistence...")
    
    test_file = "test_persistence.json"
    
    # Create first logger and add a session
    logger1 = TimeLogger(log_file=test_file)
    logger1.start_work_session("TestVPet")
    time.sleep(1)
    session_data = logger1.stop_work_session(completed=True)
    
    initial_count = len(logger1.get_all_sessions())
    print(f"✓ First logger created {initial_count} sessions")
    
    # Create second logger with same file
    logger2 = TimeLogger(log_file=test_file)
    
    # Check that previous session was loaded
    loaded_sessions = logger2.get_all_sessions()
    assert len(loaded_sessions) == initial_count
    print(f"✓ Second logger loaded {len(loaded_sessions)} sessions")
    
    # Add another session with second logger
    logger2.start_work_session("AnotherVPet")
    time.sleep(1)
    logger2.stop_work_session(completed=True)
    
    # Check total count
    final_sessions = logger2.get_all_sessions()
    assert len(final_sessions) == initial_count + 1
    print(f"✓ Final session count: {len(final_sessions)}")
    
    # Clean up test file
    if os.path.exists(test_file):
        os.remove(test_file)
    
    print("✓ Data persistence tests passed!\n")


def main():
    """Run all time logging tests."""
    print("=" * 60)
    print("POMODORO TIME LOGGING TESTS")
    print("=" * 60)
    print()
    
    try:
        test_time_logger_basic()
        test_pomodoro_engine_integration()
        test_session_completion()
        test_exit_cleanup()
        test_vpet_name_tracking()
        test_data_persistence()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED! Time logging is working correctly.")
        print("=" * 60)
        print()
        print("Features verified:")
        print("✓ Work session start/stop logging")
        print("✓ Pause/resume handling")
        print("✓ Session completion logging")
        print("✓ Exit cleanup (stops active sessions)")
        print("✓ VPet name tracking and statistics")
        print("✓ Data persistence across app restarts")
        print("✓ Today's statistics calculation")
        print("✓ Break mode doesn't trigger logging")
        print()
        print("Your work sessions will now be logged to 'data/work_sessions.json'")
        print("You can analyze your productivity data later!")
        print("Use 'python view_work_stats.py' to see your statistics!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    main()


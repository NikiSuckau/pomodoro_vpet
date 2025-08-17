#!/usr/bin/env python
"""
Simple test script for the Pomodoro Timer functionality
"""

import sys
import os

# Add current directory to path so we can import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from pomodoro_timer import PomodoroTimer
    print("✓ Successfully imported PomodoroTimer")
    
    # Test timer initialization
    timer = PomodoroTimer()
    print("✓ Timer initialized successfully")
    
    # Test timer properties
    assert timer.work_duration == 25 * 60, "Work duration should be 25 minutes"
    assert timer.break_duration == 5 * 60, "Break duration should be 5 minutes"
    assert timer.current_mode == "work", "Should start in work mode"
    assert timer.time_remaining == timer.work_duration, "Should start with full work time"
    print("✓ Timer properties are correct")
    
    # Test time formatting
    assert timer.format_time(1500) == "25:00", "Should format 1500 seconds as 25:00"
    assert timer.format_time(300) == "05:00", "Should format 300 seconds as 05:00"
    assert timer.format_time(65) == "01:05", "Should format 65 seconds as 01:05"
    print("✓ Time formatting works correctly")
    
    # Test reset functionality
    timer.reset_timer()
    assert timer.current_mode == "work", "Reset should return to work mode"
    assert timer.time_remaining == timer.work_duration, "Reset should restore work duration"
    assert not timer.is_running, "Reset should stop the timer"
    print("✓ Reset functionality works")
    
    print("\n🎉 All tests passed! The Pomodoro Timer is ready to use.")
    print("\nTo run the timer, execute:")
    print("python pomodoro_timer.py")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)


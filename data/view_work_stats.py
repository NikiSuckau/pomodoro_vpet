#!/usr/bin/env python3
"""
Work Session Statistics Viewer

This script helps you view and analyze your work session data
logged by the Pomodoro timer application.
"""

import json
import os
from collections import defaultdict
from datetime import datetime, timedelta


def load_sessions(log_file="./data/work_sessions.json"):
    """Load session data from the log file."""
    if not os.path.exists(log_file):
        print(f"No log file found: {log_file}")
        return []

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("sessions", [])
    except Exception as e:
        print(f"Error loading sessions: {e}")
        return []


def format_duration(minutes):
    """Format duration in a human-readable way."""
    if minutes < 1:
        return f"{minutes * 60:.0f} seconds"
    elif minutes < 60:
        return f"{minutes:.1f} minutes"
    else:
        hours = minutes / 60
        return f"{hours:.1f} hours"


def get_today_stats(sessions):
    """Get statistics for today."""
    today = datetime.now().date()
    today_sessions = [
        s for s in sessions if datetime.fromisoformat(s["start_time"]).date() == today
    ]

    total_minutes = sum(s.get("duration_minutes", 0) for s in today_sessions)
    completed = sum(1 for s in today_sessions if s.get("completed", False))

    return {
        "sessions": today_sessions,
        "total_minutes": total_minutes,
        "total_sessions": len(today_sessions),
        "completed_sessions": completed,
        "interrupted_sessions": len(today_sessions) - completed,
    }


def get_stats_by_vpet(sessions):
    """Get statistics grouped by vpet name."""
    vpet_stats = defaultdict(
        lambda: {
            "total_minutes": 0,
            "session_count": 0,
            "completed_sessions": 0,
            "interrupted_sessions": 0,
        }
    )

    for session in sessions:
        vpet_name = session.get("vpet_name", "Unknown")
        stats = vpet_stats[vpet_name]

        stats["total_minutes"] += session.get("duration_minutes", 0)
        stats["session_count"] += 1

        if session.get("completed", False):
            stats["completed_sessions"] += 1
        else:
            stats["interrupted_sessions"] += 1

    # Calculate success rates
    for vpet_name, stats in vpet_stats.items():
        if stats["session_count"] > 0:
            stats["success_rate"] = (
                stats["completed_sessions"] / stats["session_count"]
            ) * 100
        else:
            stats["success_rate"] = 0.0

    return dict(vpet_stats)


def get_today_stats_by_vpet(sessions):
    """Get today's statistics grouped by vpet name."""
    today = datetime.now().date()
    today_sessions = [
        s for s in sessions if datetime.fromisoformat(s["start_time"]).date() == today
    ]

    return get_stats_by_vpet(today_sessions)


def get_weekly_stats(sessions):
    """Get statistics for this week."""
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())

    weekly_sessions = [
        s
        for s in sessions
        if datetime.fromisoformat(s["start_time"]).date() >= week_start
    ]

    total_minutes = sum(s.get("duration_minutes", 0) for s in weekly_sessions)
    completed = sum(1 for s in weekly_sessions if s.get("completed", False))

    # Group by day
    daily_stats = defaultdict(lambda: {"minutes": 0, "sessions": 0})
    for session in weekly_sessions:
        day = datetime.fromisoformat(session["start_time"]).date()
        daily_stats[day]["minutes"] += session.get("duration_minutes", 0)
        daily_stats[day]["sessions"] += 1

    return {
        "total_minutes": total_minutes,
        "total_sessions": len(weekly_sessions),
        "completed_sessions": completed,
        "daily_stats": dict(daily_stats),
    }


def main():
    """Display work session statistics."""
    print("=" * 60)
    print("WORK SESSION STATISTICS")
    print("=" * 60)
    print()

    sessions = load_sessions()
    if not sessions:
        print("No work sessions found yet.")
        print("Start using the Pomodoro timer to track your work!")
        return

    # Today's stats by VPet
    today_vpet_stats = get_today_stats_by_vpet(sessions)
    if today_vpet_stats:
        print("📅 TODAY'S WORK BY VPET:")
        for vpet_name, stats in today_vpet_stats.items():
            print(f"   🐾 {vpet_name}:")
            print(f"      Time: {format_duration(stats['total_minutes'])}")
            print(
                f"      Sessions: {stats['session_count']} (✓{stats['completed_sessions']} ⏸{stats['interrupted_sessions']})"
            )
            print(f"      Success rate: {stats['success_rate']:.1f}%")
        print()
    else:
        # Fallback to overall today's stats
        today_stats = get_today_stats(sessions)
        print("📅 TODAY'S WORK:")
        print(f"   Total time: {format_duration(today_stats['total_minutes'])}")
        print(f"   Sessions: {today_stats['total_sessions']}")
        print(f"   Completed: {today_stats['completed_sessions']}")
        print(f"   Interrupted: {today_stats['interrupted_sessions']}")
        print()

    # This week's stats
    weekly_stats = get_weekly_stats(sessions)
    print("📊 THIS WEEK'S WORK:")
    print(f"   Total time: {format_duration(weekly_stats['total_minutes'])}")
    print(f"   Sessions: {weekly_stats['total_sessions']}")
    print(f"   Completed: {weekly_stats['completed_sessions']}")
    print()

    # Daily breakdown for this week
    if weekly_stats["daily_stats"]:
        print("📈 DAILY BREAKDOWN:")
        for day, stats in sorted(weekly_stats["daily_stats"].items()):
            day_name = day.strftime("%A")
            print(
                f"   {day_name} ({day}): {format_duration(stats['minutes'])} in {stats['sessions']} sessions"
            )
        print()

    # All-time stats by VPet
    all_time_vpet_stats = get_stats_by_vpet(sessions)
    if all_time_vpet_stats:
        print("🏆 ALL-TIME STATS BY VPET:")
        for vpet_name, stats in all_time_vpet_stats.items():
            print(f"   🐾 {vpet_name}:")
            print(f"      Total time: {format_duration(stats['total_minutes'])}")
            print(
                f"      Sessions: {stats['session_count']} (✓{stats['completed_sessions']} ⏸{stats['interrupted_sessions']})"
            )
            print(f"      Success rate: {stats['success_rate']:.1f}%")
        print()
    else:
        # Fallback to overall all-time stats
        total_minutes = sum(s.get("duration_minutes", 0) for s in sessions)
        total_completed = sum(1 for s in sessions if s.get("completed", False))

        print("🏆 ALL-TIME STATS:")
        print(f"   Total work time: {format_duration(total_minutes)}")
        print(f"   Total sessions: {len(sessions)}")
        print(f"   Completed sessions: {total_completed}")
        print(f"   Success rate: {(total_completed/len(sessions)*100):.1f}%")
        print()

    # Recent sessions
    print("🕒 RECENT SESSIONS:")
    recent_sessions = sorted(sessions, key=lambda x: x["start_time"], reverse=True)[:5]
    for session in recent_sessions:
        start_time = datetime.fromisoformat(session["start_time"])
        status = "✓" if session.get("completed", False) else "⏸"
        duration = format_duration(session.get("duration_minutes", 0))
        vpet_name = session.get("vpet_name", "Unknown")
        print(
            f"   {status} {start_time.strftime('%Y-%m-%d %H:%M')} - {duration} - {vpet_name}"
        )

    print()
    print("💡 TIP: Keep working to improve your statistics!")
    print("    The more you use the Pomodoro timer, the better insights you'll get.")


if __name__ == "__main__":
    main()

"""
Pomodoro VPet Application

A Pomodoro timer with an animated virtual pet (Agumon) that reacts to your work sessions.
This is the main entry point that uses the refactored object-oriented structure.
"""

from main_app import MainWindow

if __name__ == "__main__":
    # Create and run the application
    app = MainWindow()
    app.run()


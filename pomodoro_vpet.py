"""
Pomodoro VPet Application

A Pomodoro timer with an animated virtual pet (Agumon) that reacts to your work sessions.
This is the main entry point that uses the refactored object-oriented structure.
"""

from app.pygame_app import PygameApp

if __name__ == "__main__":
    # Create and run the pygame based application
    app = PygameApp()
    app.run()


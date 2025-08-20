"""
Pomodoro VPet Application

A Pomodoro timer with an animated virtual pet rendered using pygame.
This is the main entry point for the object-oriented application.
"""

from app.main_window import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    app.run()

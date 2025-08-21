"""Entry point for the Pygame based Pomodoro VPet application."""

from app.pygame_app import PomodoroApp


def main() -> None:
    app = PomodoroApp()
    app.run()


if __name__ == "__main__":
    main()


# Pomodoro VPet Timer

A Pomodoro timer application with an integrated virtual pet companion.  The
interface is implemented with **pygame**, providing a lightweight window that
shows the timer and a small animated Digimon.

## Features

- Classic Pomodoro technique with 25 minute work sessions and 5 minute breaks
- Simple keyboard controls
- Animated Agumon sprite walking along the bottom of the window
- Object-oriented design separating backend logic from pygame rendering

## Architecture

```
├── app/                    # Application controller
│   └── main_window.py      # Pygame based main window
├── backend/                # Business logic layer
│   ├── pomodoro_engine.py  # Core timer logic and state management
│   ├── time_logger.py      # Work session tracking
│   └── vpet_engine.py      # (unused in pygame version) advanced pet logic
├── frontend/               # Pygame rendering helpers
│   └── pygame_gui.py       # Timer and virtual pet drawing
├── pomodoro_vpet.py        # Main entry point
└── tests/                  # Automated tests
```

## Requirements

- Python 3.8+
- Virtual environment (recommended)

## Installation

1. Clone or download this repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv pomo
   source pomo/bin/activate  # On Windows: pomo\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Ensure your virtual environment is activated, then run the application:

```bash
python pomodoro_vpet.py
```

### Controls

- **Space**: start/pause/resume the timer
- **R**: reset to the beginning of a work session
- **Esc** or window close: exit the application

### Timer Behavior

1. Starts with a 25‑minute work session
2. When work time ends, automatically switches to a 5‑minute break
3. Sessions continue alternating between work and break periods

## Testing

Run the automated test suite to verify everything is working:

```bash
pytest
```

## License

This project is open source and available under the MIT License.

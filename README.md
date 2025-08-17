# Pomodoro VPet Timer

A unique Pomodoro timer application with an integrated virtual pet (VPet) companion! Written in Python using tkinter, this timer combines productivity tracking with the nostalgic fun of caring for a digital pet. Inspired by classic Digimon virtual pets, your Agumon companion will train alongside you during work sessions.

## Features

- **Always on top**: The timer window stays visible above all other applications
- **Compact design**: Small 250x200 pixel window positioned in the top-right corner
- **Classic Pomodoro Technique**: 25-minute work sessions followed by 5-minute breaks
- **Visual feedback**: Different colors for work time (red) and break time (green)
- **Window flashing**: Gets your attention when a session ends
- **Simple controls**: Start/Pause/Resume and Reset buttons
- **Virtual Pet Companion**: Agumon walking animation below the timer
- **Adaptive VPet Behavior**: Pet moves faster during work sessions (training) and slower during breaks (relaxing)
- **Classic Digimon Sprites**: Authentic Agumon sprites for nostalgic virtual pet experience
- **Object-Oriented Architecture**: Clean separation between backend logic and frontend GUI components

## Architecture

The application follows object-oriented principles with clear separation of concerns:

```
├── backend/                 # Business logic layer
│   ├── pomodoro_engine.py  # Core timer logic and state management
│   └── vpet_engine.py      # VPet behavior and sprite management
├── frontend/               # GUI layer
│   ├── pomodoro_gui.py     # Timer display and controls
│   └── vpet_gui.py         # VPet canvas and rendering
├── main_app.py             # Application controller and coordination
├── pomodoro_vpet.py        # Main entry point
└── pomodoro_timer.py       # Legacy monolithic version (for reference)
```

### Component Responsibilities

- **Backend Engines**: Handle all business logic, state management, and data processing
- **Frontend GUIs**: Manage display, user interactions, and visual presentation
- **Main Controller**: Coordinates between backend and frontend, handles application lifecycle

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

### Legacy Version

The original monolithic version is still available:

```bash
python legacy/pomodoro_timer.py
```

### Controls

- **Start**: Begin the timer
- **Pause**: Pause the current session
- **Resume**: Continue a paused session
- **Reset**: Reset to the beginning of a work session

### Timer Behavior

1. Starts with a 25-minute work session
2. When work time ends, automatically switches to a 5-minute break
3. When break time ends, switches back to work time
4. The window will flash yellow briefly when a session ends to get your attention
5. Colors indicate the current mode:
   - Red text: Work time
   - Green text: Break time

## Customization

You can easily modify the timer durations by editing these variables in `pomodoro_timer.py`:

```python
self.work_duration = 25 * 60  # 25 minutes in seconds
self.break_duration = 5 * 60  # 5 minutes in seconds
```

## Testing

Run the test script to verify everything is working:

```bash
python test_pomodoro.py
```

## License

This project is open source and available under the MIT License.


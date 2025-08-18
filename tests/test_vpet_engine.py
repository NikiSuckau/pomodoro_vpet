import os
import sys
import tkinter as tk

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.vpet_engine import VPetEngine


def test_engine_initialization():
    try:
        root = tk.Tk()
        root.withdraw()
    except tk.TclError:
        pytest.skip("Tkinter display not available")
    engine = VPetEngine(root_window=root)
    assert engine.root_window is root
    root.destroy()


def test_attack_launches_projectile():
    engine = VPetEngine()
    # Ensure canvas small so projectile exits quickly
    engine.set_canvas_size(80, 60)
    attack_event = engine.events["attack"]
    attack_event.start(engine)
    # No projectiles initially
    assert engine.projectiles == []
    # Advance to the release frame where projectile launches
    for _ in range(attack_event.frame_delay + 1):
        attack_event.update(engine)
    assert len(engine.projectiles) == 1
    # Projectile should spawn from mid-body height
    assert engine.projectiles[0]["y"] == engine.canvas_height // 2 - engine.sprite_height // 4
    # Update projectiles until they vanish
    for _ in range(10):
        engine._update_projectiles()
    assert len(engine.projectiles) == 0


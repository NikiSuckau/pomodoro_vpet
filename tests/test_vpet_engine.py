import os
import sys
import tkinter as tk

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.vpet_engine import VPetEngine
from backend.pet_events import PetEvent


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
    assert engine.projectiles[0]["y"] == engine.canvas_height - engine.sprite_height // 2
    # Update projectiles until they vanish
    for _ in range(10):
        engine._update_projectiles()
    assert len(engine.projectiles) == 0


def test_queue_event_starts_immediately():
    engine = VPetEngine()
    engine.queue_event("happy")
    assert engine.active_event is engine.events["happy"]


def test_queue_event_runs_after_current():
    engine = VPetEngine()

    class DummyEvent(PetEvent):
        def __init__(self, name: str):
            super().__init__(name=name, frames=[0], modes=["work"], probability=0.0)

    first = DummyEvent("first")
    second = DummyEvent("second")
    engine.register_event(first)
    engine.register_event(second)

    engine.queue_event("first")
    engine.queue_event("second")

    assert engine.active_event is first
    assert engine.event_queue == ["second"]

    frame, finished = engine.active_event.update(engine)
    assert finished
    next_event = engine.active_event.complete(engine)
    engine.active_event = None
    if next_event:
        engine._activate_event(next_event)
    elif engine.event_queue:
        engine._activate_event(engine.event_queue.pop(0))

    assert engine.active_event is second


def test_set_scale_updates_dimensions():
    engine = VPetEngine()
    engine.set_scale(2)
    assert engine.sprite_width == engine.base_sprite_width * 2
    assert engine.projectile_width == engine.base_projectile_width * 2
    assert engine.margin == engine.base_margin * 2


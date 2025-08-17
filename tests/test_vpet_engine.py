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


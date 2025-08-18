"""Event system for the VPet engine.

This module defines a small framework that allows the virtual pet
engine to register arbitrary animation events.  Each event knows
when it can trigger, which animation frames it should display and
how many cycles it should play for.  Events are independent from the
main walking loop which makes it very easy to add new behaviours in
the future (e.g. eating, sleeping, ...).

All sprite frames are assumed to face left.  The engine will flip
the sprite automatically when the pet walks to the right so event
implementations do not need to worry about orientation.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Optional, Sequence


@dataclass
class PetEvent:
    """Generic description of an animation event.

    Attributes
    ----------
    name:
        Unique name of the event.
    frames:
        Sequence of sprite frame ids to play in order.
    modes:
        Iterable of pomodoro modes (``"work"``, ``"break"``, ``"idle"``)
        in which this event is allowed to trigger.
    probability:
        Per frame probability for the event to trigger while the pet is
        in a valid mode.
    frame_delay:
        Number of animation cycles to wait before switching to the next
        frame in ``frames``.
    cycles:
        Number of times the frames sequence should be played.  ``1`` means
        the sequence is shown once, ``2`` twice, ...
    condition:
        Optional callable returning ``True`` if the event may trigger
        given the current engine state.  This can be used to express
        additional constraints such as the pomodoro timer running.
    on_complete:
        Optional callback executed after the event finishes.  It may
        return the name of another event that should immediately start.
    """

    name: str
    frames: Sequence[int]
    modes: Iterable[str]
    probability: float
    frame_delay: int = 1
    cycles: int = 1
    condition: Optional[Callable[["VPetEngine"], bool]] = None
    on_complete: Optional[Callable[["VPetEngine"], Optional[str]]] = None

    active: bool = field(init=False, default=False)
    _current_frame_index: int = field(init=False, default=0)
    _frame_delay_counter: int = field(init=False, default=0)
    _cycles_remaining: int = field(init=False, default=0)

    def start(self, engine: "VPetEngine") -> None:
        """Activate the event and reset all counters."""
        self.active = True
        self._current_frame_index = 0
        self._frame_delay_counter = 0
        self._cycles_remaining = self.cycles

    def should_trigger(self, engine: "VPetEngine") -> bool:
        """Return ``True`` if the event wants to start."""
        if engine.current_mode not in self.modes:
            return False
        if self.condition and not self.condition(engine):
            return False
        return random.random() < self.probability

    def update(self, engine: "VPetEngine") -> tuple[int, bool]:
        """Advance the event by one animation tick.

        Returns a tuple ``(frame, finished)`` where ``frame`` is the
        sprite frame id to display and ``finished`` indicates whether the
        event has completed and should be cleaned up.
        """

        frame = self.frames[self._current_frame_index]
        self._frame_delay_counter += 1
        if self._frame_delay_counter >= self.frame_delay:
            self._frame_delay_counter = 0
            self._current_frame_index += 1
            if self._current_frame_index >= len(self.frames):
                self._current_frame_index = 0
                self._cycles_remaining -= 1
                if self._cycles_remaining <= 0:
                    self.active = False
                    return frame, True
        return frame, False

    def complete(self, engine: "VPetEngine") -> Optional[str]:
        """Handle event completion.

        The optional ``on_complete`` callback may return the name of
        another event that should trigger immediately.
        """

        if self.on_complete:
            return self.on_complete(engine)
        return None


class HappyEvent(PetEvent):
    """Small celebration animation used after other events or randomly."""

    def __init__(self) -> None:
        super().__init__(
            name="happy",
            frames=[7, 3],  # alternate between these two frames
            modes=["work", "break", "idle"],
            probability=0.03,
            frame_delay=2,
            cycles=1,
        )

    def start(self, engine: "VPetEngine") -> None:  # type: ignore[override]
        # Random number of cycles between 1 and 3 for variety
        self.cycles = random.randint(1, 3)
        super().start(engine)


class AttackTrainingEvent(PetEvent):
    """Attack training animation available during work mode."""

    def __init__(self, on_complete: Optional[Callable[["VPetEngine"], Optional[str]]] = None) -> None:
        super().__init__(
            name="attack",
            frames=[6, 11],  # two attack poses
            modes=["work"],
            probability=0.08,  # roughly 8% chance per frame
            frame_delay=3,
            cycles=1,
            condition=lambda eng: getattr(eng, "is_timer_running", True),
            on_complete=on_complete,
        )

    def start(self, engine: "VPetEngine") -> None:  # type: ignore[override]
        # Attack lasts for a random number of frame pairs
        self.cycles = random.randint(5, 10)
        super().start(engine)


# Utility function -----------------------------------------------------------

def collect_event_frames(events: Dict[str, PetEvent]) -> set[int]:
    """Return a set of all sprite frame ids required by the given events."""
    frames: set[int] = set()
    for event in events.values():
        frames.update(event.frames)
    return frames


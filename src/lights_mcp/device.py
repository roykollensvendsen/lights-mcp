"""What the plugin needs from a lights, and the ways asking one can fail.

The service talks to this and nothing else. The fake (`fake.py`) and the real adapter both
answer it, so every test runs through the same door the real device does.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class DeviceError(Exception):
    """Asking the lights failed; each kind below is said to the voice in its own words."""


class UnreachableError(DeviceError):
    """The lights did not answer in time."""


class SlowDownError(DeviceError):
    """The lights refuses to be asked again so soon."""

    def __init__(self, seconds: float) -> None:
        """Keep how long to wait, so the voice can say it."""
        super().__init__(f"ask again in {seconds:.0f} s")
        self.seconds = seconds


class NotSetUpError(DeviceError):
    """No real lights is set up, so nothing was asked."""


@dataclass(frozen=True)
class Reading:
    """What the lights says about itself: whether it is on, and its level from 0 to 100."""

    on: bool
    level: int


class Lights(Protocol):
    """A lights the plugin can read."""

    async def read(self) -> Reading:
        """The lights's state now."""
        ...


class Unconnected:
    """The real lights, until an adapter for it is written: every read says so."""

    async def read(self) -> Reading:
        """Refuse, naming the next step."""
        msg = "no adapter for a real lights is written yet; run with --simulate"
        raise NotSetUpError(msg)

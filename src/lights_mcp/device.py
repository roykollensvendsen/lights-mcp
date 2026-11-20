"""What the plugin needs from a lighting mesh, and the ways asking one can fail.

The service talks to this and nothing else. The fake (`fake.py`) and the real adapter both
answer it, so every test runs through the same door the real mesh does.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class DeviceError(Exception):
    """Asking the mesh failed; each kind below is said to the voice in its own words."""


class UnreachableError(DeviceError):
    """The link to the mesh is down, so no light can be read or changed."""


class NotSetUpError(DeviceError):
    """No real mesh is set up, so nothing was asked."""


@dataclass(frozen=True)
class Light:
    """One light as the mesh reports it: its name, whether it is on, and its level from 0 to 100."""

    name: str
    on: bool
    level: int
    dimmable: bool


class Mesh(Protocol):
    """A lighting mesh the plugin can read and change."""

    async def lights(self) -> list[Light]:
        """Every light and its state now."""
        ...

    async def switch(self, name: str, *, on: bool) -> None:
        """Ask the light called `name` to switch on or off."""
        ...

    async def dim(self, name: str, level: int) -> None:
        """Ask the light called `name` for a level from 1 to 100, which also switches it on."""
        ...


NO_ADAPTER = "no adapter for a real mesh is written yet; run with --simulate"


class Unconnected:
    """The real mesh, until its adapter is written: every request says so."""

    async def lights(self) -> list[Light]:
        """Refuse, naming the next step."""
        raise NotSetUpError(NO_ADAPTER)

    async def switch(self, name: str, *, on: bool) -> None:  # noqa: ARG002 - nothing is asked
        """Refuse, naming the next step."""
        raise NotSetUpError(NO_ADAPTER)

    async def dim(self, name: str, level: int) -> None:  # noqa: ARG002 - nothing is asked
        """Refuse, naming the next step."""
        raise NotSetUpError(NO_ADAPTER)

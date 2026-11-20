"""A made-up mesh of two lights that refuses what the real one refuses.

A fake that says yes to everything lets a test pass that the real mesh would fail. So this one
keeps the mesh's limits: a level outside 1 to 100 is refused, a light that only switches cannot
be dimmed, the link can be dropped, and a light can be left out of reach, taking no command.
Write each new limit of the real mesh in here first, with a test, before the code that copes
with it.
"""

from __future__ import annotations

from dataclasses import dataclass

from lights_mcp.device import Light, UnreachableError

LOWEST, HIGHEST = 1, 100


@dataclass
class _State:
    level: int  # 0 when off
    last: int  # the level it comes back on at
    dimmable: bool


class FakeMesh:
    """Two made-up lights in memory, with the real mesh's limits."""

    def __init__(self) -> None:
        """A dimmable lamp at 40 percent, and a light that only switches, off."""
        self._lights = {
            "Desk lamp": _State(level=40, last=40, dimmable=True),
            "Porch light": _State(level=0, last=HIGHEST, dimmable=False),
        }
        self.linked = True
        #: Lights out of reach: they take no command, and still read as before.
        self.stuck: set[str] = set()

    async def lights(self) -> list[Light]:
        """Every light, unless the link is down."""
        self._linked()
        return [Light(name, state.level > 0, state.level, state.dimmable) for name, state in self._lights.items()]

    async def switch(self, name: str, *, on: bool) -> None:
        """Switch a light on at its last level, or off."""
        state = self._light(name)
        if name not in self.stuck:
            state.level = state.last if on else 0

    async def dim(self, name: str, level: int) -> None:
        """Set a level from 1 to 100, which switches the light on."""
        state = self._light(name)
        # RULE: the fake refuses a level the device cannot take
        if not LOWEST <= level <= HIGHEST:
            msg = f"level {level} is outside {LOWEST} to {HIGHEST}"
            raise ValueError(msg)
        if not state.dimmable:
            msg = f"{name} only switches"
            raise ValueError(msg)
        if name not in self.stuck:
            state.level = state.last = level

    def _linked(self) -> None:
        if not self.linked:
            msg = "the link to the mesh is down"
            raise UnreachableError(msg)

    def _light(self, name: str) -> _State:
        self._linked()
        return self._lights[name]

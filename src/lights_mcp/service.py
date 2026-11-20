"""The core: ask the mesh, and word every answer for the voice.

It knows no MCP. Every answer is a dict with `success`, an `outcome` and a `say`, the
sentence the voice reads aloud as it is, and it has one even when the mesh fails. Every change
is read back from the mesh, so an answer says what the light reads, not what was asked.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lights_mcp.device import NotSetUpError, UnreachableError

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from lights_mcp.device import Light, Mesh

LINK_DOWN = (
    "The lights can't be reached: the Bluetooth link to them is down, so I don't know how they are "
    "and changed nothing. Check that the laptop's Bluetooth is on."
)
NOT_SET_UP = "No real lights are set up yet, so nothing was asked."
BROKE = "That went wrong inside lights-mcp. Try again, and if it fails again, check its log."
LEVELS = "Say a level from 1 to 100, or 0 to switch it off."
MOST = 100


class _UnknownLightError(Exception):
    def __init__(self, name: str, lights: list[Light]) -> None:
        names = ", ".join(light.name for light in lights)
        super().__init__(f"There's no light called {name}. The lights are: {names}.")


class LightsService:
    """What the tools ask, answered from one mesh."""

    def __init__(self, mesh: Mesh) -> None:
        """Answer from `mesh`, the fake or the real one."""
        self._mesh = mesh

    async def status(self, name: str | None = None) -> dict[str, Any]:
        """Each light, or the one called `name`, as a sentence."""

        async def read() -> dict[str, Any]:
            lights = await self._mesh.lights()
            chosen = [_find(lights, name)] if name else lights
            return {
                "success": True,
                "outcome": "read",
                "link": "up",
                "lights": [vars(light) for light in chosen],
                "say": " ".join(_said(light) for light in chosen),
            }

        return await _answer(read)

    async def switch(self, name: str, *, on: bool) -> dict[str, Any]:
        """Switch the light called `name` on or off, and say what it reads after."""

        async def change() -> dict[str, Any]:
            light = _find(await self._mesh.lights(), name)
            return await self._switch(light, on=on)

        return await _answer(change)

    async def dim(self, name: str, level: int) -> dict[str, Any]:
        """Set the light called `name` to `level`: 0 switches it off, and over 100 is 100."""

        async def change() -> dict[str, Any]:
            light = _find(await self._mesh.lights(), name)
            # RULE: a level below zero is refused
            if level < 0:
                return _failed("refused", f"A level can't be below 0. {LEVELS}")
            # RULE: dim to zero switches the light off
            if level == 0:
                return await self._switch(light, on=False)
            if not light.dimmable:
                return _failed("refused", f"{light.name} can only be switched on or off.")
            # RULE: a level above 100 is clamped to 100
            wanted = min(level, MOST)
            await self._mesh.dim(light.name, wanted)
            after = _find(await self._mesh.lights(), light.name)
            if _differs(after, on=True, level=wanted):
                return _failed(
                    "not_confirmed",
                    f"I asked {light.name} for {wanted} percent, but it still reads {after.level}. "
                    "It may be out of reach.",
                )
            said = f"{light.name} is at {wanted} percent."
            return {
                "success": True,
                "outcome": "dimmed",
                "level": wanted,
                "say": f"{MOST} is the most, so {said}" if level > MOST else said,
            }

        return await _answer(change)

    async def _switch(self, light: Light, *, on: bool) -> dict[str, Any]:
        await self._mesh.switch(light.name, on=on)
        after = _find(await self._mesh.lights(), light.name)
        state, was = ("on" if on else "off"), ("on" if after.on else "off")
        if _differs(after, on=on, level=None):
            return _failed(
                "not_confirmed",
                f"I asked {light.name} to switch {state}, but it still reads {was}. It may be out of reach.",
            )
        return {"success": True, "outcome": "switched", "on": on, "say": f"{light.name} is switched {state}."}


def _find(lights: list[Light], name: str) -> Light:
    wanted = name.strip().casefold()
    for light in lights:
        if light.name.casefold() == wanted:
            return light
    raise _UnknownLightError(name, lights)


def _differs(after: Light, *, on: bool, level: int | None) -> bool:
    """Whether a light read back after a change is not as it was asked to be."""
    # RULE: a change the mesh does not confirm is said
    return after.on != on or (level is not None and after.level != level)


def _said(light: Light) -> str:
    if not light.on:
        return f"{light.name} is off."
    return f"{light.name} is on, at {light.level} percent." if light.dimmable else f"{light.name} is on."


async def _answer(work: Callable[[], Awaitable[dict[str, Any]]]) -> dict[str, Any]:
    """The answer `work` gives, or a sentence for whatever stopped it."""
    try:
        return await work()
    except _UnknownLightError as unknown:
        return _failed("unknown_light", str(unknown))
    # RULE: a dropped link is said never guessed
    except UnreachableError:
        return {**_failed("link_down", LINK_DOWN), "link": "down"}
    except NotSetUpError:
        return _failed("not_set_up", NOT_SET_UP)
    # RULE: every answer has a sentence to say even when the lights fail
    except Exception:  # noqa: BLE001 - whatever broke, the voice gets a sentence
        return _failed("broke", BROKE)


def _failed(outcome: str, say: str) -> dict[str, Any]:
    return {"success": False, "outcome": outcome, "say": say}

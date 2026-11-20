"""The core: ask the lights, and word every answer for the voice.

It knows no MCP. Every answer is a dict with `success`, an `outcome` and a `say`, the
sentence the voice reads aloud as it is, and it has one even when the lights fails.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from lights_mcp.device import NotSetUpError, SlowDownError, UnreachableError

if TYPE_CHECKING:
    from lights_mcp.device import Lights

UNREACHABLE = "The lights isn't answering. Check that it is switched on and on the network."
NOT_SET_UP = "No real lights is set up yet, so nothing was asked."
BROKE = "That went wrong inside lights-mcp. Try again, and if it fails again, check its log."


class LightsService:
    """What the tools ask, answered from one lights."""

    def __init__(self, lights: Lights) -> None:
        """Answer from `lights`, the fake or the real one."""
        self._lights = lights

    async def status(self) -> dict[str, Any]:
        """Whether the lights is on, and its level, as a sentence."""
        try:
            reading = await self._lights.read()
        except SlowDownError as slow:
            seconds = max(1, math.ceil(slow.seconds))
            return _failed("slow_down", f"The lights is busy; ask again in {seconds} seconds.")
        except UnreachableError:
            return _failed("unreachable", UNREACHABLE)
        except NotSetUpError:
            return _failed("not_set_up", NOT_SET_UP)
        # RULE: every answer has a sentence to say even when the lights fails
        except Exception:  # noqa: BLE001 - whatever broke, the voice gets a sentence
            return _failed("broke", BROKE)
        state = "on" if reading.on else "off"
        return {
            "success": True,
            "outcome": "read",
            "on": reading.on,
            "level": reading.level,
            "say": f"The lights is {state}, at level {reading.level}.",
        }


def _failed(outcome: str, say: str) -> dict[str, Any]:
    return {"success": False, "outcome": outcome, "say": say}

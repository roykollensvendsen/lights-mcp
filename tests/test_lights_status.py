"""lights_status, end to end: through the MCP server, the service and the fake mesh.

This is the walking skeleton: it runs the whole way from the first commit. Every tool has a
file like this one, named after it (tests/test_every_tool_has_a_test.py).
"""

import asyncio

from lights_mcp.device import NotSetUpError
from lights_mcp.fake import FakeMesh
from lights_mcp.server import build_server
from lights_mcp.service import BROKE, LINK_DOWN, NOT_SET_UP, LightsService


def _call(mesh, arguments=None, *, simulated=False):
    server = build_server(LightsService(mesh), simulated=simulated)
    return asyncio.run(server.call_tool("lights_status", arguments or {})).structured_content


def test_the_status_says_each_light_and_its_level():
    answer = _call(FakeMesh())
    assert answer["say"] == "Desk lamp is on, at 40 percent. Porch light is off."
    assert (answer["success"], answer["link"], answer["simulated"]) == (True, "up", False)
    assert answer["lights"] == [
        {"name": "Desk lamp", "on": True, "level": 40, "dimmable": True},
        {"name": "Porch light", "on": False, "level": 0, "dimmable": False},
    ]


def test_one_light_can_be_asked_for_by_name_in_any_case():
    answer = _call(FakeMesh(), {"name": "porch LIGHT"})
    assert answer["say"] == "Porch light is off."
    assert [light["name"] for light in answer["lights"]] == ["Porch light"]


def test_a_light_that_is_not_there_is_said_with_the_names_that_are():
    answer = _call(FakeMesh(), {"name": "Attic"})
    assert answer["outcome"] == "unknown_light"
    assert answer["say"] == "There's no light called Attic. The lights are: Desk lamp, Porch light."


def test_a_simulated_answer_says_so():
    answer = _call(FakeMesh(), simulated=True)
    assert answer["simulated"] is True
    assert answer["say"].startswith("Simulated: ")


def test_a_dropped_link_is_said_never_guessed():
    """With the link down the plugin cannot know any light's state, so it says so and no more."""
    mesh = FakeMesh()
    mesh.linked = False
    answer = _call(mesh)
    assert answer == {"success": False, "outcome": "link_down", "link": "down", "say": LINK_DOWN, "simulated": False}


class _Broken:
    async def lights(self):
        msg = "a fault nobody planned for"
        raise RuntimeError(msg)


class _NotSetUp:
    async def lights(self):
        raise NotSetUpError


def test_every_answer_has_a_sentence_to_say_even_when_the_lights_fail():
    """Whatever broke, the voice gets a sentence to read, and never a stack trace."""
    assert _call(_Broken())["say"] == BROKE
    assert _call(_NotSetUp())["say"] == NOT_SET_UP

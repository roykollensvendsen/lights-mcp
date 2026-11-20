"""lights_switch, end to end: a light is switched on or off, and the mesh is asked whether it was."""

import asyncio

from lights_mcp.fake import FakeMesh
from lights_mcp.server import build_server
from lights_mcp.service import LINK_DOWN, LightsService


def _call(mesh, name, *, on):
    server = build_server(LightsService(mesh))
    return asyncio.run(server.call_tool("lights_switch", {"name": name, "on": on})).structured_content


def _state(mesh, name):
    return next(light for light in asyncio.run(mesh.lights()) if light.name == name)


def test_a_light_is_switched_on_and_says_so():
    mesh = FakeMesh()
    answer = _call(mesh, "porch light", on=True)
    assert (answer["success"], answer["outcome"]) == (True, "switched")
    assert answer["say"] == "Porch light is switched on."
    assert _state(mesh, "Porch light").on is True


def test_a_light_is_switched_off_and_says_so():
    mesh = FakeMesh()
    assert _call(mesh, "Desk lamp", on=False)["say"] == "Desk lamp is switched off."
    assert _state(mesh, "Desk lamp").on is False


def test_a_change_the_mesh_does_not_confirm_is_said():
    """A light out of reach takes no command, so the answer comes from reading it back."""
    mesh = FakeMesh()
    mesh.stuck.add("Porch light")
    answer = _call(mesh, "Porch light", on=True)
    assert (answer["success"], answer["outcome"]) == (False, "not_confirmed")
    assert answer["say"] == "I asked Porch light to switch on, but it still reads off. It may be out of reach."


def test_switching_a_light_that_is_not_there_changes_nothing():
    mesh = FakeMesh()
    assert _call(mesh, "Attic", on=True)["outcome"] == "unknown_light"
    assert [light.on for light in asyncio.run(mesh.lights())] == [True, False]


def test_a_switch_with_the_link_down_says_so_and_changes_nothing():
    mesh = FakeMesh()
    mesh.linked = False
    assert _call(mesh, "Porch light", on=True)["say"] == LINK_DOWN
    mesh.linked = True
    assert _state(mesh, "Porch light").on is False

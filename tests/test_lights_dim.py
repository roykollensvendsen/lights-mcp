"""lights_dim, end to end: a level from 1 to 100, 0 to switch off, and the edges said plainly."""

import asyncio

from lights_mcp.fake import FakeMesh
from lights_mcp.server import build_server
from lights_mcp.service import LightsService


def _call(mesh, name, level):
    server = build_server(LightsService(mesh))
    return asyncio.run(server.call_tool("lights_dim", {"name": name, "level": level})).structured_content


def _state(mesh, name):
    return next(light for light in asyncio.run(mesh.lights()) if light.name == name)


def test_a_light_is_dimmed_to_a_level_and_says_so():
    mesh = FakeMesh()
    answer = _call(mesh, "desk lamp", 70)
    assert (answer["success"], answer["outcome"], answer["level"]) == (True, "dimmed", 70)
    assert answer["say"] == "Desk lamp is at 70 percent."
    assert (_state(mesh, "Desk lamp").on, _state(mesh, "Desk lamp").level) == (True, 70)


def test_dim_to_zero_switches_the_light_off():
    mesh = FakeMesh()
    answer = _call(mesh, "Desk lamp", 0)
    assert (answer["success"], answer["outcome"]) == (True, "switched")
    assert answer["say"] == "Desk lamp is switched off."
    assert _state(mesh, "Desk lamp").on is False


def test_a_level_above_100_is_clamped_to_100():
    mesh = FakeMesh()
    answer = _call(mesh, "Desk lamp", 250)
    assert (answer["success"], answer["level"]) == (True, 100)
    assert answer["say"] == "100 is the most, so Desk lamp is at 100 percent."
    assert _state(mesh, "Desk lamp").level == 100


def test_a_level_below_zero_is_refused():
    mesh = FakeMesh()
    answer = _call(mesh, "Desk lamp", -10)
    assert (answer["success"], answer["outcome"]) == (False, "refused")
    assert answer["say"] == "A level can't be below 0. Say a level from 1 to 100, or 0 to switch it off."
    assert _state(mesh, "Desk lamp").level == 40


def test_a_light_that_only_switches_is_not_dimmed():
    mesh = FakeMesh()
    answer = _call(mesh, "Porch light", 50)
    assert (answer["success"], answer["outcome"]) == (False, "refused")
    assert answer["say"] == "Porch light can only be switched on or off."
    assert _call(mesh, "Porch light", 0)["say"] == "Porch light is switched off."


def test_a_dim_the_mesh_does_not_confirm_is_said():
    mesh = FakeMesh()
    mesh.stuck.add("Desk lamp")
    answer = _call(mesh, "Desk lamp", 70)
    assert (answer["success"], answer["outcome"]) == (False, "not_confirmed")
    assert answer["say"] == "I asked Desk lamp for 70 percent, but it still reads 40. It may be out of reach."

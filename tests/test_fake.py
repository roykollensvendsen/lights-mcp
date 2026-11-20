"""The fake mesh refuses what the real one refuses, so a test cannot pass that the lights would fail."""

import asyncio

import pytest

from lights_mcp.device import NotSetUpError, Unconnected, UnreachableError
from lights_mcp.fake import FakeMesh


def test_the_fake_refuses_a_level_the_device_cannot_take():
    mesh = FakeMesh()
    for level in (0, 101, -1):
        with pytest.raises(ValueError, match="1 to 100"):
            asyncio.run(mesh.dim("Desk lamp", level))


def test_the_fake_refuses_to_dim_a_light_that_only_switches():
    with pytest.raises(ValueError, match="only switches"):
        asyncio.run(FakeMesh().dim("Porch light", 50))


def test_the_fake_knows_only_its_own_lights():
    with pytest.raises(KeyError):
        asyncio.run(FakeMesh().switch("Attic", on=True))


def test_a_fake_with_its_link_down_answers_nothing_and_takes_nothing():
    mesh = FakeMesh()
    mesh.linked = False
    with pytest.raises(UnreachableError):
        asyncio.run(mesh.lights())
    with pytest.raises(UnreachableError):
        asyncio.run(mesh.switch("Desk lamp", on=False))
    with pytest.raises(UnreachableError):
        asyncio.run(mesh.dim("Desk lamp", 10))


def test_an_unconnected_mesh_says_what_to_do():
    with pytest.raises(NotSetUpError, match="--simulate"):
        asyncio.run(Unconnected().lights())

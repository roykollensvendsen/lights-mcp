"""Every tool has a test file of its own, and the voice can read each one's first line whole."""

import asyncio
import pathlib

from lights_mcp.fake import FakeMesh
from lights_mcp.server import FIRST_LINE_MAX, TOOLS, build_server
from lights_mcp.service import LightsService

TESTS = pathlib.Path(__file__).parent


def _tools():
    return {tool.name: tool for tool in asyncio.run(build_server(LightsService(FakeMesh())).list_tools())}


def test_every_tool_has_a_test_file_named_after_it():
    """A tool added without one would be tested only by luck."""
    missing = [name for name in TOOLS if not (TESTS / f"test_{name}.py").is_file()]
    assert missing == [], f"write {', '.join(f'tests/test_{name}.py' for name in missing)}"


def test_the_server_offers_exactly_the_tools_it_names():
    assert sorted(_tools()) == sorted(TOOLS)


def test_each_tool_opens_with_a_whole_sentence_the_app_shows_uncut():
    """The Claude app shows a tool by its first line until the tool is loaded, cut at 78 characters."""
    for tool in _tools().values():
        first = tool.description.splitlines()[0]
        assert len(first) <= FIRST_LINE_MAX, tool.name
        assert first.endswith(("?", ".")), tool.name


def test_a_tool_that_only_reads_says_so():
    tool = _tools()["lights_status"]
    assert tool.annotations.read_only_hint is True
    assert tool.annotations.destructive_hint is False


def test_a_tool_that_changes_a_light_never_says_it_only_reads():
    """Switching and dimming change the room, and can be undone by asking again."""
    for name in ("lights_switch", "lights_dim"):
        tool = _tools()[name]
        assert tool.annotations.read_only_hint is False, name
        assert (tool.annotations.destructive_hint, tool.annotations.idempotent_hint) == (False, True), name

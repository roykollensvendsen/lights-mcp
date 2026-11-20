"""The MCP server: the lights' tools, over stdio, for a voice session.

It only puts the core together and names the tools; every answer comes from the service.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

if TYPE_CHECKING:
    from lights_mcp.service import LightsService

#: The Claude app shows a tool by the start of its description, cut at this many characters.
FIRST_LINE_MAX = 78
INSTRUCTIONS = (
    "The owner's lights, on a Bluetooth mesh. Read each answer's 'say' aloud as it is. "
    "Switching and dimming can be undone by asking again, so do them when asked, without a question first."
)
SIMULATED = "SIMULATED lights, not real ones: say so. "
STATUS_DESCRIPTION = (
    "Which lights are on, and how bright?\n"
    "Each light, or the one named, with whether it is on and its level from 0 to 100. "
    "It only reads; it changes nothing."
)
SWITCH_DESCRIPTION = (
    "Switch a light on or off.\n"
    "Give the light's name as lights_status says it, and on true or false. "
    "The answer says what the light reads after."
)
DIM_DESCRIPTION = (
    "Set a light's brightness, from 1 to 100.\n"
    "0 switches it off, and over 100 sets 100. A light that only switches is not dimmed. "
    "The answer says what the light reads after."
)
#: Every tool, by name. The manifest lists the same, and each has a test file of its own.
TOOLS = ("lights_status", "lights_switch", "lights_dim")
READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True)
CHANGES = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True)


def build_server(service: LightsService, *, simulated: bool = False) -> MCPServer[Any]:
    """The MCP server with the lights' tools, answering from `service`."""
    server: MCPServer[Any] = MCPServer(
        name="lights-simulated" if simulated else "lights",
        instructions=(SIMULATED + INSTRUCTIONS) if simulated else INSTRUCTIONS,
    )

    def marked(answer: dict[str, Any]) -> dict[str, Any]:
        answer["simulated"] = simulated
        if simulated:
            answer["say"] = "Simulated: " + answer["say"]
        return answer

    @server.tool(annotations=READ_ONLY, description=STATUS_DESCRIPTION)
    async def lights_status(name: str | None = None) -> dict[str, Any]:
        return marked(await service.status(name))

    @server.tool(annotations=CHANGES, description=SWITCH_DESCRIPTION)
    async def lights_switch(name: str, on: bool) -> dict[str, Any]:  # noqa: FBT001 - a tool's arguments are named
        return marked(await service.switch(name, on=on))

    @server.tool(annotations=CHANGES, description=DIM_DESCRIPTION)
    async def lights_dim(name: str, level: int) -> dict[str, Any]:
        return marked(await service.dim(name, level))

    return server

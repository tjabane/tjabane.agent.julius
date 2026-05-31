
from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel


class Tool(Protocol):
    name: str
    description: str
    input_schema: type[BaseModel]

    async def run(self, input_data: BaseModel) -> Any:
        raise NotImplementedError()


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    @staticmethod
    def _to_model_tool(tool: Tool) -> dict[str, Any]:
        return {
            "type": "function",
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema.model_json_schema(),
        }

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Duplicate tool: {tool.name}")
        self._tools[tool.name] = tool

    def get_model_tools(self) -> list[dict[str, Any]]:
        return [self._to_model_tool(tool) for tool in self._tools.values()]

    def get(self, name: str) -> Tool:
        return self._tools[name]

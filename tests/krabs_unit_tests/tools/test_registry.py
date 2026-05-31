from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict, Field

from krabs_tools.registry import ToolRegistry


class ExampleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str = Field(min_length=1)


class ExampleTool:
    name = "example_tool"
    description = "Example tool."
    input_schema = ExampleInput

    async def run(self, input_data: ExampleInput) -> dict[str, Any]:
        return {"value": input_data.value}


class TestToolRegistry:
    def test_registers_and_returns_tool_by_name(self):
        registry = ToolRegistry()
        tool = ExampleTool()

        registry.register(tool)

        assert registry.get("example_tool") is tool

    def test_rejects_duplicate_tool_names(self):
        registry = ToolRegistry()
        registry.register(ExampleTool())

        with pytest.raises(ValueError, match="Duplicate tool: example_tool"):
            registry.register(ExampleTool())

    def test_get_model_tools_returns_openai_function_schema(self):
        registry = ToolRegistry()
        registry.register(ExampleTool())

        assert registry.get_model_tools() == [
            {
                "type": "function",
                "name": "example_tool",
                "description": "Example tool.",
                "parameters": ExampleInput.model_json_schema(),
            }
        ]

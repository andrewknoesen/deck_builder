from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Generic, TypeVar

ToolT = TypeVar("ToolT", bound="BaseTool")
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


@dataclass
class ToolContext:
    """Whatever shared stuff tools need (clients, config, etc.)."""

    # e.g. genai_client: GenAIClient
    # db: Session
    pass


class BaseTool(ABC, Generic[InputT, OutputT]):
    """Base class for all tools an agent can use."""

    def __init__(self, context: ToolContext) -> None:
        self._context = context

    @property
    def context(self) -> ToolContext:
        return self._context

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable identifier used by the agent/LLM."""

    @abstractmethod
    def run(self, params: InputT) -> OutputT:
        """Execute the tool with model-provided args."""


class BaseAgent(ABC, Generic[ToolT]):
    """Base class for agents bound to a specific tool family."""

    def __init__(self, prompt: str, tools: Iterable[ToolT]) -> None:
        self._tools = {tool.name: tool for tool in tools}
        self._prompt = prompt

    @property
    def prompt(self) -> str:
        """The prompt for the agent."""
        return self._prompt

    @property
    def tools(self) -> dict[str, ToolT]:
        return self._tools

    def get_tool(self, name: str) -> ToolT:
        return self._tools[name]

    @abstractmethod
    def run(self, query: str) -> object:
        """Main entrypoint: orchestrate model + tools."""

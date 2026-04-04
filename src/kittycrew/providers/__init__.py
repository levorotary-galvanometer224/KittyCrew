from __future__ import annotations

from pathlib import Path

from kittycrew.models import ProviderType
from kittycrew.providers.base import ProviderAdapter
from kittycrew.providers.claude_code import ClaudeCodeAdapter
from kittycrew.providers.codex import CodexAdapter
from kittycrew.providers.github_copilot import GitHubCopilotAdapter
from kittycrew.providers.kimi import KimiAdapter
from kittycrew.providers.opencode import OpenCodeAdapter


class ProviderRegistry:
    def __init__(self, adapters: dict[ProviderType, ProviderAdapter]) -> None:
        self._adapters = adapters

    def get(self, provider: ProviderType) -> ProviderAdapter:
        return self._adapters[provider]

    async def availability(self) -> dict[ProviderType, bool]:
        return {provider: await adapter.is_available() for provider, adapter in self._adapters.items()}

    def items(self) -> list[tuple[ProviderType, ProviderAdapter]]:
        return list(self._adapters.items())


def build_provider_registry(project_root: Path) -> ProviderRegistry:
    return ProviderRegistry(
        {
            ProviderType.CLAUDE_CODE: ClaudeCodeAdapter(project_root),
            ProviderType.CODEX: CodexAdapter(project_root),
            ProviderType.GITHUB_COPILOT: GitHubCopilotAdapter(project_root),
            ProviderType.KIMI: KimiAdapter(project_root),
            ProviderType.OPENCODE: OpenCodeAdapter(project_root),
        }
    )

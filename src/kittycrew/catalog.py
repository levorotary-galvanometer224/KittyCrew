from __future__ import annotations

from kittycrew.models import AvatarDefinition, ProviderDefinition, ProviderType


AVATAR_CATALOG: list[AvatarDefinition] = [
    AvatarDefinition(
        id="banner-cat",
        name="Banner Captain",
        asset_path="/static/avatars/banner-cat.svg",
        swatch="#ffd7a6",
        accent="#ff8f5a",
    ),
    AvatarDefinition(
        id="calico",
        name="Calico Comet",
        asset_path="/static/avatars/calico.svg",
        swatch="#ffe2ce",
        accent="#f07a53",
    ),
    AvatarDefinition(
        id="midnight",
        name="Midnight Socks",
        asset_path="/static/avatars/midnight.svg",
        swatch="#c7d0ff",
        accent="#5567da",
    ),
    AvatarDefinition(
        id="peach",
        name="Peach Puff",
        asset_path="/static/avatars/peach.svg",
        swatch="#ffd6d0",
        accent="#f08b73",
    ),
    AvatarDefinition(
        id="mint",
        name="Mint Biscuit",
        asset_path="/static/avatars/mint.svg",
        swatch="#d0f2d5",
        accent="#5db57a",
    ),
    AvatarDefinition(
        id="blueberry",
        name="Blueberry Whiskers",
        asset_path="/static/avatars/blueberry.svg",
        swatch="#d7e7ff",
        accent="#5690e4",
    ),
    AvatarDefinition(
        id="sunflower",
        name="Sunflower Paws",
        asset_path="/static/avatars/sunflower.svg",
        swatch="#ffefbb",
        accent="#d48d1f",
    ),
]


PROVIDER_LABELS: dict[ProviderType, str] = {
    ProviderType.CLAUDE_CODE: "Claude Code",
    ProviderType.CODEX: "Codex",
    ProviderType.GITHUB_COPILOT: "GitHub Copilot",
    ProviderType.KIMI: "Kimi",
    ProviderType.OPENCODE: "OpenCode",
}


PROVIDER_SUMMARIES: dict[ProviderType, str] = {
    ProviderType.CLAUDE_CODE: "Anthropic Claude Code CLI wrapped as a KittyCrew member.",
    ProviderType.CODEX: "OpenAI Codex CLI wrapped as a KittyCrew member.",
    ProviderType.GITHUB_COPILOT: "GitHub Copilot CLI wrapped as a KittyCrew member.",
    ProviderType.KIMI: "MoonshotAI Kimi Code CLI wrapped as a KittyCrew member.",
    ProviderType.OPENCODE: "OpenCode CLI wrapped as a KittyCrew member.",
}


def member_avatar_options() -> list[AvatarDefinition]:
    return [avatar for avatar in AVATAR_CATALOG if avatar.id != "banner-cat"]


def default_avatar(index: int) -> str:
    avatars = member_avatar_options()
    return avatars[index % len(avatars)].id


def find_avatar(avatar_id: str) -> AvatarDefinition | None:
    for avatar in AVATAR_CATALOG:
        if avatar.id == avatar_id:
            return avatar
    return None


def build_provider_definitions(availability: dict[ProviderType, bool]) -> list[ProviderDefinition]:
    return [
        ProviderDefinition(
            id=provider,
            label=PROVIDER_LABELS[provider],
            summary=PROVIDER_SUMMARIES[provider],
            available=availability.get(provider, False),
        )
        for provider in ProviderType
    ]

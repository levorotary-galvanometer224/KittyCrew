from __future__ import annotations

from pathlib import Path

from kittycrew.models import AgentSession, ChatMessage, ProviderType, SkillOption
from kittycrew.providers.claude_code import ClaudeCodeAdapter
from kittycrew.providers.codex import CodexAdapter
from kittycrew.providers.github_copilot import GitHubCopilotAdapter


def build_session(tmp_path: Path, provider: ProviderType) -> AgentSession:
    workspace_dir = tmp_path / provider.value
    config_dir = workspace_dir / ".config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return AgentSession(
        provider=provider,
        workspace_dir=str(workspace_dir),
        config_dir=str(config_dir),
    )


def test_provider_commands_include_requested_flags(tmp_path: Path) -> None:
    claude_session = build_session(tmp_path, ProviderType.CLAUDE_CODE)
    claude_session.model_id = "sonnet"
    claude_command = ClaudeCodeAdapter(tmp_path).build_command("claude", claude_session, "hello")
    assert "--dangerously-skip-permissions" in claude_command
    assert "--model" in claude_command
    assert "sonnet" in claude_command

    codex_session = build_session(tmp_path, ProviderType.CODEX)
    codex_session.model_id = "gpt-5.4"
    codex_command = CodexAdapter(tmp_path).build_command("codex", codex_session, "hello")
    assert "--dangerously-bypass-approvals-and-sandbox" in codex_command
    assert "--sandbox" not in codex_command
    assert "--model" in codex_command
    assert "gpt-5.4" in codex_command

    copilot_session = build_session(tmp_path, ProviderType.GITHUB_COPILOT)
    copilot_session.model_id = "gpt-5-mini"
    copilot_command = GitHubCopilotAdapter(tmp_path).build_command("copilot", copilot_session, "hello")
    assert "--yolo" in copilot_command
    assert "--model" in copilot_command
    assert "gpt-5-mini" in copilot_command


def test_claude_create_session_accepts_workdir_and_skills(tmp_path: Path) -> None:
    import asyncio

    async def scenario() -> None:
        workdir = tmp_path / "new-workdir"
        skill_file = tmp_path / "demo-skill" / "SKILL.md"
        skill_file.parent.mkdir()
        skill_file.write_text("---\nname: demo-skill\n---\n", encoding="utf-8")

        session = await ClaudeCodeAdapter(tmp_path).create_session(
            "session-1",
            working_dir=str(workdir),
            skills=[SkillOption(name="demo-skill", path=str(skill_file.resolve()))],
        )
        assert workdir.exists()
        assert session.working_dir == str(workdir.resolve())
        assert session.skills[0].name == "demo-skill"
        assert session.native_session_id == "session-1"

    asyncio.run(scenario())


def test_codex_environment_uses_isolated_skill_whitelist(tmp_path: Path) -> None:
    skill_file = tmp_path / "demo-skill" / "SKILL.md"
    skill_file.parent.mkdir()
    skill_file.write_text("---\nname: demo-skill\n---\n", encoding="utf-8")

    session = build_session(tmp_path, ProviderType.CODEX)
    session.skills = [SkillOption(name="demo-skill", path=str(skill_file.resolve()))]

    env = CodexAdapter(tmp_path).build_environment(session)
    assert "CODEX_HOME" in env
    config_path = Path(env["CODEX_HOME"]) / "config.toml"
    assert config_path.exists()
    assert str(skill_file.resolve()) in config_path.read_text(encoding="utf-8")


def test_copilot_prompt_is_compact_for_large_skill_context(tmp_path: Path) -> None:
    skill_file = tmp_path / "oversized-skill" / "SKILL.md"
    skill_file.parent.mkdir()
    skill_file.write_text(
        "---\nname: oversized-skill\n---\n\n" + ("Use this very long skill block.\n" * 1200),
        encoding="utf-8",
    )

    session = build_session(tmp_path, ProviderType.GITHUB_COPILOT)
    session.skills = [SkillOption(name="oversized-skill", path=str(skill_file.resolve()))]

    transcript = [
        ChatMessage(role="user", content="Please help me debug the current repository state."),
        ChatMessage(role="assistant", content="Tell me what changed most recently."),
        ChatMessage(role="user", content=("recent diff details " * 300).strip()),
    ]

    prompt = GitHubCopilotAdapter(tmp_path).build_prompt(transcript, session=session)

    assert len(prompt) <= 12000
    assert "Use this very long skill block." not in prompt


def test_copilot_prompt_uses_full_prompt_when_under_limit(tmp_path: Path) -> None:
    skill_file = tmp_path / "small-skill" / "SKILL.md"
    skill_file.parent.mkdir()
    skill_file.write_text(
        "---\nname: small-skill\ndescription: Small skill description.\n---\n\n# Small Skill\n",
        encoding="utf-8",
    )

    session = build_session(tmp_path, ProviderType.GITHUB_COPILOT)
    session.skills = [
        SkillOption(
            name="small-skill",
            path=str(skill_file.resolve()),
            description="Small skill description.",
        )
    ]

    prompt = GitHubCopilotAdapter(tmp_path).build_prompt(
        [ChatMessage(role="user", content="Say hello briefly.")],
        session=session,
    )

    assert "Respond to the latest user message while using previous turns as context." in prompt
    assert "Read the skill file only when you need its full instructions." in prompt


def test_provider_prompt_uses_skill_metadata_without_inlining_skill_body(tmp_path: Path) -> None:
    skill_file = tmp_path / "metadata-skill" / "SKILL.md"
    skill_file.parent.mkdir()
    skill_file.write_text(
        "---\nname: metadata-skill\ndescription: Use this skill for metadata-aware debugging.\n---\n\n# Metadata Skill\n\nBody content that should not be injected into the provider prompt.\n",
        encoding="utf-8",
    )

    session = build_session(tmp_path, ProviderType.CLAUDE_CODE)
    session.skills = [
        SkillOption(
            name="metadata-skill",
            path=str(skill_file.resolve()),
            description="Use this skill for metadata-aware debugging.",
        )
    ]

    prompt = ClaudeCodeAdapter(tmp_path).build_prompt(
        [ChatMessage(role="user", content="Investigate the latest failure.")],
        session=session,
    )

    assert "Selected skill: metadata-skill" in prompt
    assert str(skill_file.resolve()) in prompt
    assert "Description: Use this skill for metadata-aware debugging." in prompt
    assert "Body content that should not be injected into the provider prompt." not in prompt

from __future__ import annotations

import asyncio
from pathlib import Path

from kittycrew.catalog import build_provider_definitions
from kittycrew.models import AgentSession, ChatMessage, ProviderType, SkillOption
from kittycrew.providers.claude_code import ClaudeCodeAdapter
from kittycrew.providers.codex import CodexAdapter
from kittycrew.providers.github_copilot import GitHubCopilotAdapter
from kittycrew.providers import build_provider_registry
from kittycrew.providers.kimi import KimiAdapter
from kittycrew.providers.opencode import OpenCodeAdapter


def build_session(tmp_path: Path, provider: ProviderType) -> AgentSession:
    working_dir = tmp_path / provider.value
    config_dir = working_dir / ".kittycrew" / provider.value / "session-under-test" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return AgentSession(
        provider=provider,
        id="session-under-test",
        working_dir=str(working_dir),
        member_title="Mochi Whiskers",
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

    kimi_session = build_session(tmp_path, ProviderType.KIMI)
    kimi_session.model_id = "kimi-k2"
    kimi_command = KimiAdapter(tmp_path).build_command("kimi", kimi_session, "hello")
    assert "--print" in kimi_command
    assert "--final-message-only" in kimi_command
    assert "--yolo" in kimi_command
    assert "--work-dir" in kimi_command
    assert "--model" in kimi_command
    assert "kimi-k2" in kimi_command

    opencode_session = build_session(tmp_path, ProviderType.OPENCODE)
    opencode_session.model_id = "openai/gpt-5"
    opencode_command = OpenCodeAdapter(tmp_path).build_command("opencode", opencode_session, "hello")
    assert "run" in opencode_command
    assert "--format" in opencode_command
    assert "json" in opencode_command
    assert "--model" in opencode_command
    assert "openai/gpt-5" in opencode_command
    assert "hello" in opencode_command


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


def test_kimi_environment_uses_isolated_skill_directory(tmp_path: Path) -> None:
    skill_file = tmp_path / "demo-skill" / "SKILL.md"
    skill_file.parent.mkdir()
    skill_file.write_text(
        "---\nname: demo-skill\ndescription: Demo skill description.\n---\n",
        encoding="utf-8",
    )

    session = build_session(tmp_path, ProviderType.KIMI)
    session.skills = [SkillOption(name="demo-skill", path=str(skill_file.resolve()), description="Demo skill description.")]

    env = KimiAdapter(tmp_path).build_environment(session)

    isolated_skills_dir = Path(session.config_dir) / "kimi-skills"
    linked_skill = isolated_skills_dir / "demo-skill" / "SKILL.md"
    assert env["KITTYCREW_ALLOWED_SKILLS"] == str(skill_file.resolve())
    assert linked_skill.exists()
    assert linked_skill.resolve() == skill_file.resolve()


def test_opencode_environment_uses_isolated_config_dir(tmp_path: Path) -> None:
    skill_file = tmp_path / "demo-skill" / "SKILL.md"
    skill_file.parent.mkdir()
    skill_file.write_text("---\nname: demo-skill\n---\n", encoding="utf-8")

    session = build_session(tmp_path, ProviderType.OPENCODE)
    session.skills = [SkillOption(name="demo-skill", path=str(skill_file.resolve()))]

    env = OpenCodeAdapter(tmp_path).build_environment(session)

    assert env["OPENCODE_CONFIG_DIR"] == session.config_dir
    assert env["XDG_DATA_HOME"].endswith("/opencode-xdg/data")
    assert env["XDG_STATE_HOME"].endswith("/opencode-xdg/state")
    assert env["XDG_CACHE_HOME"].endswith("/opencode-xdg/cache")

    config_path = Path(session.config_dir) / "opencode.json"
    config_text = config_path.read_text(encoding="utf-8")
    assert '"*": "allow"' in config_text

    linked_skill = Path(session.config_dir) / "skills" / "demo-skill" / "SKILL.md"
    assert linked_skill.exists()
    assert linked_skill.resolve() == skill_file.resolve()


def test_opencode_list_models_parses_cli_output(tmp_path: Path, monkeypatch) -> None:
    async def fake_read_models_output(self) -> str:
        del self
        return "opencode/gpt-5-nano\nopenai/gpt-5\nanthropic/claude-sonnet-4-5\n"

    monkeypatch.setattr(OpenCodeAdapter, "_read_models_output", fake_read_models_output)

    models = asyncio.run(OpenCodeAdapter(tmp_path).list_models())

    assert [model.id for model in models] == [
        "opencode/gpt-5-nano",
        "openai/gpt-5",
        "anthropic/claude-sonnet-4-5",
    ]


def test_opencode_extract_content_uses_json_text_events(tmp_path: Path) -> None:
    adapter = OpenCodeAdapter(tmp_path)
    session = build_session(tmp_path, ProviderType.OPENCODE)
    stdout = "\n".join(
        [
            '{"type":"step_start","part":{"type":"step-start"}}',
            '{"type":"text","part":{"type":"text","text":"Hello"}}',
            '{"type":"text","part":{"type":"text","text":" there"}}',
            '{"type":"step_finish","part":{"type":"step-finish"}}',
        ]
    )

    content = asyncio.run(adapter.extract_content(session, stdout, ""))

    assert content == "Hello there"


def test_opencode_stream_emits_text_deltas(tmp_path: Path, monkeypatch) -> None:
    class DummyStdout:
        def __init__(self, lines: list[bytes]) -> None:
            self._lines = list(lines)

        async def readline(self) -> bytes:
            if self._lines:
                return self._lines.pop(0)
            return b""

    class DummyStderr:
        async def read(self) -> bytes:
            return b""

    class DummyProcess:
        def __init__(self) -> None:
            self.stdout = DummyStdout(
                [
                    b'{"type":"text","part":{"type":"text","text":"Hello"}}\n',
                    b'{"type":"text","part":{"type":"text","text":" there"}}\n',
                ]
            )
            self.stderr = DummyStderr()
            self.returncode = 0

        async def wait(self) -> int:
            return self.returncode

    async def fake_spawn_process(self, command, session, handle=None):
        del self, command, session, handle
        return DummyProcess()

    monkeypatch.setattr(OpenCodeAdapter, "resolve_command", lambda self: "opencode")
    monkeypatch.setattr(OpenCodeAdapter, "spawn_process", fake_spawn_process)

    async def scenario() -> list[tuple[str, str]]:
        adapter = OpenCodeAdapter(tmp_path)
        session = build_session(tmp_path, ProviderType.OPENCODE)
        transcript = [ChatMessage(role="user", content="Say hello.")]
        deltas = []
        async for delta in adapter.stream(session, transcript):
            deltas.append((delta.mode, delta.text))
        return deltas

    deltas = asyncio.run(scenario())

    assert deltas == [("append", "Hello"), ("append", " there")]


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


def test_provider_prompt_includes_member_persona_and_current_name(tmp_path: Path) -> None:
    session = build_session(tmp_path, ProviderType.CODEX)

    prompt = CodexAdapter(tmp_path).build_prompt(
        [ChatMessage(role="user", content="Help me plan the day.")],
        session=session,
    )

    assert "Your current member name is Mochi Whiskers." in prompt
    assert "You are a pet companion and work assistant." in prompt
    assert "Speak in a cute, warm tone while staying helpful, clear, and practical." in prompt


def test_provider_registry_and_catalog_include_kimi_and_opencode(tmp_path: Path) -> None:
    registry = build_provider_registry(tmp_path)

    providers = {provider for provider, _adapter in registry.items()}
    assert ProviderType.KIMI in providers
    assert ProviderType.OPENCODE in providers

    definitions = build_provider_definitions({provider: True for provider in ProviderType})
    definition_by_id = {definition.id: definition for definition in definitions}
    assert definition_by_id[ProviderType.KIMI].label == "Kimi"
    assert definition_by_id[ProviderType.OPENCODE].label == "OpenCode"

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

from kittycrew.models import AgentSession, ProviderModelOption, ProviderType, SkillOption
from kittycrew.providers.base import ProviderExecutionResult, ProviderStreamDelta
from kittycrew.service import CrewCapacityError, CrewService
from kittycrew.store import JsonStateStore


class FakeProviderAdapter:
    def __init__(self, provider: ProviderType, label: str, root: Path) -> None:
        self.provider = provider
        self.label = label
        self.root = root

    async def is_available(self) -> bool:
        return True

    async def create_session(
        self,
        session_id: str,
        working_dir: str | None = None,
        skills: list[SkillOption] | None = None,
        skill_name: str | None = None,
        skill_path: str | None = None,
    ) -> AgentSession:
        workspace = self.root / "sessions" / session_id
        workspace.mkdir(parents=True, exist_ok=True)
        selected_skills = list(skills or [])
        if not selected_skills and skill_name and skill_path:
            selected_skills = [SkillOption(name=skill_name, path=str(Path(skill_path).resolve()))]
        return AgentSession(
            id=session_id,
            provider=self.provider,
            workspace_dir=str(workspace),
            working_dir=str(Path(working_dir).resolve()) if working_dir else str(self.root.resolve()),
            config_dir=str(workspace / ".config"),
            skill_name=selected_skills[0].name if selected_skills else None,
            skill_path=selected_skills[0].path if selected_skills else None,
            skills=selected_skills,
        )

    async def run(self, session: AgentSession, transcript: list) -> ProviderExecutionResult:
        del session
        latest_user = next(message.content for message in reversed(transcript) if message.role == "user")
        return ProviderExecutionResult(content=f"{self.label} heard: {latest_user}")

    async def stream(self, session: AgentSession, transcript: list, handle=None) -> AsyncIterator[ProviderStreamDelta]:
        del session, handle
        latest_user = next(message.content for message in reversed(transcript) if message.role == "user")
        prefix = f"{self.label} heard: "
        yield ProviderStreamDelta(mode="replace", text=prefix)
        yield ProviderStreamDelta(mode="append", text=latest_user)

    async def delete_session(self, session: AgentSession) -> None:
        Path(session.workspace_dir).parent.mkdir(parents=True, exist_ok=True)
        if Path(session.workspace_dir).exists():
            for child in Path(session.workspace_dir).iterdir():
                if child.is_dir():
                    for nested in child.iterdir():
                        nested.unlink(missing_ok=True)
                    child.rmdir()
                else:
                    child.unlink(missing_ok=True)
            Path(session.workspace_dir).rmdir()

    async def list_models(self) -> list[ProviderModelOption]:
        return [
            ProviderModelOption(id=f"{self.provider.value}-default", label="Default"),
            ProviderModelOption(id=f"{self.provider.value}-pro", label="Pro"),
        ]

    async def validate_model(self, model_id: str | None) -> None:
        if model_id is None:
            return

        models = await self.list_models()
        if not any(model.id == model_id for model in models):
            raise ValueError(f"Unknown model: {model_id}")


class FakeRegistry:
    def __init__(self, root: Path) -> None:
        self._adapters = {
            ProviderType.CLAUDE_CODE: FakeProviderAdapter(ProviderType.CLAUDE_CODE, "Claude Code", root),
            ProviderType.CODEX: FakeProviderAdapter(ProviderType.CODEX, "Codex", root),
            ProviderType.GITHUB_COPILOT: FakeProviderAdapter(ProviderType.GITHUB_COPILOT, "GitHub Copilot", root),
        }

    def get(self, provider: ProviderType) -> FakeProviderAdapter:
        return self._adapters[provider]

    async def availability(self) -> dict[ProviderType, bool]:
        return {provider: True for provider in self._adapters}


def build_service(tmp_path: Path) -> CrewService:
    store = JsonStateStore(tmp_path / "state.json")
    return CrewService(store=store, registry=FakeRegistry(tmp_path), project_root=tmp_path)


def test_create_member_enforces_five_member_limit(tmp_path: Path) -> None:
    async def scenario() -> None:
        service = build_service(tmp_path)
        crew = await service.create_crew()

        for _ in range(5):
            await service.create_member(crew.id, ProviderType.CLAUDE_CODE)

        try:
            await service.create_member(crew.id, ProviderType.CODEX)
        except CrewCapacityError:
            return

        raise AssertionError("Expected CrewCapacityError when adding a sixth member.")

    asyncio.run(scenario())


def test_send_message_and_update_avatar(tmp_path: Path) -> None:
    async def scenario() -> None:
        service = build_service(tmp_path)
        crew = await service.create_crew()
        member = await service.create_member(crew.id, ProviderType.GITHUB_COPILOT)

        updated_avatar_member = await service.update_avatar(member.id, "mint")
        assert updated_avatar_member.avatar_id == "mint"

        updated_member = await service.send_message(member.id, "Hello KittyCrew")
        assert updated_member.status == "idle"
        assert [message.role for message in updated_member.messages] == ["user", "assistant"]
        assert updated_member.messages[-1].content == "GitHub Copilot heard: Hello KittyCrew"

    asyncio.run(scenario())


def test_stream_message_rename_and_delete_member(tmp_path: Path) -> None:
    async def scenario() -> None:
        service = build_service(tmp_path)
        crew = await service.create_crew()
        crew = await service.rename_crew(crew.id, "Night Shift")
        assert crew.name == "Night Shift"

        member = await service.create_member(crew.id, ProviderType.CLAUDE_CODE)
        member = await service.rename_member(member.id, "Scout Cat")
        assert member.title == "Scout Cat"

        events = []
        async for event in service.stream_message(member.id, "Stream this please"):
            events.append(event)

        assert [event["type"] for event in events] == ["member", "delta", "delta", "done"]
        assert events[1]["mode"] == "replace"
        assert events[2]["mode"] == "append"
        assert events[-1]["member"]["messages"][-1]["content"] == "Claude Code heard: Stream this please"

        session_dir = Path(events[-1]["member"]["session"]["workspace_dir"])
        assert session_dir.exists()

        await service.delete_member(member.id)
        assert not session_dir.exists()

    asyncio.run(scenario())


def test_delete_crew_removes_all_member_sessions(tmp_path: Path) -> None:
    async def scenario() -> None:
        service = build_service(tmp_path)
        crew = await service.create_crew()
        first_member = await service.create_member(crew.id, ProviderType.CLAUDE_CODE)
        second_member = await service.create_member(crew.id, ProviderType.CODEX)

        first_session_dir = Path(first_member.session.workspace_dir)
        second_session_dir = Path(second_member.session.workspace_dir)
        assert first_session_dir.exists()
        assert second_session_dir.exists()

        await service.delete_crew(crew.id)

        state = await service.bootstrap()
        assert state.state.crews == []
        assert not first_session_dir.exists()
        assert not second_session_dir.exists()

    asyncio.run(scenario())


def test_update_member_model_and_list_provider_models(tmp_path: Path) -> None:
    async def scenario() -> None:
        service = build_service(tmp_path)
        crew = await service.create_crew()
        member = await service.create_member(crew.id, ProviderType.CODEX)

        models = await service.list_provider_models(ProviderType.CODEX)
        assert [model.id for model in models] == ["codex-default", "codex-pro"]

        updated_member = await service.update_member_model(member.id, "codex-pro")
        assert updated_member.session.model_id == "codex-pro"

        reset_member = await service.update_member_model(member.id, None)
        assert reset_member.session.model_id is None

    asyncio.run(scenario())


def test_create_member_creates_missing_workdir_and_persists_multiple_skills(tmp_path: Path) -> None:
    async def scenario() -> None:
        workspace = tmp_path / "workspace"
        skill_file = tmp_path / "demo-skill" / "SKILL.md"
        skill_file.parent.mkdir()
        skill_file.write_text(
            "---\nname: demo-skill\ndescription: Demo skill\n---\n\n# Demo Skill\n\nUse this skill.\n",
            encoding="utf-8",
        )
        second_skill_file = tmp_path / "second-skill" / "SKILL.md"
        second_skill_file.parent.mkdir()
        second_skill_file.write_text(
            "---\nname: second-skill\ndescription: Second skill\n---\n\n# Second Skill\n\nUse this too.\n",
            encoding="utf-8",
        )

        service = build_service(tmp_path)
        service.skill_roots = [tmp_path]
        crew = await service.create_crew()
        member = await service.create_member(
            crew.id,
            ProviderType.CODEX,
            working_dir=str(workspace),
            skill_references=[str(skill_file), str(second_skill_file)],
        )

        assert workspace.exists()
        assert member.session.workspace_dir != str(workspace)
        assert member.session.working_dir == str(workspace.resolve())
        assert [skill.name for skill in member.session.skills] == ["demo-skill", "second-skill"]

    asyncio.run(scenario())


def test_update_member_skills_replaces_member_skill_list(tmp_path: Path) -> None:
    async def scenario() -> None:
        first_skill = tmp_path / "first-skill" / "SKILL.md"
        first_skill.parent.mkdir()
        first_skill.write_text("---\nname: first-skill\n---\n", encoding="utf-8")
        second_skill = tmp_path / "second-skill" / "SKILL.md"
        second_skill.parent.mkdir()
        second_skill.write_text("---\nname: second-skill\n---\n", encoding="utf-8")

        service = build_service(tmp_path)
        service.skill_roots = [tmp_path]
        crew = await service.create_crew()
        member = await service.create_member(crew.id, ProviderType.CLAUDE_CODE, skill_references=[str(first_skill)])

        updated = await service.update_member_skills(member.id, [str(second_skill)])
        assert [skill.name for skill in updated.session.skills] == ["second-skill"]
        assert updated.session.skill_name == "second-skill"

    asyncio.run(scenario())


def test_cancel_active_member_stream_marks_member_idle(tmp_path: Path) -> None:
    class DummyProcess:
        def __init__(self) -> None:
            self.returncode = None
            self.killed = False

        def kill(self) -> None:
            self.killed = True
            self.returncode = 1

        async def wait(self) -> None:
            return None

    async def scenario() -> None:
        from kittycrew.models import ChatMessage, MemberStatus
        from kittycrew.providers.base import ProviderExecutionHandle

        service = build_service(tmp_path)
        crew = await service.create_crew()
        member = await service.create_member(crew.id, ProviderType.CLAUDE_CODE)

        def set_thinking(state):
            target = service._find_member(state, member.id)
            target.messages.append(ChatMessage(role="user", content="Long running task"))
            target.messages.append(ChatMessage(role="assistant", content=""))
            target.status = MemberStatus.THINKING
            return target.model_copy(deep=True)

        await service.store.mutate(set_thinking)

        handle = ProviderExecutionHandle()
        process = DummyProcess()
        handle.attach(process)
        service._active_handles[member.id] = handle

        updated = await service.cancel_active_stream(member.id)

        assert process.killed is True
        assert updated.status == "idle"
        assert updated.messages[-1].role == "user"

    asyncio.run(scenario())

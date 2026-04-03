from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import suppress
from pathlib import Path
from uuid import uuid4

from kittycrew.catalog import build_provider_definitions, default_avatar, find_avatar, member_avatar_options, PROVIDER_LABELS
from kittycrew.models import (
    AppBootstrap,
    ChatMessage,
    Crew,
    CrewMember,
    MemberStatus,
    ProviderModelOption,
    ProviderType,
    SkillOption,
)
from kittycrew.providers import ProviderRegistry
from kittycrew.providers.base import ProviderExecutionHandle, ProviderUnavailableError
from kittycrew.skills import default_skill_roots, discover_skills, resolve_skill_reference, resolve_skill_references
from kittycrew.store import JsonStateStore


class CrewNotFoundError(ValueError):
    pass


class MemberNotFoundError(ValueError):
    pass


class CrewCapacityError(ValueError):
    pass


class AvatarValidationError(ValueError):
    pass


class CrewService:
    def __init__(self, store: JsonStateStore, registry: ProviderRegistry, project_root: Path, skill_roots: list[Path] | None = None) -> None:
        self.store = store
        self.registry = registry
        self.project_root = project_root
        self.skill_roots = skill_roots or default_skill_roots(project_root)
        self._member_locks: dict[str, asyncio.Lock] = {}
        self._active_handles: dict[str, ProviderExecutionHandle] = {}

    async def bootstrap(self) -> AppBootstrap:
        availability = await self.registry.availability()
        state = await self.store.load()
        return AppBootstrap(
            state=state,
            avatars=member_avatar_options(),
            providers=build_provider_definitions(availability),
            skills=self.list_skills(),
            project_root=str(self.project_root.resolve()),
        )

    async def create_crew(self) -> Crew:
        def operation(state):
            crew = Crew(name=f"Crew {len(state.crews) + 1}")
            state.crews.append(crew)
            return crew

        return await self.store.mutate(operation)

    async def create_member(
        self,
        crew_id: str,
        provider: ProviderType,
        working_dir: str | None = None,
        skill_references: list[str] | None = None,
        skill_reference: str | None = None,
    ) -> CrewMember:
        adapter = self.registry.get(provider)
        if not await adapter.is_available():
            raise ProviderUnavailableError(f"{PROVIDER_LABELS[provider]} CLI is not available.")

        member_id = str(uuid4())
        resolved_working_dir = self._normalize_working_dir(working_dir)
        requested_skills = list(skill_references or [])
        if skill_reference:
            requested_skills.append(skill_reference)
        resolved_skills = resolve_skill_references(requested_skills, self.list_skills())
        session = await adapter.create_session(
            member_id,
            working_dir=str(resolved_working_dir),
            skills=resolved_skills,
        )

        def operation(state):
            crew = self._find_crew(state, crew_id)
            if len(crew.members) >= 5:
                raise CrewCapacityError("Each crew can have at most 5 members.")

            member_index = sum(len(existing_crew.members) for existing_crew in state.crews)
            provider_count = sum(
                1
                for existing_crew in state.crews
                for member in existing_crew.members
                if member.provider == provider
            )

            member = CrewMember(
                id=member_id,
                crew_id=crew_id,
                provider=provider,
                title=f"{PROVIDER_LABELS[provider]} {provider_count + 1}",
                avatar_id=default_avatar(member_index),
                session=session,
            )
            crew.members.append(member)
            return member.model_copy(deep=True)

        return await self.store.mutate(operation)

    async def list_provider_models(self, provider: ProviderType) -> list[ProviderModelOption]:
        return await self.registry.get(provider).list_models()

    def list_skills(self) -> list[SkillOption]:
        return discover_skills(self.skill_roots)

    async def rename_crew(self, crew_id: str, name: str) -> Crew:
        trimmed_name = self._normalize_name(name, label="Crew name")

        def operation(state):
            crew = self._find_crew(state, crew_id)
            crew.name = trimmed_name
            return crew.model_copy(deep=True)

        return await self.store.mutate(operation)

    async def delete_crew(self, crew_id: str) -> None:
        members: list[CrewMember] = []

        def operation(state):
            nonlocal members
            for index, crew in enumerate(state.crews):
                if crew.id == crew_id:
                    members = [member.model_copy(deep=True) for member in crew.members]
                    del state.crews[index]
                    return None
            raise CrewNotFoundError(f"Crew {crew_id} was not found.")

        await self.store.mutate(operation)
        for member in members:
            await self._cleanup_member_runtime(member)

    async def rename_member(self, member_id: str, title: str) -> CrewMember:
        trimmed_title = self._normalize_name(title, label="Member name")

        def operation(state):
            member = self._find_member(state, member_id)
            member.title = trimmed_title
            return member.model_copy(deep=True)

        return await self.store.mutate(operation)

    async def update_member_model(self, member_id: str, model_id: str | None) -> CrewMember:
        normalized_model = model_id.strip() if isinstance(model_id, str) else None
        if normalized_model == "":
            normalized_model = None

        snapshot = await self.store.load()
        member = self._find_member(snapshot, member_id)
        adapter = self.registry.get(member.provider)
        await adapter.validate_model(normalized_model)

        def operation(state):
            target = self._find_member(state, member_id)
            target.session.model_id = normalized_model
            return target.model_copy(deep=True)

        return await self.store.mutate(operation)

    async def update_member_skills(self, member_id: str, skill_references: list[str] | None) -> CrewMember:
        resolved_skills = resolve_skill_references(skill_references or [], self.list_skills())

        def operation(state):
            target = self._find_member(state, member_id)
            target.session.skills = resolved_skills
            target.session.skill_name = resolved_skills[0].name if resolved_skills else None
            target.session.skill_path = resolved_skills[0].path if resolved_skills else None
            return target.model_copy(deep=True)

        return await self.store.mutate(operation)

    async def update_avatar(self, member_id: str, avatar_id: str) -> CrewMember:
        if not find_avatar(avatar_id) or avatar_id == "banner-cat":
            raise AvatarValidationError("Unknown avatar selection.")

        def operation(state):
            member = self._find_member(state, member_id)
            member.avatar_id = avatar_id
            return member.model_copy(deep=True)

        return await self.store.mutate(operation)

    async def delete_member(self, member_id: str) -> None:
        deleted_member: CrewMember | None = None

        def operation(state):
            nonlocal deleted_member
            for crew in state.crews:
                for index, member in enumerate(crew.members):
                    if member.id == member_id:
                        deleted_member = member.model_copy(deep=True)
                        del crew.members[index]
                        return None
            raise MemberNotFoundError(f"Member {member_id} was not found.")

        await self.store.mutate(operation)
        if deleted_member is not None:
            await self._cleanup_member_runtime(deleted_member)

    async def cancel_active_stream(self, member_id: str) -> CrewMember:
        snapshot = await self.store.load()
        self._find_member(snapshot, member_id)

        handle = self._active_handles.get(member_id)
        if handle is not None:
            await handle.cancel()

        self._active_handles.pop(member_id, None)

        def operation(state):
            member = self._find_member(state, member_id)
            if member.messages and member.messages[-1].role == "assistant" and not member.messages[-1].content.strip():
                member.messages.pop()
            member.status = MemberStatus.IDLE
            return member.model_copy(deep=True)

        return await self.store.mutate(operation)

    async def stream_message(self, member_id: str, content: str) -> AsyncGenerator[dict, None]:
        trimmed_content = content.strip()
        if not trimmed_content:
            raise ValueError("Message content cannot be empty.")

        lock = self._member_locks.setdefault(member_id, asyncio.Lock())
        async with lock:
            if member_id in self._active_handles:
                raise ValueError("This member is already streaming a response.")

            def add_streaming_messages(state):
                member = self._find_member(state, member_id)
                member.messages.append(ChatMessage(role="user", content=trimmed_content))
                member.messages.append(ChatMessage(role="assistant", content=""))
                member.status = MemberStatus.THINKING
                return member.model_copy(deep=True)

            member_snapshot = await self.store.mutate(add_streaming_messages)
            yield {"type": "member", "member": member_snapshot.model_dump(mode="json")}

            adapter = self.registry.get(member_snapshot.provider)
            await adapter.validate_model(member_snapshot.session.model_id)
            handle = ProviderExecutionHandle()
            self._active_handles[member_id] = handle

            try:
                async for delta in adapter.stream(member_snapshot.session, member_snapshot.messages, handle=handle):
                    with suppress(MemberNotFoundError):
                        await self._apply_stream_delta(member_id, delta.mode, delta.text)
                        yield {"type": "delta", "memberId": member_id, "mode": delta.mode, "text": delta.text}

                final_member = await self.store.mutate(lambda state: self._finalize_stream(state, member_id))
                yield {"type": "done", "member": final_member.model_dump(mode="json")}
            except Exception as exc:
                if handle.cancelled:
                    return

                error_text = str(exc) or "The provider command failed without a useful error message."
                try:
                    error_member = await self.store.mutate(
                        lambda state: self._replace_stream_with_error(state, member_id, error_text)
                    )
                except MemberNotFoundError:
                    return
                yield {"type": "error", "message": error_text, "member": error_member.model_dump(mode="json")}
            finally:
                self._active_handles.pop(member_id, None)

    async def send_message(self, member_id: str, content: str) -> CrewMember:
        trimmed_content = content.strip()
        if not trimmed_content:
            raise ValueError("Message content cannot be empty.")

        lock = self._member_locks.setdefault(member_id, asyncio.Lock())
        async with lock:
            def add_user_message(state):
                member = self._find_member(state, member_id)
                member.messages.append(ChatMessage(role="user", content=trimmed_content))
                member.status = MemberStatus.THINKING
                return member.model_copy(deep=True)

            member_snapshot = await self.store.mutate(add_user_message)
            adapter = self.registry.get(member_snapshot.provider)
            await adapter.validate_model(member_snapshot.session.model_id)

            try:
                result = await adapter.run(member_snapshot.session, member_snapshot.messages)
            except Exception as exc:
                error_text = str(exc) or "The provider command failed without a useful error message."

                def add_error_message(state):
                    member = self._find_member(state, member_id)
                    member.messages.append(ChatMessage(role="assistant", content=error_text, error=True))
                    member.status = MemberStatus.ERROR
                    return member.model_copy(deep=True)

                return await self.store.mutate(add_error_message)

            def add_assistant_message(state):
                member = self._find_member(state, member_id)
                member.messages.append(ChatMessage(role="assistant", content=result.content))
                member.status = MemberStatus.IDLE
                return member.model_copy(deep=True)

            return await self.store.mutate(add_assistant_message)

    async def _apply_stream_delta(self, member_id: str, mode: str, text: str) -> CrewMember:
        def operation(state):
            member = self._find_member(state, member_id)
            target_message = self._ensure_stream_target(member)
            if mode == "replace":
                target_message.content = text
            else:
                target_message.content += text
            target_message.error = False
            member.status = MemberStatus.THINKING
            return member.model_copy(deep=True)

        return await self.store.mutate(operation)

    def _finalize_stream(self, state, member_id: str) -> CrewMember:
        member = self._find_member(state, member_id)
        target_message = self._ensure_stream_target(member)
        if not target_message.content.strip():
            target_message.content = "The provider returned an empty response."
            target_message.error = True
            member.status = MemberStatus.ERROR
        else:
            member.status = MemberStatus.IDLE
        return member.model_copy(deep=True)

    def _replace_stream_with_error(self, state, member_id: str, error_text: str) -> CrewMember:
        member = self._find_member(state, member_id)
        target_message = self._ensure_stream_target(member)
        target_message.content = error_text
        target_message.error = True
        member.status = MemberStatus.ERROR
        return member.model_copy(deep=True)

    def _ensure_stream_target(self, member: CrewMember) -> ChatMessage:
        if member.messages and member.messages[-1].role == "assistant":
            return member.messages[-1]

        placeholder = ChatMessage(role="assistant", content="")
        member.messages.append(placeholder)
        return placeholder

    def _normalize_name(self, value: str, label: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError(f"{label} cannot be empty.")
        if len(trimmed) > 80:
            raise ValueError(f"{label} cannot be longer than 80 characters.")
        return trimmed

    def _normalize_working_dir(self, working_dir: str | None) -> Path:
        candidate = Path(working_dir).expanduser() if working_dir else self.project_root
        resolved = candidate.resolve()
        if not resolved.exists():
            resolved.mkdir(parents=True, exist_ok=True)
        if not resolved.is_dir():
            raise ValueError(f"Working directory '{resolved}' is not a directory.")
        return resolved

    async def _cleanup_member_runtime(self, member: CrewMember) -> None:
        handle = self._active_handles.pop(member.id, None)
        if handle is not None:
            await handle.cancel()

        self._member_locks.pop(member.id, None)
        await self.registry.get(member.provider).delete_session(member.session)

    def _find_crew(self, state, crew_id: str) -> Crew:
        for crew in state.crews:
            if crew.id == crew_id:
                return crew
        raise CrewNotFoundError(f"Crew {crew_id} was not found.")

    def _find_member(self, state, member_id: str) -> CrewMember:
        for crew in state.crews:
            for member in crew.members:
                if member.id == member_id:
                    return member
        raise MemberNotFoundError(f"Member {member_id} was not found.")

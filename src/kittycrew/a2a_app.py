from __future__ import annotations

import os
from collections.abc import Iterable

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2ARESTFastAPIApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Part,
    Task,
    TaskState,
    TextPart,
    TransportProtocol,
)
from a2a.utils import get_message_text, new_agent_text_message, new_task
from fastapi import FastAPI

from kittycrew.catalog import PROVIDER_LABELS, PROVIDER_SUMMARIES
from kittycrew.models import ChatMessage, ProviderType
from kittycrew.providers import ProviderRegistry
from kittycrew.providers.base import ProviderExecutionHandle


def create_kittycrew_a2a_apps(registry: ProviderRegistry) -> dict[ProviderType, FastAPI]:
    base_url = _public_base_url()
    apps: dict[ProviderType, FastAPI] = {}
    for provider in ProviderType:
        card = _build_agent_card(provider, base_url)
        handler = DefaultRequestHandler(
            agent_executor=KittyCrewProviderExecutor(provider=provider, registry=registry),
            task_store=InMemoryTaskStore(),
        )
        apps[provider] = A2ARESTFastAPIApplication(agent_card=card, http_handler=handler).build(
            title=f"KittyCrew {PROVIDER_LABELS[provider]} A2A"
        )
    return apps


class KittyCrewProviderExecutor(AgentExecutor):
    def __init__(self, provider: ProviderType, registry: ProviderRegistry) -> None:
        self.provider = provider
        self.registry = registry
        self._active_handles: dict[str, ProviderExecutionHandle] = {}

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task
        if task is None:
            if context.message is None:
                raise ValueError("A2A requests must include a message.")
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        transcript = _build_transcript(context, current_task=task)
        adapter = self.registry.get(self.provider)
        session = await adapter.create_session(task.context_id)
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        handle = ProviderExecutionHandle()
        self._active_handles[task.id] = handle

        try:
            assembled = ""
            async for delta in adapter.stream(session, transcript, handle=handle):
                if delta.mode == "replace":
                    assembled = delta.text
                else:
                    assembled += delta.text
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(assembled, task.context_id, task.id),
                )

            final_text = assembled.strip() or "The provider returned an empty response."
            await updater.add_artifact(
                [Part(root=TextPart(text=final_text))],
                name="response",
                last_chunk=True,
            )
            await updater.complete(new_agent_text_message(final_text, task.context_id, task.id))
        except Exception as exc:
            if handle.cancelled:
                return
            error_text = str(exc) or f"{PROVIDER_LABELS[self.provider]} failed without a useful error message."
            await updater.failed(new_agent_text_message(error_text, task.context_id, task.id))
        finally:
            self._active_handles.pop(task.id, None)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> Task | None:
        task_id = context.task_id
        if task_id is None:
            return context.current_task

        handle = self._active_handles.pop(task_id, None)
        if handle is not None:
            await handle.cancel()

        task = context.current_task
        if task is not None:
            updater = TaskUpdater(event_queue, task.id, task.context_id)
            await updater.cancel(
                new_agent_text_message(
                    f"{PROVIDER_LABELS[self.provider]} task cancelled.",
                    task.context_id,
                    task.id,
                )
            )
        return task


def _build_agent_card(provider: ProviderType, base_url: str) -> AgentCard:
    label = PROVIDER_LABELS[provider]
    skill = AgentSkill(
        id=f"kittycrew-{provider.value}",
        name=f"{label} session relay",
        description=PROVIDER_SUMMARIES[provider],
        tags=["kittycrew", "chat", provider.value],
        examples=[f"Ask {label} to summarize a repository change."],
    )

    return AgentCard(
        name=f"{label} A2A Agent",
        description=f"KittyCrew exposes {label} as an A2A-compatible teammate endpoint.",
        url=f"{base_url}/a2a/{provider.value}",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
        preferred_transport=TransportProtocol.http_json,
    )


def _build_transcript(context: RequestContext, current_task: Task) -> list[ChatMessage]:
    transcript: list[ChatMessage] = []
    seen_ids: set[str] = set()

    for message in _iter_a2a_messages(context, current_task):
        message_id = message.message_id or ""
        if message_id and message_id in seen_ids:
            continue
        if message_id:
            seen_ids.add(message_id)

        content = get_message_text(message).strip()
        if not content:
            continue

        transcript.append(ChatMessage(role=_map_role(message.role), content=content))

    return transcript


def _iter_a2a_messages(context: RequestContext, current_task: Task) -> Iterable:
    if current_task.history:
        yield from current_task.history

    if context.message is not None:
        last_message_id = current_task.history[-1].message_id if current_task.history else None
        if context.message.message_id != last_message_id:
            yield context.message


def _map_role(role) -> str:
    role_value = getattr(role, "value", role)
    if role_value == "agent":
        return "assistant"
    if role_value == "system":
        return "system"
    return "user"


def _public_base_url() -> str:
    explicit_base_url = os.getenv("KITTYCREW_PUBLIC_BASE_URL")
    if explicit_base_url:
        return explicit_base_url.rstrip("/")

    host = os.getenv("KITTYCREW_HOST", "127.0.0.1")
    port = os.getenv("KITTYCREW_PORT", "8731")
    return f"http://{host}:{port}"

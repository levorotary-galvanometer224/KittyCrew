from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from kittycrew.a2a_app import create_kittycrew_a2a_apps
from kittycrew.models import (
    AppBootstrap,
    CrewEnvelope,
    CreateMemberRequest,
    MemberEnvelope,
    ProviderType,
    ProviderModelsEnvelope,
    SkillsEnvelope,
    SendMessageRequest,
    UpdateAvatarRequest,
    UpdateCrewRequest,
    UpdateMemberModelRequest,
    UpdateMemberSkillsRequest,
    UpdateMemberRequest,
)
from kittycrew.providers import ProviderRegistry, build_provider_registry
from kittycrew.providers.base import ProviderExecutionError, ProviderUnavailableError
from kittycrew.service import AvatarValidationError, CrewCapacityError, CrewNotFoundError, CrewService, MemberNotFoundError
from kittycrew.store import JsonStateStore

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]


def build_service(project_root: Path = PROJECT_ROOT, registry: ProviderRegistry | None = None) -> CrewService:
    state_store = JsonStateStore(project_root / "data" / "state.json")
    return CrewService(store=state_store, registry=registry or build_provider_registry(project_root), project_root=project_root)


def create_app(service: CrewService | None = None) -> FastAPI:
    app = FastAPI(title="KittyCrew", description="Cute crew scheduler for CLI agents.")
    active_service = service or build_service()
    templates = Jinja2Templates(directory=str(PACKAGE_ROOT / "templates"))

    app.state.service = active_service
    app.mount("/static", StaticFiles(directory=str(PACKAGE_ROOT / "static")), name="static")
    for provider, a2a_app in create_kittycrew_a2a_apps(active_service.registry).items():
        app.mount(f"/a2a/{provider.value}", a2a_app, name=f"a2a-{provider.value}")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/api/state", response_model=AppBootstrap)
    async def get_state() -> AppBootstrap:
        return await active_service.bootstrap()

    @app.get("/api/skills", response_model=SkillsEnvelope)
    async def get_skills() -> SkillsEnvelope:
        return SkillsEnvelope(skills=active_service.list_skills())

    @app.post("/api/crews", response_model=CrewEnvelope, status_code=status.HTTP_201_CREATED)
    async def create_crew() -> CrewEnvelope:
        return CrewEnvelope(crew=await active_service.create_crew())

    @app.patch("/api/crews/{crew_id}", response_model=CrewEnvelope)
    async def rename_crew(crew_id: str, payload: UpdateCrewRequest) -> CrewEnvelope:
        try:
            crew = await active_service.rename_crew(crew_id, payload.name)
        except Exception as exc:
            raise _to_http_error(exc) from exc
        return CrewEnvelope(crew=crew)

    @app.delete("/api/crews/{crew_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_crew(crew_id: str) -> Response:
        try:
            await active_service.delete_crew(crew_id)
        except Exception as exc:
            raise _to_http_error(exc) from exc
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.post("/api/crews/{crew_id}/members", response_model=MemberEnvelope, status_code=status.HTTP_201_CREATED)
    async def create_member(crew_id: str, payload: CreateMemberRequest) -> MemberEnvelope:
        try:
            member = await active_service.create_member(
                crew_id,
                payload.provider,
                working_dir=payload.working_dir,
                skill_references=payload.skill_references,
                skill_reference=payload.skill_reference,
            )
        except Exception as exc:
            raise _to_http_error(exc) from exc
        return MemberEnvelope(member=member)

    @app.post("/api/members/{member_id}/avatar", response_model=MemberEnvelope)
    async def update_avatar(member_id: str, payload: UpdateAvatarRequest) -> MemberEnvelope:
        try:
            member = await active_service.update_avatar(member_id, payload.avatar_id)
        except Exception as exc:
            raise _to_http_error(exc) from exc
        return MemberEnvelope(member=member)

    @app.get("/api/providers/{provider}/models", response_model=ProviderModelsEnvelope)
    async def get_provider_models(provider: ProviderType) -> ProviderModelsEnvelope:
        try:
            models = await active_service.list_provider_models(provider)
        except Exception as exc:
            raise _to_http_error(exc) from exc
        return ProviderModelsEnvelope(models=models)

    @app.patch("/api/members/{member_id}", response_model=MemberEnvelope)
    async def rename_member(member_id: str, payload: UpdateMemberRequest) -> MemberEnvelope:
        try:
            member = await active_service.rename_member(member_id, payload.title)
        except Exception as exc:
            raise _to_http_error(exc) from exc
        return MemberEnvelope(member=member)

    @app.patch("/api/members/{member_id}/model", response_model=MemberEnvelope)
    async def update_member_model(member_id: str, payload: UpdateMemberModelRequest) -> MemberEnvelope:
        try:
            member = await active_service.update_member_model(member_id, payload.model_id)
        except Exception as exc:
            raise _to_http_error(exc) from exc
        return MemberEnvelope(member=member)

    @app.patch("/api/members/{member_id}/skills", response_model=MemberEnvelope)
    async def update_member_skills(member_id: str, payload: UpdateMemberSkillsRequest) -> MemberEnvelope:
        try:
            member = await active_service.update_member_skills(member_id, payload.skill_references)
        except Exception as exc:
            raise _to_http_error(exc) from exc
        return MemberEnvelope(member=member)

    @app.delete("/api/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_member(member_id: str) -> Response:
        try:
            await active_service.delete_member(member_id)
        except Exception as exc:
            raise _to_http_error(exc) from exc
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.post("/api/members/{member_id}/cancel", response_model=MemberEnvelope)
    async def cancel_member_stream(member_id: str) -> MemberEnvelope:
        try:
            member = await active_service.cancel_active_stream(member_id)
        except Exception as exc:
            raise _to_http_error(exc) from exc
        return MemberEnvelope(member=member)

    @app.post("/api/members/{member_id}/messages", response_model=MemberEnvelope)
    async def send_message(member_id: str, payload: SendMessageRequest) -> MemberEnvelope:
        try:
            member = await active_service.send_message(member_id, payload.content)
        except Exception as exc:
            raise _to_http_error(exc) from exc
        return MemberEnvelope(member=member)

    @app.post("/api/members/{member_id}/messages/stream")
    async def stream_message(member_id: str, payload: SendMessageRequest) -> StreamingResponse:
        async def emitter():
            try:
                async for event in active_service.stream_message(member_id, payload.content):
                    yield json.dumps(event, ensure_ascii=False) + "\n"
            except Exception as exc:
                yield json.dumps({"type": "error", "message": str(_to_http_error(exc).detail)}, ensure_ascii=False) + "\n"

        return StreamingResponse(emitter(), media_type="application/x-ndjson")

    return app


def _to_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, CrewNotFoundError | MemberNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, CrewCapacityError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, AvatarValidationError | ProviderExecutionError | ValueError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if isinstance(exc, ProviderUnavailableError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


app = create_app()

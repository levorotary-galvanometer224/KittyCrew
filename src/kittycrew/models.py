from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

SUPPORTED_SITE_THEMES = (
    "candy-soft",
    "sunset-pop",
    "mint-garden",
    "midnight-ink",
    "peach-cream",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ProviderType(str, Enum):
    CLAUDE_CODE = "claude_code"
    CODEX = "codex"
    GITHUB_COPILOT = "github_copilot"
    KIMI = "kimi"
    OPENCODE = "opencode"


class MemberStatus(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ERROR = "error"


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: str = Field(default_factory=utc_now)
    error: bool = False


class AgentSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    provider: ProviderType
    created_at: str = Field(default_factory=utc_now)
    working_dir: str
    member_title: str | None = None
    config_dir: str | None = None
    native_session_id: str | None = None
    model_id: str | None = None
    skills: list["SkillOption"] = Field(default_factory=list)
    skill_name: str | None = None
    skill_path: str | None = None


class CrewMember(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    crew_id: str
    provider: ProviderType
    title: str
    avatar_id: str
    created_at: str = Field(default_factory=utc_now)
    status: MemberStatus = MemberStatus.IDLE
    session: AgentSession
    messages: list[ChatMessage] = Field(default_factory=list)


class Crew(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    created_at: str = Field(default_factory=utc_now)
    members: list[CrewMember] = Field(default_factory=list)


class AppState(BaseModel):
    crews: list[Crew] = Field(default_factory=list)
    site_theme: str = "candy-soft"
    global_skills: list["SkillOption"] = Field(default_factory=list)


class AvatarDefinition(BaseModel):
    id: str
    name: str
    asset_path: str
    swatch: str
    accent: str


class ProviderDefinition(BaseModel):
    id: ProviderType
    label: str
    summary: str
    available: bool


class ProviderModelOption(BaseModel):
    id: str
    label: str


class SkillOption(BaseModel):
    name: str
    path: str
    description: str | None = None


class AppBootstrap(BaseModel):
    state: AppState
    avatars: list[AvatarDefinition]
    providers: list[ProviderDefinition]
    skills: list[SkillOption] = Field(default_factory=list)
    member_name_candidates: list[str] = Field(default_factory=list)
    project_root: str | None = None


class CreateMemberRequest(BaseModel):
    provider: ProviderType
    title: str | None = None
    working_dir: str | None = None
    skill_references: list[str] = Field(default_factory=list)
    skill_reference: str | None = None


class UpdateAvatarRequest(BaseModel):
    avatar_id: str


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class UpdateCrewRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class UpdateMemberRequest(BaseModel):
    title: str = Field(min_length=1, max_length=80)


class UpdateMemberModelRequest(BaseModel):
    model_id: str | None = None


class UpdateMemberSkillsRequest(BaseModel):
    skill_references: list[str] = Field(default_factory=list)


class UpdateSettingsRequest(BaseModel):
    site_theme: str = Field(default="candy-soft")
    global_skill_references: list[str] = Field(default_factory=list)


class CrewEnvelope(BaseModel):
    crew: Crew


class MemberEnvelope(BaseModel):
    member: CrewMember


class ProviderModelsEnvelope(BaseModel):
    models: list[ProviderModelOption]


class SkillsEnvelope(BaseModel):
    skills: list[SkillOption]

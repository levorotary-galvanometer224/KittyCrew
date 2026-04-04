from __future__ import annotations

import os
from pathlib import Path

from kittycrew.models import AgentSession, ProviderType
from kittycrew.providers.base import ProviderAdapter


class KimiAdapter(ProviderAdapter):
    provider = ProviderType.KIMI
    label = "Kimi"
    summary = "MoonshotAI Kimi Code CLI"

    def command_candidates(self) -> tuple[str, ...]:
        override = os.getenv("KITTYCREW_KIMI_BIN")
        return tuple(candidate for candidate in (override, "kimi") if candidate)

    def build_command(self, binary: str, session: AgentSession, prompt: str) -> list[str]:
        command = [
            binary,
            "--print",
            "--output-format",
            "text",
            "--final-message-only",
            "--yolo",
            "--work-dir",
            self.session_working_dir(session),
        ]
        if session.model_id:
            command.extend(["--model", session.model_id])

        skills_dir = self._prepare_skills_dir(session)
        if skills_dir is not None:
            command.extend(["--skills-dir", str(skills_dir)])

        command.extend(["--prompt", prompt])
        return command

    def build_environment(self, session: AgentSession) -> dict[str, str]:
        environment = super().build_environment(session)
        self._prepare_skills_dir(session)
        return environment

    def _prepare_skills_dir(self, session: AgentSession) -> Path | None:
        selected_skills = self.selected_skills(session)
        if not selected_skills:
            return None

        skills_dir = Path(session.config_dir or self.runtime_dir(session) / "config") / "kimi-skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        for skill in selected_skills:
            source = Path(skill.path).resolve()
            target_dir = skills_dir / skill.name
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / "SKILL.md"
            if target.exists() or target.is_symlink():
                target.unlink()
            target.symlink_to(source)

        return skills_dir

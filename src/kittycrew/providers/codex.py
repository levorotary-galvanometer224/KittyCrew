from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from pathlib import Path
import shutil

from kittycrew.models import AgentSession, ProviderModelOption, ProviderType
from kittycrew.providers.base import ProviderAdapter, ProviderExecutionError, ProviderExecutionHandle, ProviderStreamDelta


class CodexAdapter(ProviderAdapter):
    provider = ProviderType.CODEX
    label = "Codex"
    summary = "OpenAI Codex CLI"

    def command_candidates(self) -> tuple[str, ...]:
        override = os.getenv("KITTYCREW_CODEX_BIN")
        return tuple(candidate for candidate in (override, "codex") if candidate)

    def build_command(self, binary: str, session: AgentSession, prompt: str) -> list[str]:
        output_path = self.runtime_dir(session) / ".codex-last-message.txt"
        output_path.unlink(missing_ok=True)
        working_dir = self.session_working_dir(session)
        command = [
            binary,
            "exec",
            "--skip-git-repo-check",
            "--dangerously-bypass-approvals-and-sandbox",
            "--color",
            "never",
            "-C",
            working_dir,
            "-o",
            str(output_path),
            prompt,
        ]
        if session.model_id:
            command[2:2] = ["--model", session.model_id]
        return command

    async def list_models(self) -> list[ProviderModelOption]:
        cache_path = Path(os.getenv("KITTYCREW_CODEX_MODELS_CACHE", Path.home() / ".codex" / "models_cache.json"))
        if not cache_path.exists():
            return []

        payload = self._read_json_file(cache_path)
        models = payload.get("models", []) if isinstance(payload, dict) else []
        return [
            ProviderModelOption(id=model["slug"], label=model.get("display_name", model["slug"]))
            for model in models
            if isinstance(model, dict) and isinstance(model.get("slug"), str)
        ]

    def build_environment(self, session: AgentSession) -> dict[str, str]:
        environment = super().build_environment(session)
        codex_home = Path(session.config_dir or self.runtime_dir(session) / "config") / "codex-home"
        codex_home.mkdir(parents=True, exist_ok=True)
        (codex_home / "skills").mkdir(parents=True, exist_ok=True)

        source_home = Path.home() / ".codex"
        for filename in ("auth.json", "models_cache.json", "version.json"):
            source = source_home / filename
            target = codex_home / filename
            if source.exists() and not target.exists():
                shutil.copy2(source, target)

        config_lines = ["model_reasoning_effort = \"medium\"", ""]
        for skill in self.selected_skills(session):
            config_lines.append("[[skills.config]]")
            config_lines.append(f"path = {json.dumps(skill.path)}")
            config_lines.append("enabled = true")
            config_lines.append("")
        (codex_home / "config.toml").write_text("\n".join(config_lines).strip() + "\n", encoding="utf-8")
        environment["CODEX_HOME"] = str(codex_home)
        return environment

    async def stream(
        self,
        session: AgentSession,
        transcript,
        handle: ProviderExecutionHandle | None = None,
    ) -> AsyncIterator[ProviderStreamDelta]:
        binary = self.resolve_command()
        if not binary:
            raise ProviderExecutionError(f"{self.label} CLI is not available on this machine.")

        prompt = self.build_prompt(transcript, session=session)
        working_dir = self.session_working_dir(session)
        command = [
            binary,
            "exec",
            "--skip-git-repo-check",
            "--dangerously-bypass-approvals-and-sandbox",
            "--color",
            "never",
            "--json",
            "-C",
            working_dir,
            prompt,
        ]
        if session.model_id:
            command[2:2] = ["--model", session.model_id]
        process = await self.spawn_process(command, session, handle=handle)

        latest_text = ""

        while True:
            line = await process.stdout.readline()
            if not line:
                break

            payload = line.decode("utf-8", errors="replace").strip()
            if not payload:
                continue

            try:
                event = json.loads(payload)
            except json.JSONDecodeError:
                continue

            if event.get("type") != "item.completed":
                continue

            item = event.get("item", {})
            if item.get("type") != "agent_message":
                continue

            text = item.get("text", "").strip()
            if not text:
                continue

            latest_text = text
            yield ProviderStreamDelta(mode="replace", text=text)

        stderr = (await process.stderr.read()).decode("utf-8", errors="replace").strip()
        await process.wait()

        if process.returncode != 0:
            detail = stderr or f"{self.label} exited with code {process.returncode}."
            raise ProviderExecutionError(detail)

        if not latest_text:
            detail = stderr or f"{self.label} returned an empty response."
            raise ProviderExecutionError(detail)

    async def extract_content(self, session: AgentSession, stdout: str, stderr: str) -> str:
        del stderr
        output_path = self.runtime_dir(session) / ".codex-last-message.txt"
        if output_path.exists():
            file_content = output_path.read_text(encoding="utf-8").strip()
            if file_content:
                return file_content
        return stdout.strip()

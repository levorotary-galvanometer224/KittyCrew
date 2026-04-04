from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncIterator
from pathlib import Path

from kittycrew.models import AgentSession, ProviderModelOption, ProviderType
from kittycrew.providers.base import ProviderAdapter, ProviderExecutionError, ProviderExecutionHandle, ProviderStreamDelta


class OpenCodeAdapter(ProviderAdapter):
    provider = ProviderType.OPENCODE
    label = "OpenCode"
    summary = "OpenCode CLI"

    def command_candidates(self) -> tuple[str, ...]:
        override = os.getenv("KITTYCREW_OPENCODE_BIN")
        return tuple(candidate for candidate in (override, "opencode") if candidate)

    def build_command(self, binary: str, session: AgentSession, prompt: str) -> list[str]:
        command = [binary, "run", "--format", "json"]
        if session.model_id:
            command.extend(["--model", session.model_id])
        command.append(prompt)
        return command

    async def list_models(self) -> list[ProviderModelOption]:
        output = await self._read_models_output()
        model_ids: list[str] = []
        for line in output.splitlines():
            model_id = line.strip()
            if "/" not in model_id or model_id in model_ids:
                continue
            model_ids.append(model_id)
        return [ProviderModelOption(id=model_id, label=model_id) for model_id in model_ids]

    def build_environment(self, session: AgentSession) -> dict[str, str]:
        environment = super().build_environment(session)
        config_dir = Path(session.config_dir or self.runtime_dir(session) / "config")
        config_dir.mkdir(parents=True, exist_ok=True)

        xdg_root = config_dir / "opencode-xdg"
        data_home = xdg_root / "data"
        state_home = xdg_root / "state"
        cache_home = xdg_root / "cache"
        data_home.mkdir(parents=True, exist_ok=True)
        state_home.mkdir(parents=True, exist_ok=True)
        cache_home.mkdir(parents=True, exist_ok=True)

        environment["OPENCODE_CONFIG_DIR"] = str(config_dir)
        environment["XDG_DATA_HOME"] = str(data_home)
        environment["XDG_STATE_HOME"] = str(state_home)
        environment["XDG_CACHE_HOME"] = str(cache_home)
        environment["OPENCODE_DISABLE_CLAUDE_CODE"] = "1"
        environment["OPENCODE_DISABLE_CLAUDE_CODE_PROMPT"] = "1"
        environment["OPENCODE_DISABLE_CLAUDE_CODE_SKILLS"] = "1"

        self._write_config(config_dir)
        self._prepare_skills_dir(session, config_dir)
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
        command = self.build_command(binary, session, prompt)
        process = await self.spawn_process(command, session, handle=handle)

        assistant_text = ""

        while True:
            line = await process.stdout.readline()
            if not line:
                break

            text = self._extract_text_from_event(line.decode("utf-8", errors="replace").strip())
            if not text:
                continue

            assistant_text += text
            yield ProviderStreamDelta(mode="append", text=text)

        stderr = (await process.stderr.read()).decode("utf-8", errors="replace").strip()
        await process.wait()

        if process.returncode != 0:
            detail = stderr or f"{self.label} exited with code {process.returncode}."
            raise ProviderExecutionError(detail)

        if not assistant_text:
            detail = stderr or f"{self.label} returned an empty response."
            raise ProviderExecutionError(detail)

    async def _read_models_output(self) -> str:
        binary = self.resolve_command()
        if not binary:
            raise ProviderExecutionError(f"{self.label} CLI is not available on this machine.")

        runtime_root = self.project_root / "data" / "providers" / "opencode-models"
        config_dir = runtime_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        self._write_config(config_dir)

        env = os.environ.copy()
        env["OPENCODE_CONFIG_DIR"] = str(config_dir)
        env["XDG_DATA_HOME"] = str(runtime_root / "xdg" / "data")
        env["XDG_STATE_HOME"] = str(runtime_root / "xdg" / "state")
        env["XDG_CACHE_HOME"] = str(runtime_root / "xdg" / "cache")
        env["OPENCODE_DISABLE_CLAUDE_CODE"] = "1"
        env["OPENCODE_DISABLE_CLAUDE_CODE_PROMPT"] = "1"
        env["OPENCODE_DISABLE_CLAUDE_CODE_SKILLS"] = "1"
        for key in ("XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME"):
            Path(env[key]).mkdir(parents=True, exist_ok=True)

        process = await asyncio.create_subprocess_exec(
            binary,
            "models",
            cwd=str(self.project_root),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await process.communicate()
        if process.returncode != 0:
            detail = stderr_bytes.decode("utf-8", errors="replace").strip() or self.label
            raise ProviderExecutionError(f"Failed to inspect {self.label} models: {detail}")
        return stdout_bytes.decode("utf-8", errors="replace")

    def _prepare_skills_dir(self, session: AgentSession, config_dir: Path) -> None:
        selected_skills = self.selected_skills(session)
        if not selected_skills:
            return

        skills_dir = config_dir / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        for skill in selected_skills:
            source = Path(skill.path).resolve()
            target_dir = skills_dir / skill.name
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / "SKILL.md"
            if target.exists() or target.is_symlink():
                target.unlink()
            target.symlink_to(source)

    async def extract_content(self, session: AgentSession, stdout: str, stderr: str) -> str:
        del session, stderr
        text_parts = [
            text
            for line in stdout.splitlines()
            if (text := self._extract_text_from_event(line.strip()))
        ]
        return "".join(text_parts).strip()

    def _write_config(self, config_dir: Path) -> None:
        config_path = config_dir / "opencode.json"
        config = {
            "$schema": "https://opencode.ai/config.json",
            "permission": {
                "*": "allow",
            },
        }
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    def _extract_text_from_event(self, payload: str) -> str:
        if not payload:
            return ""
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            return ""

        if event.get("type") != "text":
            return ""
        part = event.get("part", {})
        if part.get("type") != "text":
            return ""
        return part.get("text", "")

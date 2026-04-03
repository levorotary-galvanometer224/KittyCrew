from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncIterator
import re

from kittycrew.models import AgentSession, ProviderModelOption, ProviderType, SkillOption
from kittycrew.providers.base import ProviderAdapter, ProviderExecutionError, ProviderExecutionHandle, ProviderStreamDelta


class ClaudeCodeAdapter(ProviderAdapter):
    provider = ProviderType.CLAUDE_CODE
    label = "Claude Code"
    summary = "Anthropic Claude Code CLI"

    def command_candidates(self) -> tuple[str, ...]:
        override = os.getenv("KITTYCREW_CLAUDE_BIN")
        return tuple(candidate for candidate in (override, "claude") if candidate)

    async def create_session(
        self,
        session_id: str,
        working_dir: str | None = None,
        skills: list[SkillOption] | None = None,
        skill_name: str | None = None,
        skill_path: str | None = None,
    ) -> AgentSession:
        session = await super().create_session(
            session_id,
            working_dir=working_dir,
            skills=skills,
            skill_name=skill_name,
            skill_path=skill_path,
        )
        session.native_session_id = session_id
        return session

    def build_command(self, binary: str, session: AgentSession, prompt: str) -> list[str]:
        command = [
            binary,
            "-p",
            "--output-format",
            "text",
            "--bare",
            "--no-session-persistence",
            "--dangerously-skip-permissions",
            "--add-dir",
            self.session_working_dir(session),
            "--",
            prompt,
        ]
        if session.model_id:
            command[1:1] = ["--model", session.model_id]
        return command

    async def list_models(self) -> list[ProviderModelOption]:
        help_text = await self._read_help_text()
        return self._parse_help_models(help_text)

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
        command = [
            binary,
            "-p",
            "--verbose",
            "--output-format",
            "stream-json",
            "--include-partial-messages",
            "--bare",
            "--no-session-persistence",
            "--dangerously-skip-permissions",
            "--add-dir",
            self.session_working_dir(session),
            "--",
            prompt,
        ]
        if session.model_id:
            command[1:1] = ["--model", session.model_id]
        process = await self.spawn_process(command, session, handle=handle)

        fallback_text = ""
        assistant_text = ""

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

            if event.get("type") == "assistant":
                content = event.get("message", {}).get("content", [])
                text_blocks = [block.get("text", "") for block in content if block.get("type") == "text"]
                if text_blocks:
                    fallback_text = "".join(text_blocks)
                continue

            if event.get("type") != "stream_event":
                continue

            stream_event = event.get("event", {})
            if stream_event.get("type") != "content_block_delta":
                continue

            delta = stream_event.get("delta", {})
            if delta.get("type") != "text_delta":
                continue

            text = delta.get("text", "")
            if not text:
                continue

            assistant_text += text
            yield ProviderStreamDelta(mode="append", text=text)

        stderr = (await process.stderr.read()).decode("utf-8", errors="replace").strip()
        await process.wait()

        if process.returncode != 0:
            detail = stderr or f"{self.label} exited with code {process.returncode}."
            raise ProviderExecutionError(detail)

        if not assistant_text and fallback_text:
            yield ProviderStreamDelta(mode="replace", text=fallback_text)
            assistant_text = fallback_text

        if not assistant_text:
            detail = stderr or f"{self.label} returned an empty response."
            raise ProviderExecutionError(detail)

    async def _read_help_text(self) -> str:
        binary = self.resolve_command()
        if not binary:
            raise ProviderExecutionError(f"{self.label} CLI is not available on this machine.")

        process = await asyncio.create_subprocess_exec(
            binary,
            "--help",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await process.communicate()
        if process.returncode != 0:
            detail = stderr_bytes.decode("utf-8", errors="replace").strip() or self.label
            raise ProviderExecutionError(f"Failed to inspect {self.label} models: {detail}")
        return stdout_bytes.decode("utf-8", errors="replace")

    def _parse_help_models(self, help_text: str) -> list[ProviderModelOption]:
        model_ids: list[str] = []
        for candidate in re.findall(r"claude-[a-z0-9.-]+", help_text):
            if candidate not in model_ids:
                model_ids.append(candidate)

        aliases = []
        if "sonnet" in help_text.lower():
            aliases.append("sonnet")
        if "opus" in help_text.lower():
            aliases.append("opus")
        if "haiku" in help_text.lower():
            aliases.append("haiku")

        for alias in aliases:
            if alias not in model_ids:
                model_ids.insert(0, alias)

        return [ProviderModelOption(id=model_id, label=model_id) for model_id in model_ids]

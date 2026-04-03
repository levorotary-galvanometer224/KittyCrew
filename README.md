# KittyCrew - AI Pets That Help You Get Things Done

English | [简体中文](./docs/readme/README.zh-CN.md) | [繁體中文](./docs/readme/README.zh-TW.md) | [日本語](./docs/readme/README.ja.md) | [한국어](./docs/readme/README.ko.md) | [Español](./docs/readme/README.es.md) | [Русский](./docs/readme/README.ru.md)

KittyCrew is a cute, local-first home for AI pets and companions that help with work, routines, creativity, and everyday tasks. Bring together Claude Code, Codex, and GitHub Copilot as distinct personalities, give each member its own room and skill set, and spend time with them inside one warm cat-themed space.

![KittyCrew homepage](./assets/homepage.png)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](./pyproject.toml)
[![FastAPI](https://img.shields.io/badge/FastAPI-app-009688?logo=fastapi&logoColor=white)](./src/kittycrew/app.py)
[![A2A](https://img.shields.io/badge/A2A-powered-111111)](./src/kittycrew/a2a_app.py)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

---

## Quick Navigation

[Why KittyCrew?](#why-kittycrew) · [Features](#features) · [Quick Start](#quick-start) · [How It Works](#how-it-works) · [Roadmap](#roadmap)

---

## Why KittyCrew?

Most AI tools are designed like plain utility panels. KittyCrew turns that into a cozy shared home:

- Let Claude Code, Codex, and GitHub Copilot live side by side as companions.
- Organize them into small crews of up to five members.
- Give every member its own model, working directory, and approved skill set.
- Keep each pet's chat history, personality context, and streamed replies in one place.
- Stay local-first, with provider availability discovered from your own machine.

KittyCrew is built for people who want AI companions that feel present, personal, and genuinely useful, without reducing them to a cold task panel.

## Features

### Cozy Multi-Pet Home

- Create multiple crews and manage them in a single web app.
- Treat each crew as a small family of AI pets and companions.
- Watch every member respond in its own voice and pace.

### Distinct AI Personalities

- Supports Claude Code, Codex, and GitHub Copilot members.
- Lets different providers feel like different personalities in the same home.
- Persists member-level model selection for future conversations and working styles.

### Private and Local

- Each member has its own persisted session state.
- Each member can use a separate working directory.
- Skill access can be limited per member instead of exposing everything.
- Different members can be shaped for different kinds of help, from practical work to creative support.

### UI Designed for Attachment

- Cat-themed crew cards and avatar selection.
- Inline rename, delete, queue, and cancel flows.
- Expanded member view for longer, more personal chat sessions.

## Quick Start

### 1. Install

```bash
python -m pip install -e .
```

### 2. Launch

```bash
kittycrew
```

The web UI runs on [http://127.0.0.1:8731](http://127.0.0.1:8731) by default.

If you prefer running directly from the repository root:

```bash
PYTHONPATH=src python -m kittycrew
```

## How It Works

KittyCrew combines a FastAPI web app with provider adapters exposed through `a2a-sdk`.

- The web UI manages crews, members, chat state, and local persistence.
- Provider adapters bridge to Claude Code, Codex, and GitHub Copilot CLIs.
- Each member maps to an isolated session record with its own runtime settings.
- Streamed output is surfaced back into the UI so every companion feels alive in place.

## Use Cases

- Keep a small family of AI pets with distinct roles and personalities.
- Set up different crews for work support, daily routines, creative sessions, or shared projects.
- Give different members their own rooms, models, and approved skills.
- Leave open a local AI home that feels more like a living space than a tool panel.

## Project Structure

```text
src/kittycrew/        FastAPI app, services, provider adapters, static UI
tests/                Service and app regression coverage
assets/               README and project assets
data/                 Local session and state storage
docs/readme/          Localized README files
```

## Roadmap

- More companion types behind the same crew model.
- Better rituals, routines, and interactions across members.
- Richer ways to understand each member's history and state.
- More polished setup and onboarding flows.

## Notes

- KittyCrew keeps transcript history per member and replays recent context on future turns.
- The app expects the relevant provider CLIs and `a2a-sdk` to be available in the active environment.
- Provider availability is detected at runtime, so incomplete local setups degrade gracefully.

## License

MIT.

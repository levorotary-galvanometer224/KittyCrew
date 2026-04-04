# KittyCrew - 能陪伴你也能帮你做事的 AI 宠物与伙伴

[English](../../README.md) | 简体中文 | [繁體中文](./README.zh-TW.md) | [日本語](./README.ja.md) | [한국어](./README.ko.md) | [Español](./README.es.md) | [Русский](./README.ru.md)

KittyCrew 是一个可爱、以本地优先为核心的 AI 宠物与伙伴之家。它们不只是陪伴你，也能帮助你处理工作、日常事务、创作和各种生活中的小任务。你可以把 Claude Code、Codex、GitHub Copilot、Kimi Code 和 OpenCode 当成不同性格的伙伴养在一起，为每个成员分配独立空间与技能集，并在一个猫咪主题的温馨界面里陪伴它们。

![KittyCrew homepage](../../assets/homepage.png)

---

## 快速导航

[为什么选择 KittyCrew？](#为什么选择-kittycrew) · [功能亮点](#功能亮点) · [快速开始](#快速开始) · [工作方式](#工作方式) · [路线图](#路线图)

---

## 为什么选择 KittyCrew？

大多数 AI 工具看起来都像冷冰冰的功能面板，KittyCrew 则把它变成了一个温馨的共享小家：

- 让 Claude Code、Codex、GitHub Copilot、Kimi Code 和 OpenCode 作为不同性格的伙伴住在一起。
- 以最多 5 名成员的小队形式组织你的宠物与伙伴。
- 为每个成员单独配置模型、工作目录和技能白名单。
- 在同一界面中保留成员级聊天历史、记忆上下文和流式回复。
- 以本地优先的方式运行，并从你的机器上自动检测可用 provider。

KittyCrew 适合希望把 AI 当作陪伴型伙伴来相处，同时也希望它们真正能帮自己做事，又不想失去本地控制力和细腻体验的用户。

## 功能亮点

### 温馨的多宠物之家

- 在一个 Web 应用中创建和管理多个 crew。
- 把每个 crew 视作一个由 AI 宠物和伙伴组成的小家庭。
- 独立查看每个成员的流式回应与状态。

### 不同性格的 AI 伙伴

- 支持 Claude Code、Codex、GitHub Copilot、Kimi Code 和 OpenCode 成员。
- 运行时自动检测本地 provider CLI。
- 支持按成员持久化模型选择，让每个伙伴保持自己的风格与做事方式。

### 本地而私密

- 每个成员都有独立持久化会话状态。
- 每个成员都可以绑定不同工作目录。
- 技能权限可按成员限制，而不是全部暴露。
- 你可以把不同成员培养成不同类型的帮手，覆盖工作、创作与日常支持。

### 为陪伴感设计的界面

- 猫咪主题卡片和头像选择。
- 内联重命名、删除、排队和取消操作。
- 提供更大的成员展开视图以承载更长、更贴近陪伴感的对话。

## 快速开始

### 1. 安装

```bash
python -m pip install -e .
```

### 2. 启动

```bash
kittycrew
```

默认会在 [http://127.0.0.1:8731](http://127.0.0.1:8731) 启动 Web UI。

如果你更想直接从仓库根目录运行：

```bash
PYTHONPATH=src python -m kittycrew
```

## 工作方式

KittyCrew 将 FastAPI Web 应用与通过 `a2a-sdk` 暴露的 provider 适配层结合在一起。

- Web UI 负责 crew、member、聊天状态和本地持久化。
- Provider 适配器负责桥接 Claude Code、Codex、GitHub Copilot、Kimi Code 和 OpenCode CLI。
- 每个成员都映射到带有独立运行配置的隔离会话记录。
- 流式输出会实时回传到界面中，让每个伙伴都像真实地陪在你身边。

## 适用场景

- 养一小群具有不同性格和职责的 AI 宠物与伙伴。
- 为工作支持、日常陪伴、创作习惯或生活场景设置不同 crew。
- 给不同成员安排不同房间、模型和技能白名单。
- 长期开着一个更像温馨小家，而不是工具面板的本地 AI 空间。

## 项目结构

```text
src/kittycrew/        FastAPI 应用、服务层、provider 适配器、静态界面
tests/                服务与应用回归测试
assets/               README 和项目素材
data/                 本地会话与状态存储
docs/readme/          多语言 README
```

## 路线图

- 在同一 crew 模型下支持更多伙伴类型。
- 增强成员之间的互动、日常和协作体验。
- 提供更丰富的成员历史与状态查看方式。
- 继续优化安装与上手体验。

## 说明

- KittyCrew 会按成员保存聊天历史，并在后续对话中回放最近上下文。
- 应用需要在当前环境中可用的 provider CLI 和 `a2a-sdk`。
- Provider 可用性在运行时检测，因此本地环境不完整时会尽量优雅降级。

## License

MIT。

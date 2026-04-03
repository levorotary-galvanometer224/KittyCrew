# KittyCrew - 能陪伴你也能幫你做事的 AI 寵物與夥伴

[English](../../README.md) | [简体中文](./README.zh-CN.md) | 繁體中文 | [日本語](./README.ja.md) | [한국어](./README.ko.md) | [Español](./README.es.md) | [Русский](./README.ru.md)

KittyCrew 是一個可愛、以本地優先為核心的 AI 寵物與夥伴之家。它們不只是陪伴你，也能幫助你處理工作、日常事務、創作與生活裡的各種小任務。你可以把 Claude Code、Codex 與 GitHub Copilot 當成不同性格的夥伴養在一起，替每位成員配置獨立空間與技能集，並在同一個貓咪主題的溫馨介面裡陪伴它們。

![KittyCrew homepage](../../assets/homepage.png)

---

## 快速導覽

[為什麼選擇 KittyCrew？](#為什麼選擇-kittycrew) · [功能亮點](#功能亮點) · [快速開始](#快速開始) · [運作方式](#運作方式) · [路線圖](#路線圖)

---

## 為什麼選擇 KittyCrew？

多數 AI 工具看起來都像冷冰冰的功能面板，KittyCrew 則把它變成一個溫馨的共享小家：

- 讓 Claude Code、Codex 與 GitHub Copilot 以不同性格的夥伴身份住在一起。
- 以最多 5 名成員的小隊形式組織你的寵物與夥伴。
- 為每位成員單獨配置模型、工作目錄與技能白名單。
- 在同一個介面中保留成員級聊天紀錄、記憶上下文與串流回覆。
- 採本地優先運行，並從你的電腦自動偵測可用 provider。

KittyCrew 適合希望把 AI 當成陪伴型夥伴來相處，同時也希望它們真正能幫自己做事，又不想失去本地控制力與細膩體驗的使用者。

## 功能亮點

### 溫馨的多寵物之家

- 在一個 Web 應用中建立與管理多個 crew。
- 把每個 crew 視為一個由 AI 寵物與夥伴組成的小家庭。
- 獨立觀察每位成員的串流回應與狀態。

### 不同性格的 AI 夥伴

- 支援 Claude Code、Codex 與 GitHub Copilot 成員。
- 執行時自動偵測本地 provider CLI。
- 支援以成員為單位持久化模型選擇，讓每位夥伴保有自己的風格與做事方式。

### 本地而私密

- 每位成員都有獨立持久化會話狀態。
- 每位成員都可以綁定不同工作目錄。
- 技能權限可依成員限制，而不是全部開放。
- 你可以把不同成員培養成不同類型的幫手，涵蓋工作、創作與日常支持。

### 為陪伴感設計的介面

- 貓咪主題卡片與頭像選擇。
- 內嵌重新命名、刪除、排隊與取消操作。
- 提供更大的成員展開視圖以承載更長、更貼近陪伴感的對話。

## 快速開始

### 1. 安裝

```bash
python -m pip install -e .
```

### 2. 啟動

```bash
kittycrew
```

預設會在 [http://127.0.0.1:8731](http://127.0.0.1:8731) 啟動 Web UI。

如果你想直接從儲存庫根目錄執行：

```bash
PYTHONPATH=src python -m kittycrew
```

## 運作方式

KittyCrew 將 FastAPI Web 應用與透過 `a2a-sdk` 暴露的 provider 適配層結合在一起。

- Web UI 負責 crew、member、聊天狀態與本地持久化。
- Provider 適配器負責橋接 Claude Code、Codex 與 GitHub Copilot CLI。
- 每位成員都會映射到帶有獨立執行設定的隔離會話紀錄。
- 串流輸出會即時回傳到介面中，讓每位夥伴都像真實地陪在你身邊。

## 適用情境

- 養一小群擁有不同性格與角色的 AI 寵物與夥伴。
- 為工作支持、日常陪伴、創作習慣或生活場景設定不同 crew。
- 給不同成員安排不同房間、模型與技能白名單。
- 長期開著一個更像溫馨小家，而不是工具面板的本地 AI 空間。

## 專案結構

```text
src/kittycrew/        FastAPI 應用、服務層、provider 適配器、靜態介面
tests/                服務與應用回歸測試
assets/               README 與專案素材
data/                 本地會話與狀態儲存
docs/readme/          多語言 README
```

## 路線圖

- 在同一 crew 模型下支援更多夥伴類型。
- 增強成員之間的互動、日常與協作體驗。
- 提供更豐富的成員歷史與狀態檢視方式。
- 持續優化安裝與上手體驗。

## 說明

- KittyCrew 會依成員保存聊天紀錄，並在後續對話中回放最近上下文。
- 應用需要在目前環境中可用的 provider CLI 與 `a2a-sdk`。
- Provider 可用性會在執行時偵測，因此本地環境不完整時會盡量優雅降級。

## License

MIT。

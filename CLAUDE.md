# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

SRT 字幕**翻译 + 润色修复**工具，针对 AV/口语化对白场景做了 prompt 定制（语气词规则、敏感内容占位符等）。

应用为 **`web_app.py`（FastAPI 网页版）**，默认使用 **xAI Grok**（`grok-4`，OpenAI 兼容接口 `https://api.x.ai/v1`）。

## 运行与开发

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe web_app.py    # 启动后访问 http://127.0.0.1:8000
```

- 依赖见 `requirements.txt`（fastapi / uvicorn / openai / python-multipart）。
- 运行时产物（脚本同目录）：`translator.log`（日志）、`config.json`（配置，由设置弹窗写入）。
- 没有测试框架。快速冒烟测试用 FastAPI `TestClient`（见下方），注意 Windows 控制台需 `python -X utf8` 才能正确显示中日文。

## 架构（`web_app.py` + `static/index.html`）

后端单文件 `web_app.py`，前端单文件 `static/index.html`（内嵌 CSS/JS，由 `GET /` 直接读文件返回）。

1. **配置层** — `Config` dataclass + `load_config()`/`save_config()`，持久化到 `config.json`。默认 `base_url=https://api.x.ai/v1`、`model=grok-4`。
2. **SRT I/O** — `parse_srt_text()` / `build_srt()` + `SubtitleCue` dataclass。三态文本：`original`→`translation`→`fixed_text`，导出优先级 `fixed_text or translation or original`。
3. **翻译核心** — `WebSocket /ws/translate`：`Semaphore(MAX_CONCURRENCY=8)` 控 8 路并发 + `asyncio.as_completed` **逐行即时回填**（每完成一行就推 `row`/`progress`/`tokens` 消息，前端 JS 即时刷新对应表格行，而非等全部完成）。两种 `mode`：
   - `translate`：用 `PROMPT_TRANSLATE`。
   - `fix`：用 `PROMPT_FIX` 润色；若源文本含「无法翻译/【违规内容」标记，改用带额外指令的 fallback prompt 重新直译。
   - `_extract()` 统一解析三种返回形态（SDK 对象 / dict / 纯文本），对 HTML 响应抛错（提示 base_url/token 配错）。
4. **状态** — 进程内单用户全局 `state`（`AppState`：cues / 撤销历史 history / token 计数），对应桌面版的单窗口状态。多标签页会共享同一份字幕。

**REST 端点**：`/api/config`（GET/POST）、`/api/upload`、`/api/cues`、`/api/cues/{idx}`（内联编辑保存）、`/api/restore/{idx}`、`/api/undo`、`/api/export`。

### 易踩的坑

- **导出文件名含中文**：HTTP 头只允许 latin-1，文件名用 RFC 5987 `filename*=UTF-8''...` 编码（见 `export()`），不要直接塞中文进 `Content-Disposition`。
- Grok 与 OpenAI 完全兼容，仍用 `openai` SDK 的 `AsyncOpenAI`，只是 `base_url` 指向 x.ai。

## 前端

`static/index.html` 单文件（内嵌 CSS/JS，无构建步骤、无框架）。设计要点：顶栏品牌 + token chips + 设置齿轮；工具栏（打开/翻译/修复/撤销/导出，翻译为主色按钮）；顶部细进度条；表格卡片支持**拖拽 .srt 上传**、单元格 `contenteditable` 内联编辑（blur 时 POST 保存）、行更新 flash 动画；右下角 toast 通知（替代原来的 alert/状态栏）。改 UI 时注意元素 id 要与底部 `<script>` 中引用的保持一致。

## 其他

- `ec_work_config/`：无关的第三方 android CLI 工具，未纳入版本控制。

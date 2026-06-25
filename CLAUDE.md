# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

SRT 字幕**翻译 + 润色修复**工具，针对 AV/口语化对白场景做了 prompt 定制（语气词规则、敏感内容占位符等）。

应用为 **`web_app.py`（FastAPI 网页版）**，默认使用 **xAI Grok**（`grok-4`，OpenAI 兼容接口 `https://api.x.ai/v1`）。

另集成**本地转写流水线**：视频/音频 → Demucs 提取人声 → Faster-Whisper（默认 `large-v3`，语言 `ja`）→ 生成 SRT 原文 → 再走 Grok 翻译/修复 → 中文 SRT。

## 运行与开发

```powershell
# RTX 50 系（Blackwell, sm_120）必须用 CUDA 12.8 版 torch，先单独装：
.\.venv\Scripts\python.exe -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe web_app.py    # 启动后访问 http://127.0.0.1:8000
```

- 依赖见 `requirements.txt`（fastapi / uvicorn / openai / python-multipart / faster-whisper / demucs）。
- 运行时产物（脚本同目录）：`translator.log`（日志）、`config.json`（配置，由设置弹窗写入）、`media_tmp/`（上传的视频/音频）、`work_tmp/`（音轨与人声中间 wav）。
- 没有测试框架。快速冒烟测试用 FastAPI `TestClient`（见下方），注意 Windows 控制台需 `python -X utf8` 才能正确显示中日文。

## 架构（`web_app.py` + `static/index.html`）

后端单文件 `web_app.py`，前端单文件 `static/index.html`（内嵌 CSS/JS，由 `GET /` 直接读文件返回）。

1. **配置层** — `Config` dataclass + `load_config()`/`save_config()`，持久化到 `config.json`。默认 `base_url=https://api.x.ai/v1`、`model=grok-4`。
2. **SRT I/O** — `parse_srt_text()` / `build_srt()` + `SubtitleCue` dataclass。三态文本：`original`→`translation`→`fixed_text`，导出优先级 `fixed_text or translation or original`。
3. **翻译核心** — `WebSocket /ws/translate`：`Semaphore(cfg.concurrency)` 控并发（配置项，默认 10，上限 32，设置弹窗可调）+ `asyncio.as_completed` **逐行即时回填**（每完成一行就推 `row`/`progress`/`tokens` 消息，前端 JS 即时刷新对应表格行，而非等全部完成）。两种 `mode`：
   - 请求参数 `only_missing: true` 为「继续」模式：translate 只处理译文为空的行，fix 只处理 fixed_text 为空的行（前端「继续」按钮自动判断该续译还是续修）。
   - 所有逐句请求的 user 消息都经 `with_context()` 包装：【位置】（第 x/n 行 + 全片百分比，用于对应背景档案的场景分割）+【前文】【后文】各 2 句 +【当前句】；translate/fallback 的上下文用原文（`original_only=True`），fix 用译文。
   - `translate`：`PROMPT_TRANSLATE` 为 AV 对白定制：呻吟/语气词规范（啊～风格）、常见表达惯例（気持ちいい/イく/だめ/やめて 等）、称呼亲昵化、按说话人身份定语气。
   - `fix`：**两阶段**。先把整部字幕发给模型（`PROMPT_STORY`）生成详尽「剧情背景档案」——核心是**场景分割**（每个场景的位置区间百分比/地点/在场人物/对白基调），另含作品类型、人物称呼表、语气走向、统一用语表、易错提醒（建议 1500 字+，不设上限）；档案拼进 `PROMPT_FIX` 的 system prompt，润色时模型先按【位置】定位场景与台词类型再下笔。背景分析失败则降级为无背景的常规修复。若源文本含「无法翻译/【违规内容」标记，改用带额外指令的 fallback prompt（同样附带背景）重新直译。
   - `_extract()` 统一解析三种返回形态（SDK 对象 / dict / 纯文本），对 HTML 响应抛错（提示 base_url/token 配错）。
4. **本地转写** — `POST /api/upload_media`（流式落盘到 `media_tmp/`）+ `WebSocket /ws/transcribe`。流水线在后台线程跑（阻塞型 CPU/GPU 任务），用 `asyncio.Queue` + `call_soon_threadsafe` 把进度/分段结果推回事件循环，再经 WS 逐段回填前端（消息类型：`stage`/`asr_row`/`progress`/`finished`/`error`）：
   - **音轨提取** `extract_audio_wav()`：用 PyAV（faster-whisper 自带）解码任意视频/音频 → 44.1kHz 立体声 wav，**不依赖系统 ffmpeg**。
   - **人声分离** `separate_vocals()`：走 demucs Python API（`get_model` + `apply_model`，两轨 vocals 模式），**故意避开 demucs CLI**（其文件 I/O 依赖 torchaudio 后端/ffmpeg，Windows 上不可靠）；wav 读写用标准库 `wave`。
   - **转写** `get_whisper_model()` 全局缓存模型实例（按 model+device 为 key）；`transcribe(vad_filter=True, condition_on_previous_text=False)`（口语对白防幻觉重复），segments 为生成器，逐段转成 `SubtitleCue`（`_sec_to_ts()` 秒→SRT 时间戳）。
   - 相关配置：`whisper_model`/`whisper_device`(auto/cuda/cpu)/`transcribe_lang`(空=自动)/`use_demucs`/`demucs_model`。
5. **状态** — 进程内单用户全局 `state`（`AppState`：cues / 撤销历史 history / token 计数 / media_path），对应桌面版的单窗口状态。多标签页会共享同一份字幕。

**REST 端点**：`/api/config`（GET/POST）、`/api/upload`、`/api/upload_media`、`/api/cues`、`/api/cues/{idx}`（内联编辑保存）、`/api/restore/{idx}`、`/api/undo`、`/api/export`。

### 易踩的坑

- **导出文件名含中文**：HTTP 头只允许 latin-1，文件名用 RFC 5987 `filename*=UTF-8''...` 编码（见 `export()`），不要直接塞中文进 `Content-Disposition`。
- Grok 与 OpenAI 完全兼容，仍用 `openai` SDK 的 `AsyncOpenAI`，只是 `base_url` 指向 x.ai。

## 前端

`static/index.html` 单文件（内嵌 CSS/JS，无构建步骤、无框架）。设计要点：顶栏品牌 + token chips + 设置齿轮；工具栏（打开/翻译/修复/撤销/导出，翻译为主色按钮）；顶部细进度条；表格卡片支持**拖拽 .srt 上传**、单元格 `contenteditable` 内联编辑（blur 时 POST 保存）、行更新 flash 动画；右下角 toast 通知（替代原来的 alert/状态栏）。改 UI 时注意元素 id 要与底部 `<script>` 中引用的保持一致。

## 其他

- `ec_work_config/`：无关的第三方 android CLI 工具，未纳入版本控制。

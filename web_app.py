# -*- coding: utf-8 -*-
"""
AI SRT Translator —— 网页版 (FastAPI + Grok)
------------------------------------------------------------
• 由原 PySide6 桌面版迁移而来，去掉 Qt，改为浏览器界面
• 默认使用 xAI Grok（OpenAI 兼容接口，base_url=https://api.x.ai/v1，模型 grok-4）
• 保留全部功能：翻译 / 润色修复 / 撤销 / token 统计 / 配置持久化 /
  8 路并发 + 逐行即时回填（通过 WebSocket 推送）/ 导出 SRT
"""

import sys
import io
import json
import logging
import asyncio
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from openai import AsyncOpenAI

# -------- logging --------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout),
              logging.FileHandler("translator.log", encoding="utf-8")]
)
log = logging.getLogger("translator")

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
INDEX_PATH = BASE_DIR / "static" / "index.html"

# 默认指向 xAI Grok
DEFAULT_BASE_URL = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-4"

MAX_CONCURRENCY = 8


# -------- config persistence --------
@dataclass
class Config:
    api_key: str = ""
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    target_lang: str = "中文"


def load_config() -> Config:
    cfg = Config()
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            cfg.api_key = data.get("api_key", "")
            cfg.base_url = data.get("base_url", "") or DEFAULT_BASE_URL
            cfg.model = data.get("model", cfg.model) or DEFAULT_MODEL
            cfg.target_lang = data.get("target_lang", cfg.target_lang)
            log.info(f"Config loaded from {CONFIG_PATH}")
        except Exception as e:
            log.warning(f"读取配置失败: {e}")
    return cfg


def save_config(cfg: Config):
    try:
        CONFIG_PATH.write_text(
            json.dumps(asdict(cfg), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        log.info(f"配置已保存到 {CONFIG_PATH}")
    except Exception as e:
        log.error(f"写入配置失败: {e}")


# -------- data --------
@dataclass
class SubtitleCue:
    index: int
    start: str
    end: str
    original: str
    translation: str = ""
    fixed_text: str = ""


# -------- srt I/O --------
def parse_srt_text(text: str) -> List[SubtitleCue]:
    cues: List[SubtitleCue] = []
    blk: List[str] = []

    def flush(blk):
        if len(blk) >= 3 and " --> " in blk[1]:
            try:
                idx = int(blk[0].strip())
            except ValueError:
                return
            s, _, e = blk[1].partition(" --> ")
            cues.append(SubtitleCue(idx, s.strip(), e.strip(), "\n".join(blk[2:])))

    for ln in text.splitlines():
        if ln.strip():
            blk.append(ln.rstrip("\n"))
        else:
            flush(blk)
            blk = []
    flush(blk)
    return cues


def build_srt(cues: List[SubtitleCue]) -> str:
    out = io.StringIO()
    for c in cues:
        txt = c.fixed_text or c.translation or c.original
        out.write(f"{c.index}\n{c.start} --> {c.end}\n{txt}\n\n")
    return out.getvalue()


# -------- prompts (沿用桌面版) --------
PROMPT_TRANSLATE = (
    "你是一名专业字幕翻译。请将用户提供的字幕句子翻译成{lang}，口语自然、符合日语对白风格。\n"
    "规则：①如整句为无法翻译的语气词/拟声词/“晚安”→输出“啊～～”；\n"
    "②若原句仅含单字“啊”→输出“啊～”；③其余正常翻译；只输出翻译文本，禁止附带说明。"
)

PROMPT_FIX = (
    "你是一名具有 10 年以上经验的合法商业 AV 字幕润色助手。"
    "在绝不改变原意的前提下，请修正病句、口语化表达和多余重复，使语句更贴合 AV 场景的自然对白。\n"
    "请遵循以下规则：\n"
    "1. 若原句已自然流畅且符合场景，请原样输出；\n"
    "2. 若需润色，仅输出润色后的字幕文本，不得附带任何解释或标注。"
)


def _extract(resp):
    """统一解析不同 SDK / 网关返回。"""
    if hasattr(resp, "choices"):
        content = resp.choices[0].message.content or ""
        return content.strip(), resp.usage.prompt_tokens, resp.usage.completion_tokens

    if isinstance(resp, dict) and "choices" in resp:
        usage = resp.get("usage", {})
        message = resp["choices"][0].get("message", {})
        content = (message.get("content") if isinstance(message, dict) else message) or ""
        return content.strip(), usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)

    text = str(resp or "").strip()
    if text.lower().startswith("<!doctype") or "<html" in text.lower():
        raise ValueError("收到 HTML — base_url 或 Token 可能配置错误")
    return text, 0, 0


# -------- 进程内单用户状态（对应桌面版单窗口状态） --------
class AppState:
    def __init__(self):
        self.cues: List[SubtitleCue] = []
        self.history: List[List[SubtitleCue]] = []
        self.current_filename: Optional[str] = None
        self.ptok = 0
        self.ctok = 0


state = AppState()
app = FastAPI(title="AI 字幕翻译器 (Grok 网页版)")


def cues_payload():
    return [asdict(c) for c in state.cues]


# -------- 页面 --------
@app.get("/", response_class=HTMLResponse)
async def index():
    return INDEX_PATH.read_text(encoding="utf-8")


# -------- 配置 --------
@app.get("/api/config")
async def get_config():
    return asdict(load_config())


@app.post("/api/config")
async def post_config(payload: dict):
    cfg = Config(
        api_key=(payload.get("api_key") or "").strip(),
        base_url=(payload.get("base_url") or DEFAULT_BASE_URL).strip(),
        model=(payload.get("model") or DEFAULT_MODEL).strip(),
        target_lang=(payload.get("target_lang") or "中文").strip(),
    )
    save_config(cfg)
    return asdict(cfg)


# -------- SRT 文件 --------
@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    raw = await file.read()
    text = raw.decode("utf-8", errors="ignore")
    state.cues = parse_srt_text(text)
    state.history.clear()
    state.current_filename = file.filename
    return {"filename": file.filename, "cues": cues_payload()}


@app.get("/api/cues")
async def get_cues():
    return {"filename": state.current_filename, "cues": cues_payload()}


@app.post("/api/cues/{idx}")
async def update_cue(idx: int, payload: dict):
    """内联编辑：更新某一行的译文/修复后文本（可编辑表格）。"""
    if not (0 <= idx < len(state.cues)):
        return JSONResponse({"error": "索引越界"}, status_code=400)
    cue = state.cues[idx]
    if "translation" in payload:
        cue.translation = payload["translation"]
    if "fixed_text" in payload:
        cue.fixed_text = payload["fixed_text"]
    return asdict(cue)


@app.post("/api/restore/{idx}")
async def restore_cue(idx: int):
    if not (0 <= idx < len(state.cues)):
        return JSONResponse({"error": "索引越界"}, status_code=400)
    state.cues[idx].translation = ""
    state.cues[idx].fixed_text = ""
    return asdict(state.cues[idx])


@app.post("/api/undo")
async def undo():
    if state.history:
        state.cues = state.history.pop()
    return {"cues": cues_payload()}


@app.get("/api/export")
async def export():
    if not state.cues:
        return JSONResponse({"error": "没有可导出的字幕"}, status_code=400)
    name = "translated"
    if state.current_filename:
        name = Path(state.current_filename).stem + "_翻译后"
    content = build_srt(state.cues)
    # 文件名可能含中文，HTTP 头只允许 latin-1 → 用 RFC 5987 的 filename* 编码
    from urllib.parse import quote
    fname = f"{name}.srt"
    headers = {
        "Content-Disposition": f"attachment; filename=subtitle.srt; "
                               f"filename*=UTF-8''{quote(fname)}"
    }
    return StreamingResponse(io.BytesIO(content.encode("utf-8")),
                             media_type="application/x-subrip", headers=headers)


# -------- 翻译 / 修复（WebSocket 逐行即时回填） --------
@app.websocket("/ws/translate")
async def ws_translate(ws: WebSocket):
    await ws.accept()
    try:
        msg = await ws.receive_json()
        mode = msg.get("mode", "translate")
        cfg = load_config()

        if not state.cues:
            await ws.send_json({"type": "error", "message": "请先加载 SRT"})
            return
        if not cfg.api_key:
            await ws.send_json({"type": "error", "message": "请先在设置里填写 API Key"})
            return

        # 压入撤销历史
        state.history.append([SubtitleCue(**vars(c)) for c in state.cues])
        state.ptok = state.ctok = 0

        client = AsyncOpenAI(api_key=cfg.api_key, base_url=cfg.base_url or None)
        sem = asyncio.Semaphore(MAX_CONCURRENCY)
        total = len(state.cues)

        async def handle(idx: int, cue: SubtitleCue):
            async with sem:
                try:
                    if mode == "translate":
                        rsp = await client.chat.completions.create(
                            model=cfg.model,
                            messages=[
                                {"role": "system",
                                 "content": PROMPT_TRANSLATE.format(lang=cfg.target_lang)},
                                {"role": "user", "content": cue.original},
                            ],
                            timeout=60,
                        )
                        txt, pt, ct = _extract(rsp)
                        cue.translation = txt
                        cue.fixed_text = ""
                    else:
                        source = cue.translation or cue.original
                        if any(bad in source for bad in ("无法翻译", "【违规内容")):
                            fallback_prompt = (
                                PROMPT_TRANSLATE.format(lang=cfg.target_lang)
                                + "\n【额外指令】请保持直译风格，避免润色和主观扩写；"
                                  "若出现敏感内容请用 ♪♪ 占位。"
                            )
                            rsp = await client.chat.completions.create(
                                model=cfg.model,
                                messages=[
                                    {"role": "system", "content": fallback_prompt},
                                    {"role": "user", "content": cue.original},
                                ],
                                timeout=60,
                            )
                            txt, pt, ct = _extract(rsp)
                            cue.translation = txt
                            cue.fixed_text = ""
                        else:
                            rsp = await client.chat.completions.create(
                                model=cfg.model,
                                messages=[
                                    {"role": "system", "content": PROMPT_FIX},
                                    {"role": "user", "content": source},
                                ],
                                timeout=60,
                            )
                            txt, pt, ct = _extract(rsp)
                            cue.fixed_text = txt

                    state.ptok += pt
                    state.ctok += ct
                    return idx, True, ""
                except Exception as e:
                    return idx, False, str(e)

        tasks = [handle(i, c) for i, c in enumerate(state.cues)]
        done = 0
        for coro in asyncio.as_completed(tasks):
            idx, ok, err = await coro
            if not ok:
                await ws.send_json({"type": "error", "message": f"第 {idx + 1} 行: {err}"})
                continue
            cue = state.cues[idx]
            await ws.send_json({
                "type": "row", "idx": idx,
                "translation": cue.translation, "fixed_text": cue.fixed_text,
            })
            done += 1
            await ws.send_json({"type": "progress", "done": done, "total": total})
            await ws.send_json({"type": "tokens", "ptok": state.ptok, "ctok": state.ctok})

        await ws.send_json({"type": "finished", "mode": mode})
    except WebSocketDisconnect:
        log.info("WebSocket 客户端断开")
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


def main():
    import uvicorn
    log.info("启动网页服务: http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()

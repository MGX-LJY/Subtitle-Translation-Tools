# -*- coding: utf-8 -*-
"""
AI SRT Translator —— 网页版 (FastAPI + Grok)
------------------------------------------------------------
• 由原 PySide6 桌面版迁移而来，去掉 Qt，改为浏览器界面
• 默认使用 xAI Grok（OpenAI 兼容接口，base_url=https://api.x.ai/v1，模型 grok-4）
• 保留全部功能：翻译 / 润色修复 / 撤销 / token 统计 / 配置持久化 /
  8 路并发 + 逐行即时回填（通过 WebSocket 推送）/ 导出 SRT
• 本地转写流水线：视频/音频 → Demucs 提取人声 → Faster-Whisper 转写
  → 生成 SRT 字幕（原文列）→ 再走 Grok 翻译/修复
"""

import sys
import io
import json
import wave
import shutil
import logging
import asyncio
import threading
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

DEFAULT_CONCURRENCY = 10


# -------- config persistence --------
@dataclass
class Config:
    api_key: str = ""
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    target_lang: str = "中文"
    concurrency: int = DEFAULT_CONCURRENCY   # 翻译/修复的并发请求数
    # ---- 本地转写（Demucs + Faster-Whisper）----
    whisper_model: str = "large-v3"
    whisper_device: str = "auto"      # auto / cuda / cpu
    transcribe_lang: str = "ja"       # 空字符串 = 自动检测
    use_demucs: bool = True
    demucs_model: str = "htdemucs"


def load_config() -> Config:
    cfg = Config()
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            cfg.api_key = data.get("api_key", "")
            cfg.base_url = data.get("base_url", "") or DEFAULT_BASE_URL
            cfg.model = data.get("model", cfg.model) or DEFAULT_MODEL
            cfg.target_lang = data.get("target_lang", cfg.target_lang)
            try:
                cfg.concurrency = max(1, min(32, int(data.get("concurrency", cfg.concurrency))))
            except (TypeError, ValueError):
                cfg.concurrency = DEFAULT_CONCURRENCY
            cfg.whisper_model = data.get("whisper_model", cfg.whisper_model) or "large-v3"
            cfg.whisper_device = data.get("whisper_device", cfg.whisper_device) or "auto"
            cfg.transcribe_lang = data.get("transcribe_lang", cfg.transcribe_lang)
            cfg.use_demucs = bool(data.get("use_demucs", cfg.use_demucs))
            cfg.demucs_model = data.get("demucs_model", cfg.demucs_model) or "htdemucs"
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
    "你是一名资深成人影片（AV）字幕翻译，精通日语口语和成人场景对白。"
    "请将【当前句】翻译成{lang}。译文必须是地道的口语，贴合成人影片对白的语感——"
    "直接、自然、有情绪，绝不能有书面腔或机翻腔。\n"
    "【语气词与呻吟】\n"
    "1. 整句仅为呻吟/喘息/拟声词/无实义语气词（如あっ、んっ、はぁ、うぅ）或“晚安”→ 统一输出“啊～～”；\n"
    "2. 原句仅含单字“啊”→ 输出“啊～”；\n"
    "3. 句中夹杂的呻吟用“啊～”“嗯～”表示，拖长音用“～”，不要写成“啊啊啊”。\n"
    "【用语习惯】\n"
    "4. 常见表达按成人片惯例意译：気持ちいい→好舒服；イく/いっちゃう→要去了；"
    "だめ→不行/不可以（看语气）；やめて→不要/住手（分清是真抗拒还是娇嗔）；すごい→好厉害；\n"
    "5. 称呼保留亲昵感：お兄ちゃん→哥哥、先生→老师、先輩→前辈、おじさん→大叔、ご主人様→主人；\n"
    "6. 人称和语气要符合说话人身份与当下情境（女方多娇柔/羞涩/沉浸，男方多主导/调侃/命令）。\n"
    "【输出】\n"
    "7. 语音识别的原文可能带少量错字或重复，按语境理解后翻译本意；\n"
    "8. 译文简短有力，适合字幕显示；\n"
    "9. 用户消息中的【前文】【后文】【位置】仅用于理解语境，绝不要输出它们；"
    "只输出【当前句】的译文本身，不得附带任何解释、引号或标注。"
)

PROMPT_FIX = (
    "你是一名具有 10 年以上经验的合法商业成人影片（AV）字幕润色师。"
    "你的任务：在绝不改变原意的前提下，把机翻腔、病句、生硬书面语修成地道自然的成人片口语对白。\n"
    "【判断语境】先结合剧情背景档案中的场景分割和用户消息给出的【位置】，判断当前句落在哪个场景、"
    "属于什么类型的台词（采访问答/日常对话/调情挑逗/指令命令/呻吟喘息/沉浸表达/事后对话），再按该语境润色。\n"
    "【润色要点】\n"
    "1. 人称与称呼严格按背景档案的统一用语表执行，不得忽男忽女、忽你忽您；\n"
    "2. 语气强度贴合场景：拘谨阶段含蓄、沉浸阶段直接；“不要”是真抗拒还是娇嗔，要看前后文和所在场景；\n"
    "3. 呻吟语气词统一为“啊～”“嗯～”风格，拖长音用“～”，不要写成“啊啊啊”；\n"
    "4. 删去机器残留的重复词句，修通指代不明的句子，保持与前后句衔接连贯；\n"
    "5. 译文简短有力，适合字幕显示，禁止书面语；\n"
    "6. 若原句已自然流畅且符合场景，原样输出。\n"
    "【输出】用户消息中的【前文】【后文】【位置】仅用于理解语境，绝不要把它们输出出来；"
    "只输出【当前句】润色后的字幕文本，不得附带任何解释或标注。"
)

# 修复前的剧情通读：生成详尽的「剧情背景档案」注入到逐句润色的 system prompt 里
PROMPT_STORY = (
    "你是一名成人影片（AV）字幕剧情分析师。下面是一部影片的完整字幕台词（按时间顺序）。"
    "请通读全部内容后，输出一份详尽的《剧情背景档案》，供后续逐句润色字幕的 AI 作为上下文参考。"
    "后续润色时每句话都会附带它在全片中的位置百分比，所以场景分割务必标清位置区间。"
    "请严格按以下结构输出，写得越具体越好（不设字数上限，建议 1500 字以上）：\n"
    "【作品类型】判断题材与基调（剧情向/纪实采访向/纯本番；纯爱/调教/人妻/校园等），以及大致的叙事结构；\n"
    "【场景分割】最重要的部分。把全片切分成若干场景，逐一列出——\n"
    "  场景N（约位于全片 x%～y%）：地点｜在场人物｜事件概要｜对白基调"
    "（采访问答/日常聊天/调情挑逗/前戏/本番以呻吟为主/事后对话等）；\n"
    "【人物档案】每个出场人物：身份、性格、说话习惯、口头禅；以及他们彼此之间的称呼——谁叫谁什么，务必逐一列出；\n"
    "【语气与文体】各人物的语气特点；情绪随场景推进的变化（如拘谨→放开→沉浸）；呻吟与对白比例的变化；\n"
    "【统一用语表】全片必须保持一致的称呼、专有名词、反复出现的关键短语及其固定说法；\n"
    "【易错提醒】逐句润色时容易出错的点：人称指代不明的句子、语气强度容易拿捏错的台词（真抗拒还是娇嗔）、"
    "前后呼应的台词、采访段与本番段容易混淆的句子。\n"
    "只输出档案本身，不要附带任何其他说明。"
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
        self.media_path: Optional[str] = None    # 待转写的视频/音频
        self.media_name: Optional[str] = None


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
    lang = payload.get("transcribe_lang")
    try:
        concurrency = max(1, min(32, int(payload.get("concurrency", DEFAULT_CONCURRENCY))))
    except (TypeError, ValueError):
        concurrency = DEFAULT_CONCURRENCY
    cfg = Config(
        api_key=(payload.get("api_key") or "").strip(),
        base_url=(payload.get("base_url") or DEFAULT_BASE_URL).strip(),
        model=(payload.get("model") or DEFAULT_MODEL).strip(),
        target_lang=(payload.get("target_lang") or "中文").strip(),
        concurrency=concurrency,
        whisper_model=(payload.get("whisper_model") or "large-v3").strip(),
        whisper_device=(payload.get("whisper_device") or "auto").strip(),
        transcribe_lang=(lang if lang is not None else "ja").strip(),
        use_demucs=bool(payload.get("use_demucs", True)),
        demucs_model=(payload.get("demucs_model") or "htdemucs").strip(),
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


# -------- 本地转写：视频 → Demucs 人声 → Faster-Whisper → SRT --------
MEDIA_DIR = BASE_DIR / "media_tmp"   # 上传的视频/音频
WORK_DIR = BASE_DIR / "work_tmp"     # 中间产物（音轨 / 人声 wav）


def _sec_to_ts(sec: float) -> str:
    """秒 → SRT 时间戳 HH:MM:SS,mmm"""
    ms = max(0, int(round(sec * 1000)))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def extract_audio_wav(src: str, dst: str, rate: int = 44100, progress_cb=None):
    """用 PyAV（faster-whisper 自带）把视频/音频解码成 44.1kHz 立体声 wav，
    免去系统安装 ffmpeg。progress_cb(done_sec, total_sec) 约每 1% 回调一次。"""
    import av
    with av.open(src) as ic:
        stream = next((s for s in ic.streams if s.type == "audio"), None)
        if stream is None:
            raise ValueError("文件中没有音频轨")
        total = (ic.duration or 0) / 1_000_000   # av.time_base = 1/1e6
        step = max(5.0, total * 0.01)
        done_samples = 0
        last_report = 0.0
        resampler = av.AudioResampler(format="s16", layout="stereo", rate=rate)
        with av.open(dst, "w") as oc:
            ostream = oc.add_stream("pcm_s16le", rate=rate)
            ostream.layout = "stereo"
            for frame in ic.decode(stream):
                for rf in resampler.resample(frame):
                    rf.pts = None
                    done_samples += rf.samples
                    for pkt in ostream.encode(rf):
                        oc.mux(pkt)
                if progress_cb and total:
                    done = done_samples / rate
                    if done - last_report >= step:
                        last_report = done
                        progress_cb(min(done, total), total)
            for rf in resampler.resample(None):       # flush resampler
                rf.pts = None
                for pkt in ostream.encode(rf):
                    oc.mux(pkt)
            for pkt in ostream.encode(None):           # flush encoder
                oc.mux(pkt)


def _torch_device(pref: str) -> str:
    if pref in ("cuda", "cpu"):
        return pref
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


_demucs_cache: dict = {}


def separate_vocals(src_wav: Path, dst_wav: Path, model_name: str, device: str,
                    progress_cb=None):
    """Demucs 两轨模式：只要 vocals。直接走 Python API（apply_model），
    避开 demucs CLI 对 ffmpeg/torchaudio 后端的依赖。
    外层按 2 分钟分块处理（块间 2 秒重叠防边界伪影），逐块回报进度。"""
    import numpy as np
    import torch
    from demucs.pretrained import get_model
    from demucs.apply import apply_model

    with wave.open(str(src_wav), "rb") as wf:
        sr = wf.getframerate()
        n = wf.getnframes()
        raw = wf.readframes(n)
    pcm = np.frombuffer(raw, dtype=np.int16).reshape(-1, 2).T  # (2, T)
    audio = torch.from_numpy(pcm.astype(np.float32) / 32768.0)

    if model_name not in _demucs_cache:
        log.info(f"加载 Demucs 模型 {model_name} …")
        _demucs_cache[model_name] = get_model(model_name)
    model = _demucs_cache[model_name]
    model.eval()

    ref = audio.mean(0)
    norm = (audio - ref.mean()) / (ref.std() + 1e-8)

    n = norm.shape[1]
    chunk = 120 * sr      # 每块 2 分钟
    pad = 2 * sr          # 块间重叠
    vidx = model.sources.index("vocals")
    pieces = []
    pos = 0
    with torch.no_grad():
        while pos < n:
            s = max(0, pos - pad)
            e = min(n, pos + chunk + pad)
            out = apply_model(model, norm[:, s:e][None], device=device,
                              shifts=0, split=True, overlap=0.25)[0]
            voc = out[vidx].cpu()
            keep = min(chunk, n - pos)
            pieces.append(voc[:, pos - s: pos - s + keep])
            pos += chunk
            if progress_cb:
                progress_cb(min(pos, n) / sr, n / sr)
    vocals = torch.cat(pieces, dim=1)
    vocals = vocals * (ref.std() + 1e-8) + ref.mean()

    out = (vocals.clamp(-1, 1).numpy() * 32767).astype(np.int16).T  # (T, 2)
    with wave.open(str(dst_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(out.tobytes())


_whisper_lock = threading.Lock()
_whisper_cache: dict = {}


def get_whisper_model(model_name: str, device: str):
    from faster_whisper import WhisperModel
    key = (model_name, device)
    with _whisper_lock:
        if _whisper_cache.get("key") != key:
            log.info(f"加载 Whisper 模型 {model_name} (device={device}) …")
            _whisper_cache["model"] = WhisperModel(
                model_name, device=device, compute_type="auto")
            _whisper_cache["key"] = key
        return _whisper_cache["model"]


@app.post("/api/upload_media")
async def upload_media(file: UploadFile = File(...)):
    """上传待转写的视频/音频（流式落盘，支持大文件）。"""
    MEDIA_DIR.mkdir(exist_ok=True)
    for old in MEDIA_DIR.iterdir():
        try:
            old.unlink()
        except OSError:
            pass
    suffix = Path(file.filename or "media").suffix.lower() or ".bin"
    dest = MEDIA_DIR / f"source{suffix}"
    with dest.open("wb") as f:
        while chunk := await file.read(1 << 20):
            f.write(chunk)
    state.media_path = str(dest)
    state.media_name = file.filename
    log.info(f"媒体已上传: {file.filename} ({dest.stat().st_size / 1e6:.1f} MB)")
    return {"filename": file.filename, "size": dest.stat().st_size}


@app.websocket("/ws/transcribe")
async def ws_transcribe(ws: WebSocket):
    """转写流水线：逐段把识别结果推回前端（与 /ws/translate 同样的即时回填风格）。"""
    await ws.accept()
    try:
        await ws.receive_json()   # 等待前端的启动消息
        cfg = load_config()

        if not state.media_path or not Path(state.media_path).exists():
            await ws.send_json({"type": "error", "message": "请先上传视频/音频文件"})
            return

        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            await ws.send_json({"type": "error",
                                "message": "未安装 faster-whisper，请运行: pip install -r requirements.txt"})
            return
        if cfg.use_demucs:
            try:
                import demucs  # noqa: F401
            except ImportError:
                await ws.send_json({"type": "error",
                                    "message": "未安装 demucs，请运行: pip install -r requirements.txt"})
                return

        loop = asyncio.get_running_loop()
        q: asyncio.Queue = asyncio.Queue()

        def put(kind, payload=None):
            loop.call_soon_threadsafe(q.put_nowait, (kind, payload))

        def prog(label):
            def cb(done, total):
                put("prog", {"label": label, "done": done, "total": total})
            return cb

        def worker():
            try:
                shutil.rmtree(WORK_DIR, ignore_errors=True)
                WORK_DIR.mkdir(exist_ok=True)
                audio_input = state.media_path

                if cfg.use_demucs:
                    put("stage", "正在提取音轨…")
                    src_wav = WORK_DIR / "audio.wav"
                    extract_audio_wav(state.media_path, str(src_wav),
                                      progress_cb=prog("提取音轨"))
                    device = _torch_device(cfg.whisper_device)
                    put("stage", f"Demucs 正在分离人声（{cfg.demucs_model}, {device}）…")
                    voc_wav = WORK_DIR / "vocals.wav"
                    separate_vocals(src_wav, voc_wav, cfg.demucs_model, device,
                                    progress_cb=prog("人声分离"))
                    audio_input = str(voc_wav)

                put("stage", f"加载 Whisper 模型 {cfg.whisper_model}（首次使用会自动下载）…")
                model = get_whisper_model(cfg.whisper_model, cfg.whisper_device)

                put("stage", "开始转写…")
                segments, info = model.transcribe(
                    audio_input,
                    language=cfg.transcribe_lang or None,
                    beam_size=5,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500),
                    condition_on_previous_text=False,   # 口语对白，避免幻觉式重复
                )
                put("info", {"duration": info.duration, "language": info.language})
                for seg in segments:
                    text = seg.text.strip()
                    if text:
                        put("seg", {"start": seg.start, "end": seg.end, "text": text})
                put("done")
            except Exception as e:
                log.exception("转写失败")
                put("err", str(e))

        # 转写前压入撤销历史并清空表格
        state.history.append([SubtitleCue(**vars(c)) for c in state.cues])
        state.cues = []
        state.current_filename = state.media_name

        threading.Thread(target=worker, daemon=True).start()

        total_dur = 0.0
        while True:
            kind, payload = await q.get()
            if kind == "stage":
                await ws.send_json({"type": "stage", "message": payload})
            elif kind == "prog":
                await ws.send_json({"type": "progress", "label": payload["label"],
                                    "done": payload["done"], "total": payload["total"]})
            elif kind == "info":
                total_dur = payload["duration"] or 0.0
                await ws.send_json({"type": "stage",
                                    "message": f"检测到语言: {payload['language']}，时长 {_sec_to_ts(total_dur)}"})
            elif kind == "seg":
                cue = SubtitleCue(
                    index=len(state.cues) + 1,
                    start=_sec_to_ts(payload["start"]),
                    end=_sec_to_ts(payload["end"]),
                    original=payload["text"],
                )
                state.cues.append(cue)
                await ws.send_json({"type": "asr_row", "cue": asdict(cue)})
                if total_dur:
                    await ws.send_json({"type": "progress", "label": "转写",
                                        "done": min(payload["end"], total_dur),
                                        "total": total_dur})
            elif kind == "err":
                await ws.send_json({"type": "error", "message": payload})
                break
            elif kind == "done":
                await ws.send_json({"type": "finished",
                                    "filename": state.media_name,
                                    "count": len(state.cues)})
                break
    except WebSocketDisconnect:
        log.info("转写 WebSocket 客户端断开")
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


# -------- 翻译 / 修复（WebSocket 逐行即时回填） --------
@app.websocket("/ws/translate")
async def ws_translate(ws: WebSocket):
    await ws.accept()
    try:
        msg = await ws.receive_json()
        mode = msg.get("mode", "translate")
        only_missing = bool(msg.get("only_missing"))   # 续作：只处理未完成的行
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
        sem = asyncio.Semaphore(cfg.concurrency)

        if only_missing:
            if mode == "translate":
                targets = [(i, c) for i, c in enumerate(state.cues)
                           if c.original.strip() and not c.translation.strip()]
            else:
                targets = [(i, c) for i, c in enumerate(state.cues)
                           if not (c.fixed_text or "").strip()]
            if not targets:
                await ws.send_json({"type": "error", "message": "没有需要继续处理的行"})
                return
        else:
            targets = list(enumerate(state.cues))
        total = len(targets)

        # ---- 修复模式：先通读整部字幕，生成剧情背景提示 ----
        story_context = ""
        if mode == "fix":
            await ws.send_json({"type": "stage", "message": "正在通读全部字幕，分析剧情背景…"})
            full_text = "\n".join(
                t for c in state.cues if (t := (c.translation or c.original).strip())
            )
            try:
                rsp = await client.chat.completions.create(
                    model=cfg.model,
                    messages=[
                        {"role": "system", "content": PROMPT_STORY},
                        {"role": "user", "content": full_text},
                    ],
                    timeout=300,
                )
                story_context, pt, ct = _extract(rsp)
                state.ptok += pt
                state.ctok += ct
                await ws.send_json({"type": "tokens", "ptok": state.ptok, "ctok": state.ctok})
                log.info(f"剧情背景分析完成（{len(story_context)} 字）:\n{story_context}")
                await ws.send_json({"type": "stage", "message": "背景分析完成，开始逐句修复…"})
            except Exception as e:
                log.warning(f"剧情背景分析失败，按常规方式修复: {e}")
                await ws.send_json({"type": "stage",
                                    "message": f"背景分析失败（{e}），按常规方式逐句修复"})

        ctx_block = (
            "\n\n【剧情背景档案（仅供参考，注意全片称呼与语气一致）】\n" + story_context
            if story_context else ""
        )
        fix_prompt = PROMPT_FIX + ctx_block

        def with_context(idx: int, source: str, original_only: bool = False) -> str:
            """请求附带全片位置 + 前后各 2 句，帮助模型对号入座到具体场景。
            translate 模式上下文用原文（译文还不存在），fix 模式用译文。"""
            def line(c):
                return (c.original if original_only
                        else (c.translation or c.original)).strip()
            n = len(state.cues)
            pct = int(idx / max(1, n - 1) * 100)
            prev = [line(c) for c in state.cues[max(0, idx - 2):idx] if line(c)]
            nxt = [line(c) for c in state.cues[idx + 1:idx + 3] if line(c)]
            parts = [f"【位置】第 {idx + 1} 行 / 共 {n} 行（约全片 {pct}%）"]
            if prev:
                parts.append("【前文】\n" + "\n".join(prev))
            parts.append("【当前句】\n" + source)
            if nxt:
                parts.append("【后文】\n" + "\n".join(nxt))
            return "\n".join(parts)

        async def handle(idx: int, cue: SubtitleCue):
            async with sem:
                try:
                    if mode == "translate":
                        rsp = await client.chat.completions.create(
                            model=cfg.model,
                            messages=[
                                {"role": "system",
                                 "content": PROMPT_TRANSLATE.format(lang=cfg.target_lang)},
                                {"role": "user",
                                 "content": with_context(idx, cue.original, original_only=True)},
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
                                + ctx_block
                            )
                            rsp = await client.chat.completions.create(
                                model=cfg.model,
                                messages=[
                                    {"role": "system", "content": fallback_prompt},
                                    {"role": "user",
                                     "content": with_context(idx, cue.original, original_only=True)},
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
                                    {"role": "system", "content": fix_prompt},
                                    {"role": "user", "content": with_context(idx, source)},
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

        tasks = [handle(i, c) for i, c in targets]
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
    reload_mode = "--reload" in sys.argv
    log.info("启动网页服务: http://127.0.0.1:8000"
             + ("（热重载已开启，改 .py 自动重启）" if reload_mode else ""))
    if reload_mode:
        # 热重载需要 import string 形式；重启会丢失内存中的字幕状态（cues/撤销历史）
        uvicorn.run("web_app:app", host="127.0.0.1", port=8000,
                    reload=True, reload_dirs=[str(BASE_DIR)])
    else:
        uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()

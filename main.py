# -*- coding: utf-8 -*-
"""
AI SRT Translator v1.6  (2025‑07)
---------------------------------
• 并发翻译：Semaphore(8)，每行完成即实时回写 GUI
• 表格列：# 开始 结束 原文 译文 修复后 恢复
  - “修复后” 显示 AI 输出的润色版本，而非简单打钩
• 修复逻辑：始终返回修正文；若本身通顺，AI 将原样返回
• 翻译提示词强化：
  - 纯语气词 / 拟声词 → “啊～～”
  - 单字 “啊” → “啊～”
  - 其余正常翻译，禁止附加说明
"""

import sys, asyncio, logging, datetime
from dataclasses import dataclass
from pathlib import Path
from typing import List

from openai import AsyncOpenAI
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QProgressBar, QToolBar, QStatusBar, QMessageBox,
    QDialog, QComboBox, QHeaderView
)
from PySide6.QtGui import QAction

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout),
              logging.FileHandler("translator.log", encoding="utf-8")]
)
log = logging.getLogger("translator")

# ---------------- Data ------------------
@dataclass
class Config:
    api_key: str = ""
    base_url: str = ""          # 需带 /v1
    model: str = "gpt-4o-mini"
    target_lang: str = "中文"

@dataclass
class SubtitleCue:
    index: int
    start: str
    end: str
    original: str
    translation: str = ""        # 翻译
    fixed_text: str = ""         # 修复后文本

# ---------------- SRT -------------------
def parse_srt(path: Path) -> List[SubtitleCue]:
    cues, blk = [], []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            if ln.strip(): blk.append(ln.rstrip("\n"))
            else: _blk_to_cue(blk, cues); blk=[]
        _blk_to_cue(blk, cues)
    return cues

def _blk_to_cue(blk, cues):
    if len(blk) >= 3:
        idx = int(blk[0]); st,_,ed = blk[1].partition(" --> ")
        cues.append(SubtitleCue(idx, st, ed, "\n".join(blk[2:])))

def write_srt(path: Path, cues: List[SubtitleCue]):
    with path.open("w", encoding="utf-8") as f:
        for c in cues:
            out = c.fixed_text or c.translation or c.original
            f.write(f"{c.index}\n{c.start} --> {c.end}\n{out}\n\n")

# ---------------- Worker ----------------
class TranslateWorker(QThread):
    """后台线程：并发翻译 / 修复"""
    update_row = Signal(int, str, str)   # 行号, 翻译, 修复后
    token_inc  = Signal(int, int)
    progress   = Signal(int, int)
    finished   = Signal(str)
    error      = Signal(str)

    MAX_CONCURRENCY = 8    # 并发量

    def __init__(self, cues: List[SubtitleCue], cfg: Config, mode: str):
        super().__init__()
        self.cues = cues; self.cfg = cfg; self.mode = mode
        self._ptok = self._ctok = 0

    # ---- 解析多版本返回 ----
    @staticmethod
    def _extract(resp):
        if hasattr(resp, "choices"):
            return resp.choices[0].message.content.strip(), resp.usage.prompt_tokens, resp.usage.completion_tokens
        if isinstance(resp, dict) and "choices" in resp:
            u = resp.get("usage", {})
            return resp["choices"][0]["message"]["content"].strip(), u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
        txt = str(resp).strip()
        if txt.lower().startswith("<!doctype") or "<html" in txt.lower():
            raise ValueError("返回 HTML — 检查 base_url 或 Token")
        return txt, 0, 0

    # ---- 线程入口 ----
    def run(self):
        try: asyncio.run(self._runner())
        except Exception as e: self.error.emit(str(e))

    async def _runner(self):
        client = AsyncOpenAI(api_key=self.cfg.api_key, base_url=self.cfg.base_url or None)
        sem = asyncio.Semaphore(self.MAX_CONCURRENCY)
        tasks = [self._translate_one(client, sem, i, c) if self.mode=="translate"
                 else self._fix_one(client, sem, i, c)
                 for i, c in enumerate(self.cues)]
        total=len(tasks)
        for i, coro in enumerate(asyncio.as_completed(tasks), 1):
            try:
                await coro
                self.progress.emit(i, total)
            except Exception as e:
                self.error.emit(str(e)); return
        self.finished.emit(self.mode)

    # ---- 单行翻译 ----
    async def _translate_one(self, client, sem, idx, cue):
        async with sem:
            rsp = await client.chat.completions.create(
                model=self.cfg.model,
                messages=[
                    {"role":"system",
                     "content":f"你是一名专业字幕翻译。"
                               f"把用户提供的字幕句子翻译成{self.cfg.target_lang}并保持语气自然。"
                               "若整句为无法翻译的语气词或拟声词，请输出“啊～～”；"
                               "若原句仅为单字“啊”，输出“啊～”。"
                               "严格只输出翻译文本，无任何解释。"},
                    {"role":"user","content":cue.original}
                ],
                timeout=30)
            txt, pt, ct = self._extract(rsp)
            cue.translation = txt; cue.fixed_text = ""
            self._ptok += pt; self._ctok += ct
            self.update_row.emit(idx, txt, "")
            self.token_inc.emit(pt, ct)

    # ---- 单行修复 ----
    async def _fix_one(self, client, sem, idx, cue):
        async with sem:
            rsp = await client.chat.completions.create(
                model=self.cfg.model,
                messages=[
                    {"role":"system",
                     "content":"你是一名中文润色助手，请在不改变原意的前提下，"
                               "修正不自然、重复或病句之处，使语句通顺自然。"
                               "如果句子本就通顺，请原样返回。严格只输出修正后的完整句子，不加任何其他内容。"},
                    {"role":"user","content":cue.translation or cue.original}
                ],
                timeout=30)
            txt, pt, ct = self._extract(rsp)
            cue.fixed_text = txt
            self._ptok += pt; self._ctok += ct
            self.update_row.emit(idx, cue.translation, txt)
            self.token_inc.emit(pt, ct)

# ---------------- MainWindow ------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = Config()
        self.cues: List[SubtitleCue] = []
        self.history: List[List[SubtitleCue]] = []
        self._ptok = self._ctok = 0
        self._ui()

    # ---- UI 构建 ----
    def _ui(self):
        self.setWindowTitle("AI 字幕翻译器"); self.resize(1120, 650)
        QApplication.setStyle("Fusion")
        QApplication.instance().setStyleSheet("""
            QPushButton{border:1px solid #ccc;border-radius:6px;padding:4px 10px;background:#fafafa;}
            QPushButton:hover{background:#e6f2ff;}
            QToolBar{spacing:4px;} QToolButton{margin:2px;padding:4px 8px;border-radius:6px;}
            QToolButton:hover{background:#e6f2ff;}
        """)
        tb = QToolBar(); tb.setMovable(False); self.addToolBar(tb)
        for t, cb in (("打开", self.open_file), ("保存", self.save_file), ("导出", self.export_file),
                      (None, None), ("全部翻译", self.translate_all), ("全部修复", self.fix_all),
                      ("撤销", self.undo), ("设置", self.open_settings)):
            tb.addSeparator() if t is None else tb.addAction(QAction(t, self, triggered=cb))

        # 表格
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["#", "开始", "结束", "原文", "译文", "修复后", "恢复"])
        hdr = self.table.horizontalHeader()
        for i in (0,1,2,6): hdr.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.Stretch); hdr.setSectionResizeMode(4, QHeaderView.Stretch)
        hdr.setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setWordWrap(True); self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)

        # 进度 & 状态
        self.progress = QProgressBar(); self.progress.setFixedHeight(18)
        self.status = QStatusBar(); self.setStatusBar(self.status)
        self.token_lbl = QLabel("Tokens P:0 | C:0"); self.status.addPermanentWidget(self.token_lbl)

        layout = QVBoxLayout(); layout.addWidget(self.table); layout.addWidget(self.progress)
        cw = QWidget(); cw.setLayout(layout); self.setCentralWidget(cw)

    # ---- 文件 ----
    def open_file(self):
        fn, _ = QFileDialog.getOpenFileName(self, "选择 SRT", "", "SRT (*.srt)")
        if fn:
            self.cues = parse_srt(Path(fn)); self._refresh(); self.history.clear()
            self.status.showMessage(f"已加载 {fn}")

    def save_file(self):
        fn, _ = QFileDialog.getSaveFileName(self, "保存为", "translated.srt", "SRT (*.srt)")
        if fn: write_srt(Path(fn), self.cues); self.status.showMessage(f"已保存 {fn}")

    def export_file(self):
        if not self.cues: return
        out = Path(f"export_{datetime.datetime.now():%Y%m%d_%H%M%S}.srt")
        write_srt(out, self.cues); self.status.showMessage(f"已导出 {out}")

    # ---- 表格辅助 ----
    def _refresh(self):
        self.table.setRowCount(len(self.cues))
        for r, c in enumerate(self.cues):
            self._set_row(r, c.translation, c.fixed_text)

    def _set_row(self, row: int, trans: str, fix: str):
        cue = self.cues[row]; cue.translation = trans; cue.fixed_text = fix
        values = (cue.index, cue.start, cue.end, cue.original, cue.translation, cue.fixed_text, "")
        for col, val in enumerate(values):
            itm = QTableWidgetItem(str(val)); itm.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            itm.setFlags(itm.flags() | Qt.ItemIsEditable)
            self.table.setItem(row, col, itm)
        # 恢复按钮：清除修复后文本
        if cue.translation or cue.fixed_text:
            btn = QPushButton("恢复")
            btn.clicked.connect(lambda _, r=row: self._restore(r))
            self.table.setCellWidget(row, 6, btn)
        else:
            self.table.setCellWidget(row, 6, QWidget())

    def _restore(self, row: int):
        self.cues[row].translation = ""
        self.cues[row].fixed_text  = ""
        self._set_row(row, "", "")
        self.status.showMessage(f"第 {row+1} 行已恢复")

    # ---- LLM 调度 ----
    def translate_all(self): self._launch("translate")
    def fix_all(self):       self._launch("fix")

    def _launch(self, mode: str):
        if not self._ready(): return
        self._ptok = self._ctok = 0; self._update_tok()
        self.progress.setValue(0); self.progress.setMaximum(len(self.cues))
        self._push_history()

        self.worker = TranslateWorker(self.cues.copy(), self.cfg, mode)
        self.worker.update_row.connect(self._set_row)
        self.worker.token_inc.connect(lambda p, c: (self._tok_inc(p, c)))
        self.worker.progress.connect(lambda d, _t: self.progress.setValue(d))
        self.worker.error.connect(lambda m: QMessageBox.critical(self, "错误", m))
        self.worker.finished.connect(lambda _: self.status.showMessage("全部完成！"))
        self.worker.start(); self.status.showMessage("任务进行中…")

    def _tok_inc(self, p, c): self._ptok += p; self._ctok += c; self._update_tok()
    def _update_tok(self): self.token_lbl.setText(f"Tokens P:{self._ptok} | C:{self._ctok}")

    # ---- 撤销 ----
    def _push_history(self):
        self.history.append([SubtitleCue(**vars(c)) for c in self.cues])

    def undo(self):
        if self.history:
            self.cues = self.history.pop(); self._refresh(); self.status.showMessage("已撤销")
        else: self.status.showMessage("无可撤销")

    # ---- 设置 ----
    def open_settings(self): SettingsDialog(self.cfg, self).exec()

    # ---- 工具 ----
    def _ready(self) -> bool:
        if not self.cues:
            QMessageBox.warning(self, "提示", "请先加载 SRT"); return False
        if not self.cfg.api_key:
            QMessageBox.warning(self, "提示", "请在设置里输入 API Key"); return False
        return True

# ---------------- Settings --------------
class SettingsDialog(QDialog):
    _MODELS = ["gpt-4o-mini","gpt-4o","gpt-4o-128k","gpt-3.5-turbo","gpt-3.5-turbo-16k"]
    _LANGS  = ["中文","English","日本語","Español","Français","Deutsch"]
    def __init__(self, cfg: Config, parent=None):
        super().__init__(parent); self.cfg=cfg; self.setWindowTitle("设置"); self.resize(400,240)
        self.api=QLineEdit(cfg.api_key); self.url=QLineEdit(cfg.base_url)
        self.model=QComboBox(); self.model.addItems(self._MODELS); self.model.setCurrentText(cfg.model)
        self.lang=QComboBox(); self.lang.addItems(self._LANGS); self.lang.setCurrentText(cfg.target_lang)
        lay=QVBoxLayout(self)
        for lbl,w in (("API Key", self.api),("接口地址(含 /v1)", self.url),
                      ("模型", self.model),("目标语言", self.lang)):
            lay.addWidget(QLabel(lbl)); lay.addWidget(w)
        btn_ok=QPushButton("保存"); btn_ok.clicked.connect(self.accept)
        btn_ca=QPushButton("取消"); btn_ca.clicked.connect(self.reject)
        hb=QHBoxLayout(); hb.addStretch(); hb.addWidget(btn_ok); hb.addWidget(btn_ca); lay.addLayout(hb)
    def accept(self):
        self.cfg.api_key=self.api.text().strip()
        self.cfg.base_url=self.url.text().strip()
        self.cfg.model=self.model.currentText()
        self.cfg.target_lang=self.lang.currentText()
        super().accept()

# --------------- main -------------------
def main():
    app = QApplication(sys.argv)
    win = MainWindow(); win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

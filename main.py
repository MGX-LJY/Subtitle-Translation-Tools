# -*- coding: utf-8 -*-
"""
AI SRT Translator v1.8  (2025‑07)
---------------------------------
• 并发 8 通道，但结果按行顺序 *即时* 刷新
• 语气词规则再加: “晚安” → “啊～～”
• 导出文件名: <原名>_翻译后.srt，可自选文件夹
"""

import sys, asyncio, logging, datetime
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from openai import AsyncOpenAI
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QProgressBar, QToolBar, QStatusBar, QMessageBox,
    QDialog, QComboBox, QHeaderView
)
from PySide6.QtGui import QAction

# -------- logging --------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout),
              logging.FileHandler("translator.log", encoding="utf-8")]
)
log = logging.getLogger("translator")

# -------- data --------
@dataclass
class Config:
    api_key: str = ""
    base_url: str = ""
    model: str   = "gpt-4o-mini"
    target_lang: str = "中文"

@dataclass
class SubtitleCue:
    index:int; start:str; end:str; original:str
    translation:str=""; fixed_text:str=""

# -------- srt I/O --------
def parse_srt(path:Path)->List[SubtitleCue]:
    cues,blk=[],[]
    with path.open("r",encoding="utf-8",errors="ignore") as f:
        for ln in f:
            if ln.strip(): blk.append(ln.rstrip("\n"))
            else: _blk_to_cue(blk,cues); blk=[]
        _blk_to_cue(blk,cues)
    return cues
def _blk_to_cue(blk,cues):
    if len(blk)>=3:
        idx=int(blk[0]); s,_,e=blk[1].partition(" --> ")
        cues.append(SubtitleCue(idx,s,e,"\n".join(blk[2:])))
def write_srt(path:Path,cues:List[SubtitleCue]):
    with path.open("w",encoding="utf-8") as f:
        for c in cues:
            txt=c.fixed_text or c.translation or c.original
            f.write(f"{c.index}\n{c.start} --> {c.end}\n{txt}\n\n")

# -------- worker --------
class TranslateWorker(QThread):
    update_row = Signal(int,str,str)
    token_inc  = Signal(int,int)
    progress   = Signal(int,int)
    finished   = Signal(str)
    error      = Signal(str)
    MAX_CONCURRENCY=8
    def __init__(self,cues:List[SubtitleCue],cfg:Config,mode:str):
        super().__init__(); self.cues=cues; self.cfg=cfg; self.mode=mode
        self.prompt_translate=(
            "你是一名专业字幕翻译。请将用户提供的字幕句子翻译成{lang}，口语自然、符合日语对白风格。\n"
            "规则：①如整句为无法翻译的语气词/拟声词/“晚安”→输出“啊～～”；\n"
            "②若原句仅含单字“啊”→输出“啊～”；③其余正常翻译；只输出翻译文本，禁止附带说明。"
        )


        self.prompt_fix = (
            "你是一名具有 10 年以上经验的合法商业 AV 字幕润色助手。"
            "在绝不改变原意的前提下，请修正病句、口语化表达和多余重复，使语句更贴合 AV 场景的自然对白。\n"
            "请遵循以下规则：\n"
            "1. 若原句已自然流畅且符合场景，请原样输出；\n"
            "2. 若需润色，仅输出润色后的字幕文本，不得附带任何解释或标注。"
        )

    # --- extract ---
    @staticmethod
    def _extract(resp):
        """
        统一解析不同 SDK / 网关返回，避免 content 为 None 时触发
        AttributeError: 'NoneType' object has no attribute 'strip'
        """
        # ── openai>=1.0 (对象) ───────────────────────────────
        if hasattr(resp, "choices"):
            content = resp.choices[0].message.content or ""
            return content.strip(), resp.usage.prompt_tokens, resp.usage.completion_tokens

        # ── openai 0.x (dict) ──────────────────────────────
        if isinstance(resp, dict) and "choices" in resp:
            usage    = resp.get("usage", {})
            message  = resp["choices"][0].get("message", {})
            content  = (message.get("content") if isinstance(message, dict) else message) or ""
            return content.strip(), usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)

        # ── 其它 / 代理平台直接字符串 ───────────────────────
        text = str(resp or "").strip()
        if text.lower().startswith("<!doctype") or "<html" in text.lower():
            raise ValueError("收到 HTML — base_url 或 Token 可能配置错误")
        return text, 0, 0
    # --- thread entry ---
    def run(self):
        try:
            asyncio.run(self._main())          # ★ 这里仍然调用 _main
        except Exception as e:
            self.error.emit(str(e))

    # -------- 核心异步逻辑 --------
    async def _main(self):
        client = AsyncOpenAI(
            api_key=self.cfg.api_key,
            base_url=self.cfg.base_url or None
        )
        sem = asyncio.Semaphore(self.MAX_CONCURRENCY)
        total = len(self.cues)

        # ---- 内部协程：真正的处理单元 ----
        async def handle(idx: int, cue: SubtitleCue):
            async with sem:
                try:
                    # --- ① 翻译模式 ---
                    if self.mode == "translate":
                        rsp = await client.chat.completions.create(
                            model=self.cfg.model,
                            messages=[
                                {"role": "system",
                                 "content": self.prompt_translate.format(
                                     lang=self.cfg.target_lang)},
                                {"role": "user", "content": cue.original}
                            ],
                            timeout=25
                        )
                        txt, pt, ct = self._extract(rsp)
                        cue.translation = txt
                        cue.fixed_text = ""

                    # --- ② 修复模式 ---
                    else:
                        source = cue.translation or cue.original
                        # 遇到拒绝性文本 → 保守直译
                        if any(bad in source for bad in ("无法翻译", "【违规内容")):
                            fallback_prompt = (
                                self.prompt_translate.format(
                                    lang=self.cfg.target_lang)
                                + "\n【额外指令】请保持直译风格，避免润色和主观扩写；"
                                  "若出现敏感内容请用 ♪♪ 占位。"
                            )
                            rsp = await client.chat.completions.create(
                                model=self.cfg.model,
                                messages=[
                                    {"role": "system",
                                     "content": fallback_prompt},
                                    {"role": "user",
                                     "content": cue.original}
                                ],
                                timeout=25
                            )
                            txt, pt, ct = self._extract(rsp)
                            cue.translation = txt
                            cue.fixed_text = ""
                        else:
                            # 正常润色
                            rsp = await client.chat.completions.create(
                                model=self.cfg.model,
                                messages=[
                                    {"role": "system",
                                     "content": self.prompt_fix},
                                    {"role": "user", "content": source}
                                ],
                                timeout=25
                            )
                            txt, pt, ct = self._extract(rsp)
                            cue.fixed_text = txt

                    # --- ③ 通用：Token & 回传 ---
                    self.token_inc.emit(pt, ct)
                    return (idx, True, "")

                except Exception as e:
                    return (idx, False, str(e))

        # ---- 并发调度 & 进度回写 ----
        tasks = [handle(i, c) for i, c in enumerate(self.cues)]
        done_cnt = 0
        for coro in asyncio.as_completed(tasks):
            idx, ok, err = await coro
            if not ok:
                self.error.emit(err)
                return
            cue = self.cues[idx]
            self.update_row.emit(idx, cue.translation, cue.fixed_text)
            done_cnt += 1
            self.progress.emit(done_cnt, total)

        self.finished.emit(self.mode)

# -------- main window --------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg=Config(); self.cues:List[SubtitleCue]=[]; self.history=[]; self.current_file:Path|None=None
        self._ptok=self._ctok=0
        self._ui()
    # ui
    def _ui(self):
        self.setWindowTitle("AI 字幕翻译器"); self.resize(1120,650)
        QApplication.setStyle("Fusion")
        QApplication.instance().setStyleSheet(
            "QPushButton{border:1px solid #ccc;border-radius:6px;padding:4px 10px;background:#fafafa;}"
            "QPushButton:hover{background:#e6f2ff;} QToolBar{spacing:4px;}"
            "QToolButton{margin:2px;padding:4px 8px;border-radius:6px;} QToolButton:hover{background:#e6f2ff;}"
        )
        tb=QToolBar(); tb.setMovable(False); self.addToolBar(tb)
        for t,cb in (("打开",self.open_file),("保存",self.save_file),("导出",self.export_file),
                     (None,None),("全部翻译",self.translate_all),("全部修复",self.fix_all),
                     ("撤销",self.undo),("设置",self.open_settings)):
            tb.addSeparator() if t is None else tb.addAction(QAction(t,self,triggered=cb))
        self.table=QTableWidget(0,7)
        self.table.setHorizontalHeaderLabels(["#","开始","结束","原文","译文","修复后","恢复"])
        hdr=self.table.horizontalHeader()
        for i in (0,1,2,6): hdr.setSectionResizeMode(i,QHeaderView.ResizeToContents)
        for i in (3,4,5): hdr.setSectionResizeMode(i,QHeaderView.Stretch)
        self.table.setWordWrap(True); self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.DoubleClicked|QTableWidget.EditKeyPressed)
        self.progress=QProgressBar(); self.progress.setFixedHeight(18)
        self.status=QStatusBar(); self.setStatusBar(self.status)
        self.token_lbl=QLabel("Tokens P:0 | C:0"); self.status.addPermanentWidget(self.token_lbl)
        lay=QVBoxLayout(); lay.addWidget(self.table); lay.addWidget(self.progress)
        cw=QWidget(); cw.setLayout(lay); self.setCentralWidget(cw)
    # table helpers
    def _refresh(self):
        self.table.setRowCount(len(self.cues))
        for r,c in enumerate(self.cues): self._set_row(r,c.translation,c.fixed_text)
    def _set_row(self,row,t,f):
        cue=self.cues[row]; cue.translation=t; cue.fixed_text=f
        vals=(cue.index,cue.start,cue.end,cue.original,cue.translation,cue.fixed_text,"")
        for col,val in enumerate(vals):
            item=QTableWidgetItem(str(val)); item.setTextAlignment(Qt.AlignLeft|Qt.AlignTop)
            item.setFlags(item.flags()|Qt.ItemIsEditable); self.table.setItem(row,col,item)
        if cue.translation or cue.fixed_text:
            btn=QPushButton("恢复"); btn.clicked.connect(lambda _,r=row:self._restore(r))
            self.table.setCellWidget(row,6,btn)
        else: self.table.setCellWidget(row,6,QWidget())
    def _restore(self,row): self.cues[row].translation=""; self.cues[row].fixed_text=""; self._set_row(row,"","")
    # file ops
    def open_file(self):
        fn,_=QFileDialog.getOpenFileName(self,"选择 SRT","","SRT (*.srt)")
        if fn: self.current_file=Path(fn); self.cues=parse_srt(self.current_file); self._refresh(); self.history.clear()
    def save_file(self):
        fn,_=QFileDialog.getSaveFileName(self,"保存为","translated.srt","SRT (*.srt)")
        if fn: write_srt(Path(fn),self.cues)
    def export_file(self):
        if not self.cues: return
        dest_dir=QFileDialog.getExistingDirectory(self,"选择导出文件夹")
        if not dest_dir: return
        name="translated"
        if self.current_file: name=self.current_file.stem+"_翻译后"
        out=Path(dest_dir)/f"{name}.srt"; write_srt(out,self.cues); self.status.showMessage(f"已导出 {out}")
    # llm launch
    def translate_all(self): self._run("translate")
    def fix_all(self):       self._run("fix")
    def _run(self,mode):
        if not self._ready(): return
        self._ptok=self._ctok=0; self._update_tok()
        self.progress.setValue(0); self.progress.setMaximum(len(self.cues))
        self._push_hist()
        w=TranslateWorker(self.cues.copy(),self.cfg,mode)
        w.update_row.connect(self._set_row); w.token_inc.connect(lambda p,c:self._add_tok(p,c))
        w.progress.connect(lambda d,total:self.progress.setValue(d))
        w.error.connect(lambda m: QMessageBox.critical(self,"错误",m))
        w.finished.connect(lambda _: self.status.showMessage("全部完成！"))
        w.start(); self.status.showMessage("任务进行中…"); self.worker=w
    def _add_tok(self,p,c): self._ptok+=p; self._ctok+=c; self._update_tok()
    def _update_tok(self): self.token_lbl.setText(f"Tokens P:{self._ptok} | C:{self._ctok}")
    # hist / undo
    def _push_hist(self): self.history.append([SubtitleCue(**vars(c)) for c in self.cues])
    def undo(self):
        if self.history: self.cues=self.history.pop(); self._refresh()
    # settings
    def open_settings(self): SettingsDialog(self.cfg,self).exec()
    # util
    def _ready(self):
        if not self.cues: QMessageBox.warning(self,"提示","请先加载 SRT"); return False
        if not self.cfg.api_key: QMessageBox.warning(self,"提示","请在设置里输入 API Key"); return False
        return True

# settings dialog (同 v1.7 略)
class SettingsDialog(QDialog):
    _MODELS=["gpt-4o-mini","gpt-4o","gpt-4o-128k","gpt-3.5-turbo","gpt-3.5-turbo-16k"]
    _LANGS=["中文","English","日本語","Español","Français","Deutsch"]
    def __init__(self,cfg:Config,parent=None):
        super().__init__(parent); self.cfg=cfg; self.setWindowTitle("设置"); self.resize(400,240)
        self.api=QLineEdit(cfg.api_key); self.url=QLineEdit(cfg.base_url)
        self.model=QComboBox(); self.model.addItems(self._MODELS); self.model.setCurrentText(cfg.model)
        self.lang=QComboBox();  self.lang.addItems(self._LANGS);  self.lang.setCurrentText(cfg.target_lang)
        lay=QVBoxLayout(self)
        for lbl,w in (("API Key",self.api),("接口地址(含 /v1)",self.url),
                      ("模型",self.model),("目标语言",self.lang)):
            lay.addWidget(QLabel(lbl)); lay.addWidget(w)
        ok=QPushButton("保存"); ca=QPushButton("取消")
        ok.clicked.connect(self.accept); ca.clicked.connect(self.reject)
        hb=QHBoxLayout(); hb.addStretch(); hb.addWidget(ok); hb.addWidget(ca); lay.addLayout(hb)
    def accept(self):
        self.cfg.api_key=self.api.text().strip(); self.cfg.base_url=self.url.text().strip()
        self.cfg.model=self.model.currentText(); self.cfg.target_lang=self.lang.currentText()
        super().accept()

# ---- main ----
def main():
    app=QApplication(sys.argv); win=MainWindow(); win.show(); sys.exit(app.exec())
if __name__=="__main__": main()

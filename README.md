# Subtitle Translation Tools

一个基于 FastAPI 的 SRT 字幕翻译、润色修复与本地转写工具。项目默认通过 OpenAI 兼容接口调用 xAI Grok，并针对日语口语对白、语气词、称呼与上下文一致性做了专门优化。

## 主要功能

- 导入、编辑与导出 SRT 字幕
- 使用 Grok 逐句翻译，支持并发请求和 WebSocket 实时回填
- 根据整部字幕生成剧情背景档案，再结合场景、前后文进行两阶段润色
- “继续”模式仅处理尚未翻译或尚未修复的字幕行
- 支持撤销、单行恢复、Token 统计与行内编辑
- 视频或音频本地转写：PyAV 提取音轨 → Demucs 分离人声 → Faster-Whisper 生成字幕
- 浏览器端单页界面，无需前端构建步骤

> 本项目的翻译提示词针对口语化及成人影视对白场景进行了定制。请确保输入内容、模型使用方式和生成结果符合所在地法律及服务条款。

## 环境要求

- Windows 10/11
- Python 3.10 或更高版本
- 可访问的 OpenAI 兼容 API；默认配置为 xAI API
- 本地转写建议使用 NVIDIA GPU；CPU 也可运行，但速度会明显较慢

## 安装

```powershell
git clone https://github.com/MGX-LJY/Subtitle-Translation-Tools.git
cd Subtitle-Translation-Tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

RTX 50 系显卡（Blackwell，`sm_120`）需要先安装 CUDA 12.8 版本的 PyTorch：

```powershell
python -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r requirements.txt
```

其他环境通常可以直接安装依赖：

```powershell
python -m pip install -r requirements.txt
```

## 启动

```powershell
.\.venv\Scripts\python.exe web_app.py
```

浏览器打开 [http://127.0.0.1:8000](http://127.0.0.1:8000)。

首次使用时点击右上角设置按钮，至少填写 API Key。默认服务配置为：

| 配置项 | 默认值 |
| --- | --- |
| Base URL | `https://api.x.ai/v1` |
| 模型 | `grok-4` |
| 目标语言 | 中文 |
| 翻译并发数 | `10`（可配置范围 `1–32`） |
| Whisper 模型 | `large-v3` |
| 转写语言 | `ja`，留空时自动检测 |
| Demucs 模型 | `htdemucs` |

设置会保存在本机的 `config.json` 中。该文件已被 Git 忽略，请勿公开 API Key。

## 使用方法

### 翻译现有字幕

1. 点击“打开”选择 `.srt` 文件，或将文件拖入字幕表格。
2. 点击“翻译”，等待各行实时回填。
3. 点击“修复”，工具会先分析整部字幕的剧情和场景，再逐句润色。
4. 可直接点击表格单元格修改文字，或使用撤销与单行恢复。
5. 点击“导出”保存中文 SRT；导出时优先使用修复文本，其次是译文，最后是原文。

中断后可点击“继续”，仅补齐尚未完成的行。

### 从视频或音频生成字幕

1. 上传视频或音频文件。
2. 工具使用 PyAV 解码并生成 WAV，无需系统安装 FFmpeg。
3. 启用 Demucs 时先提取人声，再由 Faster-Whisper 逐段转写。
4. 转写结果进入原文列，可继续执行翻译和修复。

首次转写会下载所选模型，需要额外时间与磁盘空间。关闭 Demucs 可以降低显存占用并缩短处理时间，但复杂背景声下的识别效果可能下降。

## 运行时文件

以下文件和目录会在程序运行时生成：

- `config.json`：本地配置和 API Key
- `translator.log`：运行日志
- `media_tmp/`：上传的媒体文件
- `work_tmp/`：音轨及人声分离的中间文件

应用状态保存在当前进程内，多标签页会共享同一份字幕。该工具目前定位为本机单用户应用，请勿未经鉴权直接暴露到公网。

## 项目结构

```text
.
├── web_app.py          # FastAPI 后端、翻译/修复和转写流水线
├── static/
│   └── index.html      # 内嵌 CSS/JavaScript 的单页前端
├── requirements.txt    # Python 依赖
└── README.md
```

## 常见问题

### API 返回 HTML 或请求失败

检查 Base URL、API Key 和模型名称。Base URL 应指向兼容 OpenAI Chat Completions 的 API 根地址，而不是网页地址。

### CUDA 无法使用或提示不支持显卡架构

RTX 50 系显卡请确认安装的是 CUDA 12.8 的 `torch` 和 `torchaudio`。也可以在设置中把 Whisper 设备切换为 `cpu` 进行排查。

### Windows 控制台中文或日文乱码

可以使用 UTF-8 模式启动：

```powershell
.\.venv\Scripts\python.exe -X utf8 web_app.py
```

## 技术栈

- FastAPI / Uvicorn
- OpenAI Python SDK（兼容 xAI API）
- Faster-Whisper
- Demucs
- 原生 HTML、CSS 与 JavaScript

## 许可证

仓库当前未提供开源许可证。在许可证明确之前，默认保留所有权利。

# Subtitle Translation Tools 数据流设计

## 主要数据流向

### 1. 配置数据流
```
应用启动 → load_config() → JSON文件读取 → Config对象 → MainWindow.cfg
                    ↓
设置对话框 ← 用户输入 ← SettingsDialog ← GUI交互
                    ↓
Config对象 → save_config() → JSON文件写入 → 持久化存储
```

### 2. 字幕处理数据流
```
SRT文件 → parse_srt() → 文本解析 → SubtitleCue列表 → 表格显示
                              ↓
原始文本 → OpenAI API → GPT处理 → 翻译文本 → SubtitleCue.translation
                              ↓
翻译文本 → OpenAI API → GPT润色 → 修复文本 → SubtitleCue.fixed_text
                              ↓
SubtitleCue列表 → write_srt() → 格式化输出 → 目标SRT文件
```

### 3. 异步处理数据流
```
UI请求 → TranslateWorker.start() → QThread创建 → 异步事件循环
                                        ↓
并发任务队列 → asyncio.Semaphore(8) → API并发调用 → 响应收集
                                        ↓
结果数据 → Qt.Signal → 信号发送 → UI线程 → 表格更新
```

### 4. 错误处理数据流
```
异常发生 → try/catch → 错误分类 → 日志记录 → logging系统
                              ↓
用户通知 ← QMessageBox ← 错误转换 ← 友好化处理
                              ↓
系统恢复 ← 降级策略 ← 错误评估 ← 影响分析
```

## 详细数据流程

### 应用启动流程
1. **程序初始化**
   ```python
   app = QApplication(sys.argv)
   win = MainWindow()
   ```

2. **配置加载**
   ```python
   self.cfg = load_config()  # 从 main.config.json 加载
   ```
   - 检查配置文件存在性
   - JSON 解析和数据验证
   - 默认值填充和错误处理

3. **UI 构建**
   ```python
   self._ui()  # 构建界面组件
   ```
   - 工具栏创建和事件绑定
   - 表格初始化和列设置
   - 进度条和状态栏配置

### 文件操作流程
1. **SRT 文件加载**
   ```
   用户选择文件 → QFileDialog → 文件路径
                            ↓
   parse_srt(path) → 逐行读取 → 块分析 → SubtitleCue对象
                            ↓
   self.cues列表 → _refresh() → 表格数据填充
   ```

2. **文件保存流程**
   ```
   用户触发保存 → QFileDialog → 目标路径
                             ↓
   write_srt(path, cues) → 格式化输出 → UTF-8编码写入
   ```

### 翻译处理流程
1. **翻译任务创建**
   ```python
   # 任务初始化
   worker = TranslateWorker(self.cues.copy(), self.cfg, mode)
   worker.update_row.connect(self._set_row)
   worker.start()
   ```

2. **异步并发处理**
   ```python
   # 并发控制
   sem = asyncio.Semaphore(MAX_CONCURRENCY)  # 8个并发限制
   
   # 任务分发
   tasks = [handle(i, c) for i, c in enumerate(self.cues)]
   for coro in asyncio.as_completed(tasks):
       result = await coro
   ```

3. **API 调用流程**
   ```
   字幕文本 → 提示词组装 → OpenAI API请求 → GPT模型处理
                                   ↓
   API响应 → _extract()解析 → 结果提取 → 文本内容
                                   ↓
   SubtitleCue更新 → Qt信号发送 → UI线程接收 → 表格刷新
   ```

### 事件驱动流程
1. **用户交互事件**
   ```
   鼠标点击 → Qt事件系统 → 信号发送 → 槽函数执行
                                   ↓
   业务逻辑处理 → 数据模型更新 → UI状态刷新
   ```

2. **异步任务事件**
   ```
   工作线程 → 任务完成 → Signal.emit() → 主线程槽函数
                                   ↓
   UI更新 → 进度显示 → 状态反馈 → 用户感知
   ```

### 配置管理流程
1. **配置读取**
   ```python
   CONFIG_PATH = Path(__file__).with_suffix(".config.json")
   if CONFIG_PATH.exists():
       data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
       cfg.api_key = data.get("api_key", "")
   ```

2. **配置保存**
   ```python
   data = {
       "api_key": cfg.api_key,
       "base_url": cfg.base_url,
       "model": cfg.model,
       "target_lang": cfg.target_lang,
   }
   CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))
   ```

## 数据格式规范

### SubtitleCue 数据结构
```python
@dataclass
class SubtitleCue:
    index: int           # 字幕序号 (1, 2, 3, ...)
    start: str          # 开始时间 "00:00:01,000"
    end: str            # 结束时间 "00:00:03,000"
    original: str       # 原始文本 "こんにちは"
    translation: str    # 翻译文本 "你好"
    fixed_text: str     # 修复文本 "你好！"
```

### Config 数据结构
```python
@dataclass
class Config:
    api_key: str = ""                # OpenAI API 密钥
    base_url: str = ""               # API 基础URL
    model: str = "gpt-4o-mini"       # GPT 模型名称
    target_lang: str = "中文"        # 目标语言
```

### SRT 文件格式
```
1
00:00:01,000 --> 00:00:03,000
原始字幕文本

2
00:00:04,000 --> 00:00:06,000
翻译后的字幕文本
```

### JSON 配置格式
```json
{
  "api_key": "sk-xxxxxxxxxxxxxxxx",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "target_lang": "中文"
}
```

### Qt 信号数据格式
```python
# 表格更新信号
update_row = Signal(int, str, str)  # (行号, 翻译文本, 修复文本)

# Token 统计信号
token_inc = Signal(int, int)        # (prompt_tokens, completion_tokens)

# 进度更新信号
progress = Signal(int, int)         # (已完成数, 总数)

# 任务完成信号
finished = Signal(str)              # (模式: "translate" or "fix")

# 错误报告信号
error = Signal(str)                 # (错误消息)
```

## 性能考量

### 并发控制策略
- **并发限制**: 8个同时进行的API请求
- **信号量控制**: `asyncio.Semaphore(MAX_CONCURRENCY)`
- **任务调度**: `asyncio.as_completed()` 按完成顺序处理结果
- **内存优化**: 工作线程使用数据副本避免竞争条件

### 异步处理优化
```python
# 异步客户端复用
client = AsyncOpenAI(api_key=self.cfg.api_key, base_url=self.cfg.base_url)

# 批量任务处理
tasks = [handle(i, c) for i, c in enumerate(self.cues)]
for coro in asyncio.as_completed(tasks):
    result = await coro
```

### UI 响应性保障
- **线程分离**: UI线程与工作线程分离
- **异步非阻塞**: 长时间操作在工作线程执行
- **实时反馈**: Qt信号机制实现实时进度更新
- **用户交互**: 翻译过程中UI保持可操作性

### 内存管理策略
- **数据复制**: 翻译前复制字幕数据避免UI阻塞
- **历史管理**: 操作历史栈支持撤销功能
- **垃圾回收**: Python自动内存管理
- **资源释放**: 文件句柄和网络连接及时关闭

### 网络性能优化
- **超时控制**: 25秒API调用超时
- **错误重试**: 网络错误的自动重试机制
- **连接复用**: AsyncOpenAI客户端连接池
- **响应解析**: 统一的API响应解析器 `_extract()`

### 数据持久化性能
- **即时保存**: 配置更改后立即写入文件
- **原子操作**: 文件写入的原子性保证
- **编码优化**: UTF-8编码处理中文字符
- **缓存策略**: 配置数据内存缓存减少文件IO
# Subtitle Translation Tools 技术栈

## 核心技术

### 编程语言

**Python 3.8+**
- **选择理由**: 
  - 丰富的 AI/ML 生态系统支持
  - 优秀的异步编程能力 (`asyncio`)
  - 成熟的 GUI 开发框架
  - 跨平台兼容性好
- **版本要求**: Python 3.8+ (支持现代异步语法)
- **关键特性**: 
  - Type Hints 支持静态类型检查
  - Dataclasses 简化数据结构定义
  - Pathlib 现代文件路径处理
  - 内置 JSON 支持和 Unicode 处理

**关键语言特性使用**:
```python
# 现代数据结构定义
@dataclass
class SubtitleCue:
    index: int
    start: str
    end: str
    original: str
    translation: str = ""
    fixed_text: str = ""

# 异步编程模式
async def _main(self):
    async with AsyncOpenAI() as client:
        tasks = [handle(i, c) for i, c in enumerate(self.cues)]
        for coro in asyncio.as_completed(tasks):
            result = await coro
```

### 架构模式

**桌面应用 MVC 架构**
- **Model**: `SubtitleCue`, `Config` 数据模型
- **View**: PySide6 GUI 组件 (`MainWindow`, `SettingsDialog`)
- **Controller**: 业务逻辑控制器和事件处理器

**异步处理模式**
- **主线程**: UI 响应和用户交互
- **工作线程**: `TranslateWorker` (QThread) 处理耗时操作
- **事件驱动**: Qt 信号槽机制实现组件间通信

**并发控制模式**
```python
# 信号量控制并发数量
sem = asyncio.Semaphore(MAX_CONCURRENCY)  # 8 个并发限制

# 异步任务调度
async with sem:
    result = await client.chat.completions.create(...)
```

**错误处理模式**
- **分层异常处理**: API 级 → 服务级 → UI 级
- **优雅降级**: 网络错误时的备用策略
- **用户友好的错误报告**: 技术错误转换为用户可理解的消息

### 数据格式

**SRT 字幕格式**
```
1
00:00:01,000 --> 00:00:03,000
原始字幕文本

2
00:00:04,000 --> 00:00:06,000
翻译后的字幕文本
```
- **标准兼容**: 遵循 SubRip 标准格式
- **编码支持**: UTF-8 编码确保多语言支持
- **时间轴格式**: `HH:MM:SS,mmm --> HH:MM:SS,mmm`

**JSON 配置格式**
```json
{
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini", 
  "target_lang": "中文"
}
```
- **结构化配置**: 键值对映射
- **类型安全**: 通过 dataclass 进行验证
- **人类可读**: 易于手动编辑和调试

### 文件系统操作

**现代路径处理 (pathlib)**
```python
CONFIG_PATH = Path(__file__).with_suffix(".config.json")
```
- **跨平台兼容**: 自动处理路径分隔符
- **类型安全**: 路径对象 vs 字符串
- **链式操作**: 支持方法链式调用

**文件 I/O 策略**
- **编码处理**: 统一使用 UTF-8 编码
- **错误容错**: `errors="ignore"` 处理编码问题
- **流式处理**: 逐行读取大文件避免内存问题

### 依赖策略

**核心依赖管理**
```
PySide6>=6.6.0          # Qt6 GUI 框架
openai>=1.0.0           # OpenAI 官方 SDK
```

**依赖选择原则**
- **最小化原则**: 只引入必要的依赖
- **稳定性优先**: 选择成熟稳定的库
- **官方优先**: 优先使用官方维护的 SDK
- **版本锁定**: 指定最低兼容版本

**依赖分层**
- **UI 层**: PySide6 (Qt6 Python 绑定)
- **AI 层**: OpenAI SDK (官方 Python 客户端)
- **系统层**: Python 标准库 (asyncio, logging, json)

### 配置管理

**分层配置系统**
```python
# 默认配置
@dataclass
class Config:
    api_key: str = ""
    base_url: str = ""
    model: str = "gpt-4o-mini"  # 默认模型
    target_lang: str = "中文"    # 默认语言

# 文件配置覆盖
def load_config() -> Config:
    cfg = Config()  # 默认值
    if CONFIG_PATH.exists():
        data = json.loads(CONFIG_PATH.read_text())
        cfg.api_key = data.get("api_key", cfg.api_key)
        # ... 其他字段覆盖
    return cfg
```

**配置持久化策略**
- **即时保存**: 设置更改后立即写入文件
- **原子操作**: 文件写入的原子性保证
- **备份机制**: 配置加载失败时使用默认值
- **安全性**: 配置文件权限控制

**环境适配**
- **开发环境**: 本地配置文件
- **生产环境**: 同目录配置文件
- **便携模式**: 相对路径配置

## 版本兼容性

**Python 版本兼容性**
- **最低要求**: Python 3.8+
- **推荐版本**: Python 3.10+
- **测试版本**: Python 3.8, 3.9, 3.10, 3.11, 3.12

**依赖版本策略**
```
PySide6>=6.6.0          # 支持现代 Qt6 特性
openai>=1.0.0           # 新版 API 接口
```

**向后兼容性**
- **配置文件**: 新版本自动兼容旧格式配置
- **数据格式**: SRT 格式向后兼容
- **API 接口**: 自动适配不同 OpenAI API 版本

**操作系统兼容性**
- **Windows**: Windows 10+ (GUI 子系统)
- **macOS**: macOS 10.14+ (64位系统)
- **Linux**: Ubuntu 18.04+ / CentOS 7+ (X11 或 Wayland)

## 部署架构

**单机部署模式**
```
应用程序目录/
├── main.py              # 主程序文件
├── main.config.json     # 配置文件 (运行时生成)
├── translator.log       # 日志文件 (运行时生成)
└── docs/                # 文档目录
```

**运行时依赖**
- **Python Runtime**: 解释器 + 标准库
- **GUI 子系统**: 操作系统图形界面支持
- **网络栈**: HTTP/HTTPS 网络通信
- **文件系统**: 读写权限和 UTF-8 支持

**资源需求**
- **CPU**: 双核心 2GHz+ (推荐四核心)
- **内存**: 4GB+ RAM (推荐 8GB+)
- **存储**: 100MB+ 可用空间
- **网络**: 1Mbps+ 稳定连接 (推荐 5Mbps+)

**部署流程**
1. **环境准备**: Python 3.8+ 安装
2. **依赖安装**: `pip install PySide6 openai`
3. **程序启动**: `python main.py`
4. **配置设置**: GUI 设置对话框配置 API

**维护和监控**
- **日志轮转**: 日志文件大小控制
- **配置备份**: 重要配置文件备份
- **性能监控**: API 调用量和响应时间
- **错误报告**: 异常堆栈跟踪和错误统计

**安全考虑**
- **API 密钥保护**: 本地文件存储 (建议加密)
- **网络安全**: HTTPS 传输加密
- **文件权限**: 配置文件访问权限控制
- **输入验证**: 用户输入数据验证和清理
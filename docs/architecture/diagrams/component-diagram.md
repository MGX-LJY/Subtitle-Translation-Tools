# Subtitle Translation Tools 组件关系图

## 核心组件依赖关系

```mermaid
graph TB
    subgraph "UI Components"
        MW[MainWindow<br/>主窗口控制器]
        SD[SettingsDialog<br/>设置对话框]
        TW_UI[TableWidget<br/>字幕表格]
        TB[ToolBar<br/>工具栏]
        SB[StatusBar<br/>状态栏]
    end
    
    subgraph "Data Models"
        SC[SubtitleCue<br/>字幕数据模型]
        CF[Config<br/>配置数据模型]
    end
    
    subgraph "Service Layer"
        TW[TranslateWorker<br/>翻译服务]
        FS[FileService<br/>文件处理服务]
        CS[ConfigService<br/>配置服务]
    end
    
    subgraph "External Dependencies"
        OAI[OpenAI<br/>API客户端]
        QT[PySide6<br/>GUI框架]
        SYS[System<br/>文件系统]
    end
    
    MW --> SD
    MW --> TW_UI
    MW --> TB
    MW --> SB
    MW --> TW
    MW --> FS
    MW --> CS
    MW --> SC
    MW --> CF
    
    SD --> CS
    SD --> CF
    
    TW --> OAI
    TW --> SC
    
    FS --> SC
    FS --> SYS
    
    CS --> CF
    CS --> SYS
    
    MW --> QT
    SD --> QT
    TW_UI --> QT
    TB --> QT
    SB --> QT
```

## 详细组件接口

### 数据模型组件
```mermaid
classDiagram
    class SubtitleCue {
        +int index
        +str start
        +str end
        +str original
        +str translation
        +str fixed_text
    }
    
    class Config {
        +str api_key
        +str base_url
        +str model
        +str target_lang
        +load_config() Config
        +save_config(Config) void
    }
    
    SubtitleCue "1..*" --o "1" MainWindow : manages
    Config "1" --o "1" MainWindow : uses
```

### 服务层组件
```mermaid
classDiagram
    class TranslateWorker {
        +List~SubtitleCue~ cues
        +Config cfg
        +str mode
        +int MAX_CONCURRENCY
        +run() void
        +_main() async void
        +_extract(response) tuple
        
        <<signals>>
        +update_row(int, str, str)
        +token_inc(int, int)
        +progress(int, int)
        +finished(str)
        +error(str)
    }
    
    class FileService {
        +parse_srt(Path) List~SubtitleCue~
        +write_srt(Path, List~SubtitleCue~) void
        +_blk_to_cue(list, list) void
    }
    
    class ConfigService {
        +load_config() Config
        +save_config(Config) void
        +CONFIG_PATH Path
    }
    
    TranslateWorker --> SubtitleCue : processes
    TranslateWorker --> Config : uses
    FileService --> SubtitleCue : creates/saves
    ConfigService --> Config : manages
```

### UI组件层次
```mermaid
graph TB
    subgraph "MainWindow Components"
        MW_CORE[MainWindow Core]
        MW_UI[UI Setup Method]
        MW_EVENTS[Event Handlers]
        MW_REFRESH[Refresh Methods]
    end
    
    subgraph "Widget Components"
        TABLE[QTableWidget<br/>字幕编辑表格]
        TOOLBAR[QToolBar<br/>操作工具栏]
        PROGRESS[QProgressBar<br/>进度指示器]
        STATUS[QStatusBar<br/>状态显示]
    end
    
    subgraph "Dialog Components"
        SETTINGS[SettingsDialog<br/>配置对话框]
        FILE_DLG[QFileDialog<br/>文件选择]
        MSG_BOX[QMessageBox<br/>消息提示]
    end
    
    MW_CORE --> MW_UI
    MW_CORE --> MW_EVENTS
    MW_CORE --> MW_REFRESH
    
    MW_UI --> TABLE
    MW_UI --> TOOLBAR
    MW_UI --> PROGRESS
    MW_UI --> STATUS
    
    MW_EVENTS --> SETTINGS
    MW_EVENTS --> FILE_DLG
    MW_EVENTS --> MSG_BOX
```

## 组件间通信机制

### 信号槽通信图
```mermaid
graph LR
    subgraph "TranslateWorker Signals"
        S1[update_row]
        S2[token_inc]
        S3[progress]
        S4[finished]
        S5[error]
    end
    
    subgraph "MainWindow Slots"
        SLOT1[_set_row]
        SLOT2[_add_tok]
        SLOT3[setValue]
        SLOT4[showMessage]
        SLOT5[critical]
    end
    
    subgraph "UI Updates"
        U1[Table Row Update]
        U2[Token Counter]
        U3[Progress Bar]
        U4[Status Message]
        U5[Error Dialog]
    end
    
    S1 --> SLOT1 --> U1
    S2 --> SLOT2 --> U2
    S3 --> SLOT3 --> U3
    S4 --> SLOT4 --> U4
    S5 --> SLOT5 --> U5
```

### 数据流组件交互
```mermaid
sequenceDiagram
    participant UI as MainWindow
    participant FS as FileService
    participant DM as DataModel
    participant TW as TranslateWorker
    participant API as OpenAI
    
    UI->>FS: open_file()
    FS->>FS: parse_srt()
    FS->>DM: create SubtitleCue list
    FS->>UI: return cues
    UI->>UI: _refresh() table
    
    UI->>TW: translate_all()
    TW->>TW: start() thread
    TW->>API: async requests
    API->>TW: responses
    TW->>UI: update_row signal
    UI->>UI: _set_row()
```

## 组件配置和初始化

### 应用程序启动序列
```mermaid
graph TB
    START[程序启动] --> INIT_APP[QApplication 初始化]
    INIT_APP --> LOAD_CONFIG[加载配置文件]
    LOAD_CONFIG --> CREATE_WINDOW[创建主窗口]
    CREATE_WINDOW --> SETUP_UI[构建UI组件]
    SETUP_UI --> CONNECT_SIGNALS[连接信号槽]
    CONNECT_SIGNALS --> SHOW_WINDOW[显示窗口]
    SHOW_WINDOW --> EVENT_LOOP[进入事件循环]
    
    LOAD_CONFIG --> CONFIG_OBJ[Config 对象]
    CONFIG_OBJ --> CREATE_WINDOW
    
    SETUP_UI --> TABLE_INIT[表格初始化]
    SETUP_UI --> TOOLBAR_INIT[工具栏初始化]
    SETUP_UI --> STATUS_INIT[状态栏初始化]
    
    CONNECT_SIGNALS --> BUTTON_SIGNALS[按钮信号连接]
    CONNECT_SIGNALS --> WORKER_SIGNALS[工作线程信号连接]
```

### 翻译服务初始化
```mermaid
graph TB
    USER_ACTION[用户点击翻译] --> VALIDATE_INPUT[验证输入数据]
    VALIDATE_INPUT --> COPY_DATA[复制字幕数据]
    COPY_DATA --> CREATE_WORKER[创建 TranslateWorker]
    CREATE_WORKER --> CONNECT_WORKER[连接工作线程信号]
    CONNECT_WORKER --> START_WORKER[启动工作线程]
    START_WORKER --> ASYNC_LOOP[异步事件循环]
    ASYNC_LOOP --> CONCURRENT_TASKS[并发任务处理]
    CONCURRENT_TASKS --> API_CALLS[OpenAI API 调用]
    API_CALLS --> RESULT_PROCESSING[结果处理]
    RESULT_PROCESSING --> UI_UPDATE[UI 更新]
```

## 组件职责分离

### 单一职责原则应用
```mermaid
graph TB
    subgraph "数据层职责"
        DR1[数据模型定义]
        DR2[数据验证]
        DR3[数据持久化]
    end
    
    subgraph "业务层职责"
        BR1[翻译逻辑]
        BR2[文件处理]
        BR3[配置管理]
    end
    
    subgraph "表现层职责"
        PR1[用户界面]
        PR2[用户交互]
        PR3[状态显示]
    end
    
    subgraph "控制层职责"
        CR1[事件处理]
        CR2[流程控制]
        CR3[组件协调]
    end
    
    DR1 --> BR1
    DR2 --> BR2
    DR3 --> BR3
    
    BR1 --> CR1
    BR2 --> CR2
    BR3 --> CR3
    
    CR1 --> PR1
    CR2 --> PR2
    CR3 --> PR3
```

### 依赖注入模式
```mermaid
graph TB
    subgraph "依赖接口"
        I1[ITranslationService]
        I2[IFileService]
        I3[IConfigService]
    end
    
    subgraph "具体实现"
        IMPL1[OpenAITranslationService]
        IMPL2[SRTFileService]
        IMPL3[JSONConfigService]
    end
    
    subgraph "使用者"
        MW[MainWindow]
        TW[TranslateWorker]
    end
    
    I1 --> IMPL1
    I2 --> IMPL2
    I3 --> IMPL3
    
    MW --> I2
    MW --> I3
    TW --> I1
```

## 扩展性设计

### 插件化架构潜力
```mermaid
graph TB
    subgraph "核心框架"
        CORE[Core Application]
        PLUGIN_MGR[Plugin Manager]
        EVENT_BUS[Event Bus]
    end
    
    subgraph "翻译服务插件"
        OPENAI[OpenAI Plugin]
        GOOGLE[Google Translate Plugin]
        AZURE[Azure Translator Plugin]
    end
    
    subgraph "文件格式插件"
        SRT[SRT Plugin]
        VTT[VTT Plugin]
        ASS[ASS Plugin]
    end
    
    CORE --> PLUGIN_MGR
    PLUGIN_MGR --> EVENT_BUS
    
    EVENT_BUS --> OPENAI
    EVENT_BUS --> GOOGLE
    EVENT_BUS --> AZURE
    
    EVENT_BUS --> SRT
    EVENT_BUS --> VTT
    EVENT_BUS --> ASS
```

### 配置驱动的组件系统
```mermaid
graph LR
    CONFIG[配置文件] --> FACTORY[组件工厂]
    FACTORY --> TRANSLATION[翻译组件]
    FACTORY --> FILE[文件组件]
    FACTORY --> UI[界面组件]
    
    TRANSLATION --> SERVICE1[OpenAI服务]
    TRANSLATION --> SERVICE2[本地服务]
    
    FILE --> FORMAT1[SRT格式]
    FILE --> FORMAT2[VTT格式]
    
    UI --> THEME1[默认主题]
    UI --> THEME2[暗色主题]
```

这个组件关系图展示了系统的模块化设计，清晰地定义了各组件的职责边界和交互方式，为后续的扩展和维护提供了良好的架构基础。
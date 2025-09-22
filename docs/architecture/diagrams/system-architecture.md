# Subtitle Translation Tools 系统架构图

## 整体系统架构

```mermaid
graph TB
    subgraph "用户层 (User Layer)"
        U1[用户]
    end
    
    subgraph "表现层 (Presentation Layer)"
        UI1[MainWindow - 主窗口]
        UI2[SettingsDialog - 设置对话框]
        UI3[QTableWidget - 字幕表格]
        UI4[工具栏 & 状态栏]
    end
    
    subgraph "控制层 (Controller Layer)"
        C1[事件处理器]
        C2[文件操作控制器]
        C3[翻译任务控制器]
        C4[配置管理控制器]
    end
    
    subgraph "服务层 (Service Layer)"
        S1[TranslateWorker - 翻译服务]
        S2[SRT文件处理服务]
        S3[配置管理服务]
        S4[日志服务]
    end
    
    subgraph "数据层 (Data Layer)"
        D1[SubtitleCue - 字幕数据模型]
        D2[Config - 配置数据模型]
        D3[JSON配置文件]
        D4[SRT字幕文件]
        D5[日志文件]
    end
    
    subgraph "外部服务 (External Services)"
        E1[OpenAI API]
        E2[文件系统]
        E3[网络服务]
    end
    
    U1 --> UI1
    UI1 --> UI2
    UI1 --> UI3
    UI1 --> UI4
    
    UI1 --> C1
    UI2 --> C4
    UI3 --> C2
    UI4 --> C3
    
    C1 --> S1
    C2 --> S2
    C3 --> S1
    C4 --> S3
    
    S1 --> D1
    S2 --> D1
    S2 --> D4
    S3 --> D2
    S3 --> D3
    S4 --> D5
    
    S1 --> E1
    S2 --> E2
    S3 --> E2
    S4 --> E2
```

## 详细组件架构

### 用户界面层架构
```mermaid
graph TB
    subgraph "MainWindow - 主窗口"
        MW1[工具栏 - QToolBar]
        MW2[字幕表格 - QTableWidget]
        MW3[进度条 - QProgressBar]
        MW4[状态栏 - QStatusBar]
        MW5[菜单系统]
    end
    
    subgraph "对话框系统"
        D1[SettingsDialog - 设置]
        D2[QFileDialog - 文件选择]
        D3[QMessageBox - 消息提示]
    end
    
    subgraph "事件系统"
        E1[鼠标事件]
        E2[键盘事件]
        E3[菜单事件]
        E4[按钮事件]
    end
    
    MW1 --> E3
    MW1 --> E4
    MW2 --> E1
    MW2 --> E2
    MW5 --> D1
    MW5 --> D2
    
    E1 --> D3
    E2 --> D3
    E3 --> D3
    E4 --> D3
```

### 异步处理架构
```mermaid
graph TB
    subgraph "主线程 (UI Thread)"
        UI[用户界面]
        MC[主控制器]
        SIG[信号处理器]
    end
    
    subgraph "工作线程 (Worker Thread)"
        TW[TranslateWorker]
        AE[异步事件循环]
        TM[任务管理器]
    end
    
    subgraph "异步任务池"
        T1[翻译任务1]
        T2[翻译任务2]
        T3[翻译任务N]
        SEM[信号量控制器<br/>Semaphore(8)]
    end
    
    subgraph "外部API"
        API[OpenAI API]
        NET[网络层]
    end
    
    UI --> MC
    MC --> TW
    TW --> AE
    AE --> TM
    TM --> SEM
    
    SEM --> T1
    SEM --> T2
    SEM --> T3
    
    T1 --> API
    T2 --> API
    T3 --> API
    
    API --> NET
    
    T1 --> SIG
    T2 --> SIG
    T3 --> SIG
    SIG --> UI
```

### 数据流架构
```mermaid
graph LR
    subgraph "输入数据"
        I1[SRT文件]
        I2[用户配置]
        I3[用户操作]
    end
    
    subgraph "数据处理层"
        P1[SRT解析器]
        P2[配置验证器]
        P3[事件处理器]
    end
    
    subgraph "数据模型层"
        M1[SubtitleCue列表]
        M2[Config对象]
        M3[应用状态]
    end
    
    subgraph "业务逻辑层"
        B1[翻译处理器]
        B2[文件管理器]
        B3[配置管理器]
    end
    
    subgraph "输出数据"
        O1[翻译后SRT]
        O2[更新的配置]
        O3[用户反馈]
    end
    
    I1 --> P1 --> M1 --> B1 --> O1
    I2 --> P2 --> M2 --> B3 --> O2
    I3 --> P3 --> M3 --> B2 --> O3
```

## 模块间依赖关系

### 核心模块依赖图
```mermaid
graph TB
    subgraph "配置模块"
        CM1[Config dataclass]
        CM2[load_config()]
        CM3[save_config()]
    end
    
    subgraph "数据模型模块"
        DM1[SubtitleCue dataclass]
        DM2[数据验证]
        DM3[类型转换]
    end
    
    subgraph "文件处理模块"
        FM1[parse_srt()]
        FM2[write_srt()]
        FM3[_blk_to_cue()]
    end
    
    subgraph "翻译服务模块"
        TS1[TranslateWorker]
        TS2[_main() - 异步逻辑]
        TS3[_extract() - 响应解析]
    end
    
    subgraph "UI控制模块"
        UC1[MainWindow]
        UC2[SettingsDialog]
        UC3[事件处理方法]
    end
    
    CM1 --> UC1
    CM2 --> UC1
    CM3 --> UC2
    
    DM1 --> FM1
    DM1 --> FM2
    DM1 --> TS1
    
    FM1 --> UC1
    FM2 --> UC1
    FM3 --> FM1
    
    TS1 --> UC1
    TS2 --> TS1
    TS3 --> TS2
    
    UC2 --> CM3
    UC3 --> TS1
```

### 信号槽连接架构
```mermaid
graph TB
    subgraph "TranslateWorker 信号"
        S1[update_row<br/>Signal(int,str,str)]
        S2[token_inc<br/>Signal(int,int)]
        S3[progress<br/>Signal(int,int)]
        S4[finished<br/>Signal(str)]
        S5[error<br/>Signal(str)]
    end
    
    subgraph "MainWindow 槽函数"
        SLOT1[_set_row()<br/>更新表格行]
        SLOT2[_add_tok()<br/>更新Token计数]
        SLOT3[setValue()<br/>更新进度条]
        SLOT4[showMessage()<br/>显示完成消息]
        SLOT5[critical()<br/>显示错误对话框]
    end
    
    subgraph "UI 组件更新"
        UI1[QTableWidget<br/>表格更新]
        UI2[QLabel<br/>Token显示]
        UI3[QProgressBar<br/>进度显示]
        UI4[QStatusBar<br/>状态显示]
        UI5[QMessageBox<br/>错误提示]
    end
    
    S1 --> SLOT1 --> UI1
    S2 --> SLOT2 --> UI2
    S3 --> SLOT3 --> UI3
    S4 --> SLOT4 --> UI4
    S5 --> SLOT5 --> UI5
```

## 系统交互流程

### 典型用户操作流程
```mermaid
sequenceDiagram
    participant U as 用户
    participant UI as 主界面
    participant C as 控制器
    participant W as 翻译服务
    participant API as OpenAI API
    
    U->>UI: 点击"打开"按钮
    UI->>C: 触发文件选择
    C->>UI: 显示文件对话框
    U->>UI: 选择SRT文件
    UI->>C: 返回文件路径
    C->>C: 解析SRT文件
    C->>UI: 更新表格显示
    
    U->>UI: 点击"全部翻译"
    UI->>C: 启动翻译任务
    C->>W: 创建翻译Worker
    W->>W: 启动异步处理
    
    loop 并发翻译处理
        W->>API: 发送翻译请求
        API->>W: 返回翻译结果
        W->>UI: 发送更新信号
        UI->>UI: 更新表格行
    end
    
    W->>UI: 发送完成信号
    UI->>U: 显示完成消息
```

### 配置管理流程
```mermaid
sequenceDiagram
    participant U as 用户
    participant SD as 设置对话框
    participant C as 配置管理器
    participant F as 配置文件
    
    U->>SD: 打开设置对话框
    SD->>C: 请求当前配置
    C->>F: 读取JSON文件
    F->>C: 返回配置数据
    C->>SD: 显示当前配置
    
    U->>SD: 修改配置项
    U->>SD: 点击保存按钮
    SD->>C: 提交新配置
    C->>C: 验证配置数据
    C->>F: 写入JSON文件
    F->>C: 确认保存成功
    C->>SD: 返回保存结果
    SD->>U: 关闭对话框
```

## 安全架构考虑

### 数据安全架构
```mermaid
graph TB
    subgraph "数据保护层"
        DP1[输入验证]
        DP2[类型检查]
        DP3[编码处理]
    end
    
    subgraph "网络安全层"
        NS1[HTTPS传输]
        NS2[API密钥管理]
        NS3[超时控制]
    end
    
    subgraph "文件安全层"
        FS1[权限检查]
        FS2[路径验证]
        FS3[编码安全]
    end
    
    subgraph "错误处理层"
        EH1[异常捕获]
        EH2[错误日志]
        EH3[用户友好提示]
    end
    
    DP1 --> NS1
    DP2 --> NS2
    DP3 --> NS3
    
    NS1 --> FS1
    NS2 --> FS2
    NS3 --> FS3
    
    FS1 --> EH1
    FS2 --> EH2
    FS3 --> EH3
```

### 系统健壮性架构
```mermaid
graph TB
    subgraph "容错机制"
        FT1[网络重试]
        FT2[API降级]
        FT3[数据恢复]
    end
    
    subgraph "监控机制"
        M1[性能监控]
        M2[错误跟踪]
        M3[资源监控]
    end
    
    subgraph "恢复机制"
        R1[状态回滚]
        R2[配置重置]
        R3[缓存清理]
    end
    
    FT1 --> M1 --> R1
    FT2 --> M2 --> R2
    FT3 --> M3 --> R3
```

这个系统架构图展示了 Subtitle Translation Tools 的完整技术架构，包括各层级的组件关系、数据流向、以及关键的安全和健壮性考虑。架构设计强调了模块化、可扩展性和用户体验的平衡。
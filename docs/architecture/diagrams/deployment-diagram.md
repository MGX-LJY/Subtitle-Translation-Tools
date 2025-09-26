# Subtitle Translation Tools 部署架构

## 单机部署架构

```mermaid
deployment
    node "用户桌面环境" {
        node "操作系统层" {
            component "Windows 10+/macOS 10.14+/Linux"
            component "GUI子系统 (X11/Wayland/GDI)"
            component "文件系统 (NTFS/APFS/ext4)"
            component "网络栈 (TCP/IP)"
        }
        
        node "Python运行时环境" {
            component "Python 3.8+ 解释器"
            component "标准库 (asyncio, json, logging)"
            component "第三方依赖包"
        }
        
        node "应用程序层" {
            artifact "main.py" as APP
            artifact "main.config.json" as CONFIG
            artifact "translator.log" as LOG
        }
        
        node "依赖库" {
            component "PySide6 (GUI框架)"
            component "OpenAI SDK (API客户端)"
        }
    }
    
    cloud "外部服务" {
        node "OpenAI 服务" {
            interface "API Gateway"
            component "GPT-4o-mini"
            component "GPT-4o"
        }
    }
    
    APP --> CONFIG : 读写配置
    APP --> LOG : 写入日志
    APP ..> "OpenAI 服务" : HTTPS API调用
```

## 详细部署组件

### 系统依赖层
```mermaid
graph TB
    subgraph "硬件层"
        CPU[CPU: 双核2GHz+<br/>推荐: 四核心]
        MEM[内存: 4GB+<br/>推荐: 8GB+]
        DISK[存储: 100MB+<br/>推荐: SSD]
        NET[网络: 1Mbps+<br/>推荐: 5Mbps+]
    end
    
    subgraph "操作系统层"
        OS_WIN[Windows 10+]
        OS_MAC[macOS 10.14+]
        OS_LINUX[Ubuntu 18.04+]
        GUI_SYS[GUI子系统支持]
    end
    
    subgraph "运行时环境"
        PY_RT[Python 3.8+ Runtime]
        SYS_LIBS[系统标准库]
        PKG_MGR[包管理器 (pip)]
    end
    
    CPU --> OS_WIN
    CPU --> OS_MAC
    CPU --> OS_LINUX
    MEM --> GUI_SYS
    
    OS_WIN --> PY_RT
    OS_MAC --> PY_RT
    OS_LINUX --> PY_RT
    GUI_SYS --> SYS_LIBS
    
    PY_RT --> PKG_MGR
```

### 应用程序部署结构
```mermaid
graph TB
    subgraph "应用程序目录"
        MAIN[main.py<br/>主程序文件<br/>17.25KB]
        
        subgraph "运行时生成文件"
            CONFIG[main.config.json<br/>配置文件<br/>~200B]
            LOG[translator.log<br/>日志文件<br/>动态大小]
        end
        
        subgraph "文档目录 (可选)"
            DOCS[docs/<br/>项目文档<br/>~1MB]
            README[README.md<br/>使用说明]
        end
    end
    
    subgraph "Python环境依赖"
        PYSIDE[PySide6>=6.6.0<br/>GUI框架<br/>~100MB]
        OPENAI[openai>=1.0.0<br/>API客户端<br/>~5MB]
        STDLIB[Python标准库<br/>asyncio, json, logging]
    end
    
    MAIN --> CONFIG
    MAIN --> LOG
    MAIN --> PYSIDE
    MAIN --> OPENAI
    MAIN --> STDLIB
```

## 网络架构

### 网络连接图
```mermaid
graph TB
    subgraph "本地环境"
        APP[Subtitle Translation Tools]
        FW[防火墙/代理]
    end
    
    subgraph "网络层"
        ISP[互联网服务提供商]
        DNS[DNS解析]
    end
    
    subgraph "OpenAI基础设施"
        subgraph "API Gateway"
            LB[负载均衡器]
            RATE[速率限制器]
            AUTH[认证服务]
        end
        
        subgraph "AI服务"
            GPT4O_MINI[GPT-4o-mini]
            GPT4O[GPT-4o]
            OTHER[其他模型]
        end
    end
    
    APP --> FW
    FW --> ISP
    ISP --> DNS
    DNS --> LB
    LB --> RATE
    RATE --> AUTH
    AUTH --> GPT4O_MINI
    AUTH --> GPT4O
    AUTH --> OTHER
```

### API通信流程
```mermaid
sequenceDiagram
    participant App as 翻译应用
    participant Net as 网络层
    participant API as OpenAI API
    participant GPT as GPT模型
    
    App->>Net: HTTPS请求 (端口443)
    Net->>API: 转发请求
    API->>API: 认证API密钥
    API->>API: 速率限制检查
    API->>GPT: 调用模型推理
    GPT->>API: 返回翻译结果
    API->>Net: HTTPS响应
    Net->>App: 接收响应数据
    
    Note over App,GPT: 支持并发8个请求
    Note over Net,API: 25秒超时设置
```

## 配置管理部署

### 配置文件部署策略
```mermaid
graph TB
    subgraph "配置层次"
        DEFAULT[默认配置<br/>硬编码在代码中]
        LOCAL[本地配置文件<br/>main.config.json]
        USER[用户设置<br/>GUI配置对话框]
    end
    
    subgraph "配置存储"
        JSON_FILE[JSON配置文件<br/>UTF-8编码<br/>同目录存储]
        MEMORY[内存中的Config对象<br/>运行时状态]
    end
    
    subgraph "配置安全"
        PERM[文件权限控制<br/>仅用户可读写]
        BACKUP[配置备份机制<br/>错误时使用默认值]
    end
    
    DEFAULT --> LOCAL
    LOCAL --> USER
    USER --> JSON_FILE
    JSON_FILE --> MEMORY
    
    JSON_FILE --> PERM
    MEMORY --> BACKUP
```

### 环境适配部署
```mermaid
graph LR
    subgraph "开发环境"
        DEV_CONFIG[开发配置<br/>调试API密钥<br/>本地日志级别]
    end
    
    subgraph "测试环境"
        TEST_CONFIG[测试配置<br/>测试API密钥<br/>详细日志]
    end
    
    subgraph "生产环境"
        PROD_CONFIG[生产配置<br/>正式API密钥<br/>精简日志]
    end
    
    subgraph "便携环境"
        PORT_CONFIG[便携配置<br/>相对路径<br/>自包含部署]
    end
    
    DEV_CONFIG --> TEST_CONFIG
    TEST_CONFIG --> PROD_CONFIG
    PROD_CONFIG --> PORT_CONFIG
```

## 安装部署流程

### 标准安装流程
```mermaid
graph TB
    START[开始安装] --> CHECK_PYTHON[检查Python版本>=3.8]
    CHECK_PYTHON --> INSTALL_DEPS[安装依赖包<br/>pip install PySide6 openai]
    INSTALL_DEPS --> DOWNLOAD_APP[下载应用程序<br/>main.py]
    DOWNLOAD_APP --> FIRST_RUN[首次运行<br/>python main.py]
    FIRST_RUN --> CONFIG_SETUP[配置API密钥<br/>设置对话框]
    CONFIG_SETUP --> TEST_CONNECTION[测试API连接]
    TEST_CONNECTION --> READY[安装完成<br/>可以使用]
    
    CHECK_PYTHON --> INSTALL_PYTHON[安装Python 3.8+]
    INSTALL_PYTHON --> CHECK_PYTHON
    
    TEST_CONNECTION --> FIX_CONFIG[修复配置问题]
    FIX_CONFIG --> CONFIG_SETUP
```

### 自动化部署脚本
```bash
#!/bin/bash
# 部署脚本示例

# 检查Python版本
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
if (( $(echo "$python_version < 3.8" | bc -l) )); then
    echo "Error: Python 3.8+ required"
    exit 1
fi

# 安装依赖
pip install PySide6>=6.6.0 openai>=1.0.0

# 下载主程序
wget https://example.com/main.py -O main.py

# 设置执行权限
chmod +x main.py

# 创建启动脚本
cat > start_translator.sh << EOF
#!/bin/bash
cd "$(dirname "$0")"
python3 main.py
EOF

chmod +x start_translator.sh

echo "安装完成! 运行 ./start_translator.sh 启动应用"
```

## 监控和维护部署

### 日志管理部署
```mermaid
graph TB
    subgraph "日志生成"
        APP_LOG[应用程序日志<br/>INFO级别]
        ERROR_LOG[错误日志<br/>ERROR级别]
        PERF_LOG[性能日志<br/>API调用时间]
    end
    
    subgraph "日志存储"
        FILE_LOG[文件日志<br/>translator.log]
        CONSOLE_LOG[控制台日志<br/>实时输出]
        ROTATE_LOG[日志轮转<br/>大小限制]
    end
    
    subgraph "日志分析"
        LOG_PARSER[日志解析器]
        METRICS[性能指标]
        ALERTS[异常告警]
    end
    
    APP_LOG --> FILE_LOG
    ERROR_LOG --> FILE_LOG
    PERF_LOG --> FILE_LOG
    
    APP_LOG --> CONSOLE_LOG
    ERROR_LOG --> CONSOLE_LOG
    
    FILE_LOG --> ROTATE_LOG
    ROTATE_LOG --> LOG_PARSER
    LOG_PARSER --> METRICS
    LOG_PARSER --> ALERTS
```

### 健康检查部署
```mermaid
graph TB
    subgraph "健康检查项"
        API_CHECK[API连接检查]
        CONFIG_CHECK[配置文件检查]
        DEPS_CHECK[依赖包检查]
        DISK_CHECK[磁盘空间检查]
    end
    
    subgraph "监控脚本"
        HEALTH_SCRIPT[health_check.py]
        CRON_JOB[定时任务]
        ALERT_SYSTEM[告警系统]
    end
    
    subgraph "响应策略"
        AUTO_RESTART[自动重启]
        CONFIG_RESET[配置重置]
        ADMIN_NOTIFY[管理员通知]
    end
    
    API_CHECK --> HEALTH_SCRIPT
    CONFIG_CHECK --> HEALTH_SCRIPT
    DEPS_CHECK --> HEALTH_SCRIPT
    DISK_CHECK --> HEALTH_SCRIPT
    
    HEALTH_SCRIPT --> CRON_JOB
    CRON_JOB --> ALERT_SYSTEM
    
    ALERT_SYSTEM --> AUTO_RESTART
    ALERT_SYSTEM --> CONFIG_RESET
    ALERT_SYSTEM --> ADMIN_NOTIFY
```

## 扩展部署架构

### 多用户部署模式
```mermaid
graph TB
    subgraph "共享服务器"
        SHARED_SERVER[共享服务器]
        MULTI_USER[多用户支持]
        RESOURCE_MGR[资源管理器]
    end
    
    subgraph "用户实例"
        USER1[用户1实例<br/>独立配置]
        USER2[用户2实例<br/>独立配置]
        USER3[用户N实例<br/>独立配置]
    end
    
    subgraph "共享资源"
        API_POOL[API连接池]
        CACHE_LAYER[缓存层]
        LOG_CENTRAL[集中日志]
    end
    
    SHARED_SERVER --> MULTI_USER
    MULTI_USER --> RESOURCE_MGR
    
    RESOURCE_MGR --> USER1
    RESOURCE_MGR --> USER2
    RESOURCE_MGR --> USER3
    
    USER1 --> API_POOL
    USER2 --> API_POOL
    USER3 --> API_POOL
    
    API_POOL --> CACHE_LAYER
    CACHE_LAYER --> LOG_CENTRAL
```

### 云端部署架构
```mermaid
graph TB
    subgraph "云服务提供商"
        CLOUD[AWS/Azure/GCP]
        CONTAINER[容器服务<br/>Docker/Kubernetes]
        LOAD_BALANCER[负载均衡器]
    end
    
    subgraph "应用集群"
        APP1[应用实例1]
        APP2[应用实例2]
        APP3[应用实例N]
    end
    
    subgraph "数据服务"
        CONFIG_DB[配置数据库]
        FILE_STORE[文件存储]
        LOG_SERVICE[日志服务]
    end
    
    CLOUD --> CONTAINER
    CONTAINER --> LOAD_BALANCER
    LOAD_BALANCER --> APP1
    LOAD_BALANCER --> APP2
    LOAD_BALANCER --> APP3
    
    APP1 --> CONFIG_DB
    APP2 --> CONFIG_DB
    APP3 --> CONFIG_DB
    
    APP1 --> FILE_STORE
    APP2 --> FILE_STORE
    APP3 --> FILE_STORE
    
    APP1 --> LOG_SERVICE
    APP2 --> LOG_SERVICE
    APP3 --> LOG_SERVICE
```

这个部署架构图提供了从单机部署到云端扩展的完整部署方案，涵盖了安装、配置、监控和维护的各个方面，为不同规模的使用场景提供了参考。
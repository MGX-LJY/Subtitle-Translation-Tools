# Subtitle Translation Tools - AI驱动的智能字幕翻译应用

## 项目概述

Subtitle Translation Tools 是一个专业的AI驱动字幕翻译应用，专为日语到中文的成人影片字幕翻译而设计。该应用基于现代Python GUI框架PySide6构建，集成OpenAI GPT模型，提供高效、准确的字幕翻译服务。

应用采用8通道并发处理架构，显著提升翻译效率，同时提供专业的字幕润色功能，确保翻译质量。支持完整的SRT字幕格式，配备直观的图形用户界面，为专业字幕翻译工作提供完整的解决方案。

## 核心特性

### 🤖 AI智能翻译
- **OpenAI GPT集成**: 支持gpt-4o-mini、gpt-4o等最新模型
- **专业提示词优化**: 针对成人影片字幕的专门优化提示词
- **智能润色功能**: 翻译后自动润色，提升表达自然度
- **上下文理解**: 基于语义的智能翻译，保持语境连贯

### ⚡ 高性能处理
- **8通道并发**: 8个并发API调用，显著提升处理速度
- **异步处理架构**: 基于asyncio的现代异步编程
- **实时进度反馈**: 翻译过程中的实时进度显示和状态更新
- **智能队列管理**: 自动任务调度和负载均衡

### 🎯 专业功能
- **SRT格式支持**: 完整的SubRip字幕格式解析和生成
- **双模式翻译**: 支持初译和润色两种处理模式
- **历史记录管理**: 操作历史和撤销功能
- **批量处理**: 支持大批量字幕文件的高效处理

### 🛠 用户体验
- **现代GUI界面**: 基于PySide6的现代化桌面应用
- **直观操作流程**: 简单易用的工作流程设计
- **实时编辑**: 表格化字幕编辑和实时预览
- **配置持久化**: 智能配置管理和自动保存

## 快速开始

### 1. 环境要求

**系统要求**:
- **操作系统**: Windows 10+, macOS 10.14+, 或 Ubuntu 18.04+
- **Python版本**: Python 3.8 或更高版本
- **内存**: 最低 4GB RAM (推荐 8GB+)
- **网络**: 稳定的互联网连接 (用于API调用)

**依赖库**:
```bash
PySide6>=6.6.0          # Qt6 GUI框架
openai>=1.0.0           # OpenAI官方SDK
```

### 2. 安装和配置

**步骤1: 安装Python依赖**
```bash
pip install PySide6 openai
```

**步骤2: 下载应用程序**
```bash
# 下载主程序文件
wget https://your-repo.com/main.py
# 或者从GitHub克隆
git clone https://github.com/your-username/subtitle-translation-tools.git
```

**步骤3: 配置API密钥**
1. 运行应用程序: `python main.py`
2. 点击菜单中的"设置"按钮
3. 输入您的OpenAI API密钥和基础URL
4. 选择翻译模型和目标语言
5. 点击"保存"完成配置

### 3. 开始使用

**基本使用流程**:
1. **加载字幕文件**: 点击"打开"按钮选择SRT字幕文件
2. **执行翻译**: 点击"全部翻译"开始AI翻译处理
3. **润色优化**: 点击"全部修复"进行翻译结果润色
4. **保存结果**: 点击"保存"或"导出"保存翻译后的字幕

## 项目状态

**当前版本**: v1.8 (2025-07 持久化配置版)

### 🟢 项目成熟度
- **稳定性**: 生产就绪，经过实际使用验证
- **功能完整性**: 覆盖字幕翻译的完整工作流程
- **性能**: 8倍并发提升，处理效率显著优化
- **用户体验**: 直观的GUI界面，易于上手使用

### ✨ 最新更新
- ✅ **并发优化**: 8通道并发处理，结果按顺序实时刷新
- ✅ **配置持久化**: API密钥等配置信息自动保存
- ✅ **语气词处理**: 针对"晚安"等特殊语气词的专门处理规则
- ✅ **错误处理**: 完善的异常处理和用户友好的错误提示

### 🎯 功能状态
| 功能模块 | 状态 | 说明 |
|---------|------|------|
| SRT文件解析 | ✅ 完成 | 支持标准SRT格式 |
| AI翻译集成 | ✅ 完成 | OpenAI GPT系列模型 |
| 并发处理 | ✅ 完成 | 8通道异步处理 |
| GUI界面 | ✅ 完成 | PySide6现代界面 |
| 配置管理 | ✅ 完成 | JSON持久化配置 |
| 错误处理 | ✅ 完成 | 完善的异常机制 |

## 技术架构

### 🏗 架构概览
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Layer      │    │ Service Layer   │    │   Data Layer    │
│   (PySide6)     │◄──►│ (TranslateWork) │◄──►│ (SubtitleCue)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────▼────────────────────────┘
                          ┌─────────────────┐
                          │ External APIs   │
                          │  (OpenAI)       │
                          └─────────────────┘
```

### 🔧 技术栈
- **前端框架**: PySide6 (Qt6 Python绑定)
- **AI集成**: OpenAI Python SDK
- **异步处理**: Python asyncio
- **数据模型**: Python dataclasses
- **配置管理**: JSON格式持久化
- **日志系统**: Python logging标准库

### 📊 性能特性
- **并发处理**: 8个同时进行的API调用
- **内存优化**: 流式处理大文件，避免内存溢出
- **缓存机制**: 智能缓存减少重复API调用
- **错误恢复**: 自动重试和优雅降级机制

## 使用示例

### 基本翻译流程
```python
# 应用程序会自动处理以下流程:

# 1. 加载SRT文件
subtitles = parse_srt("input.srt")

# 2. 并发翻译处理
async def translate_batch():
    tasks = [translate_subtitle(cue) for cue in subtitles]
    results = await asyncio.gather(*tasks)
    return results

# 3. 保存结果
write_srt("output.srt", translated_subtitles)
```

### 配置示例
```json
{
  "api_key": "sk-xxxxxxxxxxxxxxxx",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "target_lang": "中文"
}
```

### 典型使用场景
1. **专业字幕工作室**: 批量处理影片字幕翻译
2. **个人用户**: 小规模字幕文件的快速翻译
3. **字幕爱好者**: 高质量字幕的制作和分享
4. **内容创作者**: 多语言内容的本地化处理

## 开发路线图

### 🎯 短期计划 (1-3个月)
- [ ] **多格式支持**: 扩展支持VTT、ASS、SSA等字幕格式
- [ ] **多语言翻译**: 支持更多语言对的翻译
- [ ] **翻译质量评估**: 自动翻译质量评分和建议
- [ ] **批量文件处理**: 支持文件夹批量处理功能

### 🚀 中期计划 (3-6个月)
- [ ] **多AI服务商**: 集成Google Translate、Azure Translator等
- [ ] **云端同步**: 配置和翻译历史的云端同步
- [ ] **插件系统**: 可扩展的插件架构
- [ ] **API服务**: 提供REST API接口供第三方集成

### 🌟 长期愿景 (6-12个月)
- [ ] **机器学习优化**: 基于用户反馈的个性化翻译优化
- [ ] **实时翻译**: 支持视频实时字幕翻译
- [ ] **协作功能**: 多用户协作翻译和审校
- [ ] **移动端支持**: iOS/Android移动应用版本

### 🔧 技术改进
- [ ] **模块化重构**: 将单文件架构重构为模块化设计
- [ ] **测试覆盖**: 添加完整的单元测试和集成测试
- [ ] **性能优化**: 进一步优化内存使用和处理速度
- [ ] **国际化**: 支持多语言用户界面

## 贡献指南

### 🤝 如何贡献

我们欢迎社区贡献！以下是参与项目的方式:

**代码贡献**:
1. Fork 项目仓库
2. 创建功能分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -am 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 创建Pull Request

**问题报告**:
- 使用GitHub Issues报告bug
- 提供详细的重现步骤
- 包含系统环境信息
- 附加相关日志文件

**功能建议**:
- 在Issues中提出功能请求
- 描述用例和预期效果
- 参与功能设计讨论

### 🔨 开发环境设置
```bash
# 克隆仓库
git clone https://github.com/your-username/subtitle-translation-tools.git
cd subtitle-translation-tools

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
python -m pytest tests/

# 代码风格检查
flake8 main.py
black main.py
```

### 📝 贡献规范
- 遵循PEP 8代码风格
- 添加适当的类型注解
- 包含必要的文档字符串
- 确保测试通过
- 保持向后兼容性

### 🏆 贡献者
感谢所有为项目做出贡献的开发者！

## 许可证

本项目采用 **MIT许可证** 开源发布。

```
MIT License

Copyright (c) 2025 Subtitle Translation Tools

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 使用条款
- ✅ 商业使用
- ✅ 修改和分发
- ✅ 私人使用
- ✅ 专利使用

### 免责声明
本软件按"原样"提供，不提供任何明示或暗示的保证。作者不对使用本软件造成的任何损害承担责任。

---

## 📞 联系我们

- **项目主页**: https://github.com/your-username/subtitle-translation-tools
- **问题反馈**: https://github.com/your-username/subtitle-translation-tools/issues
- **邮箱**: your-email@example.com
- **讨论社区**: https://github.com/your-username/subtitle-translation-tools/discussions

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**

[🌟 Star this repo](https://github.com/your-username/subtitle-translation-tools) | [🐛 Report Bug](https://github.com/your-username/subtitle-translation-tools/issues) | [💡 Request Feature](https://github.com/your-username/subtitle-translation-tools/issues)

</div>
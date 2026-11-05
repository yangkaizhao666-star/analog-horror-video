# analog-horror-video

屏幕录屏式模拟恐怖（Analog Horror / Found Footage UI）短视频创作 Skill。

不拍真人、不使用传统镜头，而是伪装成“某人真实电脑/手机的屏幕录像”，通过聊天软件、业主群、私聊、浏览器、智能门锁、监控等日常界面叙事，让观众像在偷看一台正在出事的设备。适用于丧尸/感染、入侵、怪谈、规则、AI 失控等题材的系列化短视频。

## 能力

- 8 步完整工作流：世界观 → 信息层级与节拍 → 消息流剧本 → 时间轴 → 画面生成 → 音频设计 → 剪辑 → 发布
- 基于真实拉片与音频分析提炼的风格指南：UI 载体、叙事手法、误判链、节奏节拍表、音量曲线
- 可直接改写的 AI 图片/视频/音频提示词库
- 消息流 JSON 模板 + 时间轴构建脚本（仅依赖标准库）

## 快速开始

1. 阅读 `SKILL.md` 了解完整工作流与交付检查清单。
2. 复制 `assets/message_flow_template.json`，按本集设定填写消息流。
3. 运行脚本生成时间轴、镜头与音效清单：

```bash
python scripts/timeline_builder.py assets/message_flow_template.json
```

4. 从 `references/prompt-library.md` 选用提示词生成画面与音频，按时间轴剪辑。

## 目录结构

```
analog-horror-video/
├── SKILL.md                          # 核心工作流
├── references/
│   ├── style-guide.md                # 视听语言与节奏模型
│   ├── screenplay-template.md        # 剧本与消息流模板
│   └── prompt-library.md             # 图片/视频/音频提示词
├── scripts/
│   └── timeline_builder.py           # 消息流 → 时间轴/镜头/音效
└── assets/
    └── message_flow_template.json    # 消息流脚本模板
```

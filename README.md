# analog-horror-video

屏幕录屏式模拟恐怖（Analog Horror / Found Footage UI）短视频创作 Skill。

不拍真人、不使用传统镜头，而是伪装成"某人真实电脑/手机的屏幕录像"，通过聊天软件、业主群、私聊、浏览器、AI 助手、智能门锁、监控、应急频道等日常界面叙事，让观众像在偷看一台正在出事的设备；高潮段可结合黑暗实景第一人称。适用于丧尸/感染、入侵、怪谈、规则、AI 失控等题材的系列化短视频。

## 能力

- 8 步完整工作流：世界观 → 信息层级与节拍 → 消息流剧本 → 时间轴与乱码 → 画面生成 → 音频设计 → 剪辑 → 发布
- 基于三集拉片与音频分析的风格指南：UI 载体、误判链、乱码异化、认知偏差、节奏节拍、音量曲线、连载数据衰减与避坑
- 手机 UI 动效工程手册 + 沉浸感/生理反馈工程：丝滑过渡、真实打字、通知轰炸、心跳震动、颜色渐变、静音留白
- 可直接改写的 AI 图片/视频/音频提示词库
- 消息流 JSON 模板 + 时间轴构建脚本；乱码生成脚本（编码错位 / 生僻字 / 刷屏）、UI 动效脚本、沉浸感反馈脚本，仅依赖标准库

## 快速开始

1. 阅读 `SKILL.md` 了解完整工作流与交付检查清单。
2. 复制 `assets/message_flow_template.json`，按本集设定填写消息流。
3. 运行脚本生成时间轴、镜头与音效清单：

```bash
python scripts/timeline_builder.py assets/message_flow_template.json
```

4. 用乱码脚本生成异常文本：

```bash
python scripts/garble_text.py garble "阿姨就在你门口"
python scripts/garble_text.py rare --length 20
python scripts/garble_text.py spam "绫夌绡" --repeat 30
```

5. 从 `references/prompt-library.md` 选用提示词生成画面与音频，按时间轴剪辑。

## 目录结构

```
analog-horror-video/
├── SKILL.md                          # 核心工作流
├── agents/doubao.yaml                 # 面板中文显示名
├── references/
│   ├── style-guide.md                # 视听语言、节奏模型与避坑
│   ├── mobile-ui-motion.md           # 手机 UI 动效（丝滑过渡、真实打字）
│   ├── immersion-feedback.md         # 沉浸感/生理反馈（通知轰炸、心跳、调色、静音）
│   ├── loop-horror.md                # 时间循环/死亡轮回规则
│   ├── screenplay-template.md        # 剧本与消息流模板
│   └── prompt-library.md             # 图片/视频/音频提示词
├── scripts/
│   ├── timeline_builder.py           # 消息流 → 时间轴/镜头/音效
│   ├── garble_text.py                # 乱码/生僻字/刷屏生成
│   ├── ui_motion.py                  # 缓动、动效规格、打字节奏
│   └── immersion_fx.py               # 心跳、颜色渐变、轰炸节奏、微震
└── assets/
    └── message_flow_template.json    # 消息流脚本模板
```

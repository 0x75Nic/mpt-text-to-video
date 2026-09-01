# mpt-text-to-video

<div align="center">

[![WorkBuddy](https://img.shields.io/badge/WorkBuddy-Skill-7C3AED.svg)](#)
[![引擎](https://img.shields.io/badge/引擎-MoneyPrinterTurbo-131415.svg?logo=github)](#)
[![免LLM](https://img.shields.io/badge/免LLM-无需Key-2ea44f)](#)
[![配音](https://img.shields.io/badge/配音-Edge%20TTS-2490FF)](#)
[![Stars](https://img.shields.io/github/stars/0x75Nic/mpt-text-to-video?logo=github)](https://github.com/0x75Nic/mpt-text-to-video)
[![Last Commit](https://img.shields.io/github/last-commit/0x75Nic/mpt-text-to-video)](https://github.com/0x75Nic/mpt-text-to-video)

</div>

![示例：由一段主题文案自动生成的横屏 16:9 视频封面](assets/cover.jpg)


把「一段文字描述 → 一条连贯短视频」跑通的 WorkBuddy 技能。底层用 [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) 的 `--video-script` 模式，**免 LLM Key**、免付费配音，只需一个 Pexels API Key。


## 它能做什么


> 输入：「城市美食探店」「品牌产品宣传」这类主题/描述
> 输出：一条带中文配音、Pexels 素材拼接的短视频（`final-1.mp4`），横屏/竖屏可选


自动流水线：`分镜脚本 → 检索词 → Pexels 素材 → Edge TTS 中文配音 → 字幕(可选) → 拼接成片`


![成片示例：多段 Pexels 素材自动拼接](assets/preview_grid.jpg)


整条链路**只需一个 Pexels Key**，不依赖 OpenAI / Gemini / Whisper 等任何付费或重型服务。


## 为什么不需要 LLM


- `--video-script "<脚本>"`：直接喂分镜脚本，跳过 LLM 写脚本。
- `--video-terms "<词>"`：直接喂检索词，跳过 LLM 生成检索词。
- 字幕/配音默认用微软 **Edge TTS**（`zh-CN-XiaoxiaoNeural-Female`），免费、无需 Key。
- 素材源 `video_source="pexels"`，只需一个 Pexels Key。


## 安装到 WorkBuddy


把本仓库放到 WorkBuddy 的技能目录即可被识别（自动触发）：


```bash
# 用户级（跨项目）
cp -r mpt-text-to-video ~/.workbuddy/skills/


# 或项目级
cp -r mpt-text-to-video <你的项目>/.workbuddy/skills/
```


## 兼容性：其他 AI 也能用吗？


- **能自动识别**：实现了 skills 系统的 Agent —— WorkBuddy，以及 Claude Code / Codex 这类读取 `SKILL.md` 的客户端（本仓库的 `name` / `description` frontmatter 与它们兼容）。
- **不能直接自动识别，但照样能用**：ChatGPT 网页版、普通聊天机器人等。它们不会去扫 GitHub 的 `SKILL.md`，但本仓库的 `README.md` + `scripts/bootstrap.py` 是纯 Markdown + 纯 Python，**任何 AI 或人都能读、能跑**。把本仓库链接丢给任意 AI，说「按 README 帮我生成一个 XX 主题视频」即可。
- **跨平台 / 跨环境**：`bootstrap.py` 不依赖 WorkBuddy。在有 managed venv 的机器上复用它；否则自动在 `<repo>/.venv` 建隔离环境。Windows / macOS / Linux 均可用。


## 一键准备环境（可选但推荐）


`scripts/bootstrap.py` 会把「克隆 MoneyPrinterTurbo → 建隔离 venv → 装最小依赖 → 写入 config.toml」封装成一步，幂等可重复跑：


```bash
# WorkBuddy 环境
python scripts/bootstrap.py --repo <任意目录>/MoneyPrinterTurbo --key <你的PEXELS_KEY>


# 任意环境（venv 自动降级到 <repo>/.venv）
python scripts/bootstrap.py --repo ./MoneyPrinterTurbo
python scripts/bootstrap.py --repo ./MoneyPrinterTurbo --venv ./myenv --key <你的PEXELS_KEY>
```


最小依赖（刻意避开 faster-whisper / litellm / streamlit 等重型包）：
`openai edge_tts moviepy toml pydantic`


## 手动跑一条视频


```bash
# 解释器：优先用 bootstrap 建好的 venv

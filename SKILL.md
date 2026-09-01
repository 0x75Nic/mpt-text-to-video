---
name: mpt-text-to-video
description: 用 MoneyPrinterTurbo 的 --video-script 模式（免 LLM Key）把中文分镜脚本 + Pexels 素材自动合成带中文配音和字幕的短视频。支持跨项目复用：自动克隆仓库、建隔离环境、装最小依赖。当用户要「给主题/描述→生成连贯短视频并后期微调」时使用。
agent_created: true
---

# MoneyPrinterTurbo 文字转视频（免 LLM · 跨项目版）

## 何时触发
用户想要「输入一段描述/主题 → 自动生成连贯短视频，后期再微调」，或直接说「做个 XX 主题视频 / 帮我生成一条短视频」。此技能就是为这类请求准备的，无需用户显式说「skill」。

## 核心架构（为什么这样能跑通）
MoneyPrinterTurbo 的流水线：`script → terms → materials(pexels) → voice(edge-tts) → subtitle → video`。
- `--video-script "<脚本>"`：跳过 LLM 脚本生成（不用 LLM Key）。
- `--video-terms "<词>"`：跳过 LLM 检索词生成（不用 LLM Key）。
- 默认字幕用 Edge TTS（`zh-CN-XiaoxiaoNeural-Female`），**完全免费、无需 Key**。
- 素材源 `video_source="pexels"`，只需一个 Pexels Key。

所以整条链路**只需要 Pexels Key 一个凭据**，不用 OpenAI / Gemini / Whisper 等任何付费或重型依赖。

## 跨项目策略（关键）
技能可能被在任何工作区触发，所以**仓库和环境都走「复用优先」**，不要求每个项目重新克隆/装包：
1. 仓库：优先复用 `<workspace>/MoneyPrinterTurbo`；不存在则 `git clone --depth 1`（见 bootstrap）。
2. 环境：使用 managed venv `$HOME/.workbuddy/binaries/python/envs/default`（已含 loguru/requests）。缺失则用 `python -m venv` 自建。
3. 依赖：仅需 `openai edge_tts moviepy toml pydantic`（刻意避开 faster-whisper / litellm / streamlit 等重型包）。
4. Key：`MPT_PEXELS_KEY` 环境变量 > `~/.workbuddy/pexels_config.json` > 询问用户。

## 标准执行流程（agent 照做）
1. **加载技能后立刻调用 `bootstrap.py`**：`python scripts/bootstrap.py --repo <workspace>/MoneyPrinterTurbo --key <PEXELS_KEY>`。它会克隆/复用仓库、确保 venv 与依赖、写入 config.toml。幂等，可重复跑。
2. **写中文分镜脚本**（见下「分镜怎么写」），存为 `script.txt`。
3. **写英文检索词**（对应每镜，Pexels 英文更准），用英文逗号分隔。
4. **生成**：用 managed venv 的 python 跑：
   ```bash
   "$PY" cli.py --video-script "$(cat script.txt)" \
     --video-terms "yining xinjiang,street morning,..." \
     --video-aspect 9:16 --bgm-type none --stop-at video
   ```
5. **交付** `storage/t.asks/<id>/final-1.mp4` 给用户。

> 不想用 bootstrap 时，也可直接命令式执行；bootstrap 只是把「克隆+装包+写配置」封装成一步。

## 分镜脚本怎么写（决定成片质量，最重要）
- **每镜一行**，整篇 4–8 行最稳，每行即一段配音 + 一段素材。
- **画面具体、有动作**：「阳光洒进蓝色小院」优于「这里很美」；给素材检索留画面锚点。
- **节奏均匀**：每行约 3–10 秒，太长会被自动裁、太短会重复素材。
- **不要**写镜头术语（「近景」「转场」），MPT 不解析；只写自然语言旁白。
- 示例（伊宁六星街·天合民宿）：
  ```
  清晨，中国新疆伊宁的六星街刚刚醒来，蓝色的小院门缓缓打开。
  主人煮好一壶手冲咖啡，热气在晨光里轻轻升起。
  院子里种满鲜花，葡萄藤爬满木架，风一吹全是夏天的味道。
  旅客推开房门，远处的雪山在窗外清晰可见。
  这就是天合民宿，一个可以在街角慢下来的地方。
  ```

## 参数速查
| 参数 | 取值 | 说明 |
|---|---|---|
| `--video-aspect` | `9:16` / `16:9` / `1:1` | 竖屏短视频默认 `9:16` |
| `--bgm-type` | `none` / `random` / `<name>` | 没有 BGM 素材时务必 `none` |
| `--video-transition-mode` | `None` / `fade` / `slide` … | 转场，默认即可 |
| `--stop-at` | `script` / `terms` / `materials` / `video` / `everything` | 想先看脚本/素材就提前停 |
| `--voice` | `zh-CN-XiaoxiaoNeural-Female` 等 | 换音色 |
| `--no-subtitle-enabled` | （无值） | 关闭字幕；默认开启，加此参数即禁用 |

## 用户常用风格预设（默认采用）
根据多次迭代，用户偏好以下风格，作为默认值套用（除非用户另行指定）：
- **横屏 16:9**（非竖屏）
- **无字幕**（`--no-subtitle-enabled`）
- **中国面孔 / 中国场景**：检索词全部带 `Chinese / China / Asian` 倾向（Pexels 无种族筛选，靠关键词尽量命中）
- **无 BGM**（`--bgm-type none`）

一键调用（分镜 script.txt 与检索词按当前主题实时拟定，顺序不固定）：
```bash
PY="$HOME/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
SCRIPT=$(cat script.txt)
"$PY" cli.py --video-script "$SCRIPT" \
  --video-terms "Chinese family,Chinese landscape,Chinese worker,Chinese logistics,Chinese warehouse" \
  --video-aspect 16:9 --bgm-type none --no-subtitle-enabled --stop-at video
```

## 踩坑记录（务必遵守）
1. **Python 路径**：用 `$HOME/.workbuddy/binaries/python/envs/default/Scripts/python.exe`（Windows）或 `.../bin/python`（mac/linux），不是版本目录下的裸 python。
2. **必须显式 `--video-terms`**：否则 `generate_terms` 走 LLM，无 Key 报错。
3. **BGM**：默认 `random` 需内置音乐文件，缺则会报缺文件 → 加 `--bgm-type none`。
4. **`open_task_folder_on_completion`**：无头/沙箱环境弹资源管理器会失败 → 设 `false`。
5. **pip 镜像**：清华源部分 wheel 返回 403 → 用 `https://mirrors.aliyun.com/pypi/simple/`。
6. **Pexels UA**：直接 urllib 抓会被 403，必须带浏览器 UA（MPT 已处理，自己写脚本时留意）。
7. **素材下载需联网**：moviepy 首次渲染会下载 ffmpeg 二进制。

## 产物
- `storage/tasks/<task-id>/final-1.mp4`（竖屏 9:16 成片）
- 同目录还有 `combined-1.mp4`、`audio.mp3`、`subtitle.srt`、`script.json`

## 进阶
- 可做**定时自动化**：「每天生成一条六星街日常」，用 automation_update 创建 once/recurring 任务，prompt 写「用 mpt-text-to-video 生成一个关于 XX 的竖屏短视频」。
- **民宿专属模板**：把分镜套路（蓝巷/花架/咖啡/雪山/手风琴）固化进本技能，生成更贴近天合民宿调性。

# Kids Picture Book Video · 儿童英语绘本短视频

A [Claude Code](https://claude.com/claude-code) skill that turns 5 simple English sentences into a ~25-second picture-book video for kids aged 3–6, with crayon-style pictures, camera animation, a child voice, subtitles and original background music.

一个 Claude Code skill：把 5 句简单英文做成约 25 秒的儿童英语绘本短视频，适合 3–6 岁孩子磨耳朵。主角是小女孩 **Lily**（频道 *Lily Story Time*）。

## 能做什么

| 步骤 | 脚本 | 输出 |
|---|---|---|
| 主题和文案 | Claude 对话 | 5 句英文 |
| 出图 | `scripts/generate.py` | 蜡笔风绘本图，横版 16:9 + 竖版 3:4 |
| 动画 | `scripts/animate.py` | 每张 5 秒：镜头推拉摇移 + 角色小动作 |
| 配音 | `scripts/voiceover.py` | 英文童声（edge-tts） |
| 成品 | `scripts/finalize.py` | 字幕 + 原创背景音乐 + 响度标准化 |
| 发布 | `references/publishing.md` | YouTube / 抖音 / 小红书标题和说明 |

图片由 DeepSeek（`deepseek-flash`）写 SVG 矢量图，再加蜡笔滤镜、用 Chrome 导出，所以不需要专门的生图模型。

## 安装

1. 把本仓库克隆到 Claude Code 的个人 skills 目录：
   ```bash
   git clone https://github.com/konsang121/kids-picture-book-video ~/.claude/skills/kids-picture-book-video
   ```
2. 安装依赖（Python 3.10+，并且需要装好 Google Chrome）：
   ```bash
   python -m pip install playwright imageio-ffmpeg
   python -m pip install edge-tts --only-binary :all:
   ```
3. 配置 DeepSeek API Key（任选一种）：
   - 设置环境变量 `DEEPSEEK_API_KEY`
   - 或者设置环境变量 `DEEPSEEK_KEY_FILE`，指向保存 key 的文本文件
   - 或者在 skill 根目录建一个 `.deepseek_key_file`，里面写 key 文件的路径（已被 `.gitignore` 忽略）

> Windows 上脚本默认使用 `C:\Program Files\Google\Chrome\Application\chrome.exe`。路径不同的话，修改 `scripts/common.py` 里的 `BROWSER`。

## 使用

在 Claude Code 里直接说，例如：

> 用 Lily 做一期下雨天的英语绘本短视频

Claude 会和你确认文案，在项目文件夹里写好 `story.py`（模板见 `assets/story_template.py`），然后逐步运行脚本，并检查每一步的结果。

也可以手动运行，每个脚本都用 `--project <项目文件夹>` 指定项目，竖版加 `--3x4`：

```bash
python scripts/generate.py --project D:/绘本/下雨天
python scripts/generate.py --project D:/绘本/下雨天 --3x4
python scripts/animate.py  --project D:/绘本/下雨天
python scripts/animate.py  --project D:/绘本/下雨天 --3x4
python scripts/voiceover.py --project D:/绘本/下雨天
python scripts/finalize.py  --project D:/绘本/下雨天
```

## 版权说明

- 背景音乐由 `finalize.py` 现场合成，是原创旋律，没有使用任何采样。
- 字幕字体 [Fredoka](https://fonts.google.com/specimen/Fredoka)，SIL Open Font License。
- 配音使用微软 Edge 在线语音（edge-tts），商用前请自行确认微软的使用条款。
- Lily 的角色形象（`assets/lily.svg`）属于 *Lily Story Time* 频道。

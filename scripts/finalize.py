"""第 5 步 成品：配音版完整视频 + 开头钩子大字 + 字幕 + 原创背景音乐和音效 + 提亮 + 响度标准化。

用法：
    python finalize.py --project ...                 # 16:9 + 9:16（有哪个做哪个）
    python finalize.py --project ... --music 0.15    # 调背景音乐音量（默认 0.22）
    python finalize.py --project ... --remusic       # 重新合成背景音乐和音效（改了 CLIP/TEASER/MUSIC 后要加）

背景音乐和音效都由本脚本用正弦波现场合成（原创旋律、无采样），不存在版权问题；
story.py 里 MUSIC = "playful"（默认，轻快，适合信息流）或 "lullaby"（睡前主题用）。
字幕字体 Fredoka 是 SIL Open Font License 开源字体，可商用。
输出：成品/<TITLE>_16x9.mp4、_9x16.mp4（由 3:4 竖版工作画面扩展；3:4 本身不再输出成品）、配音/bgm.wav、配音/sfx.wav
"""
import array
import math
import random
import re
import subprocess
import sys
import wave

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

import common as c

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
OUT = c.ROOT / "成品"
BGM = c.ROOT / "配音" / "bgm.wav"
SFX = c.ROOT / "配音" / "sfx.wav"
MUSIC_VOL = float(c.arg_value("--music", 0.22))
MUSIC = getattr(c.STORY, "MUSIC", "playful")
SR = 44100
HIGHLIGHT = c.STORY.HIGHLIGHT
HOOK_END = c.TEASER_SECONDS + 1.2      # 开头大字显示到第一句说出来之后


# ---------------- 原创音乐 ----------------
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}
CHORD_TONES = {"C": ["C3", "E3", "G3", "C4"], "Am": ["A2", "E3", "A3", "C4"],
               "F": ["F2", "C3", "F3", "A3"], "G": ["G2", "D3", "G3", "B3"]}

LULLABY = {  # 音乐盒摇篮曲，96 BPM
    "bpm": 96,
    "chords": ["C", "Am", "F", "G", "C", "Am", "F", "G"],
    "melody": [[("E5", 1), ("G5", 1), ("C6", 2)], [("B5", 1), ("A5", 1), ("E5", 2)],
               [("F5", 1), ("A5", 1), ("C6", 1), ("A5", 1)], [("G5", 3), ("D5", 1)],
               [("E5", 1), ("G5", 1), ("D6", 2)], [("C6", 1), ("B5", 1), ("A5", 2)],
               [("A5", 1), ("G5", 1), ("F5", 1), ("A5", 1)], [("G5", 2), ("B5", 1), ("D6", 1)]],
    "ending": ("C", [("C6", 2), ("C5", 2)]),
}
PLAYFUL = {  # 轻快的木琴小调，120 BPM，弹跳的八分音符
    "bpm": 120,
    "chords": ["C", "G", "Am", "F", "C", "G", "F", "G"],
    "melody": [[("C5", .5), ("E5", .5), ("G5", .5), ("E5", .5), ("C6", 1), ("G5", 1)],
               [("B4", .5), ("D5", .5), ("G5", .5), ("D5", .5), ("B5", 1), ("G5", 1)],
               [("A4", .5), ("C5", .5), ("E5", .5), ("C5", .5), ("A5", 1), ("E5", 1)],
               [("F5", .5), ("G5", .5), ("A5", .5), ("G5", .5), ("F5", 1), ("C5", 1)],
               [("E5", .5), ("E5", .5), ("G5", 1), ("E5", .5), ("D5", .5), ("C5", 1)],
               [("D5", .5), ("D5", .5), ("G5", 1), ("B4", .5), ("C5", .5), ("D5", 1)],
               [("A5", .5), ("G5", .5), ("F5", .5), ("E5", .5), ("D5", 1), ("G5", 1)],
               [("G5", .5), ("A5", .5), ("B5", .5), ("D6", .5), ("G5", 2)]],
    "ending": ("C", [("C6", 1), ("G5", .5), ("E5", .5), ("C5", 2)]),
}


def freq(name):
    return 440 * 2 ** ((NOTE[name[:-1]] + 12 * (int(name[-1]) + 1) - 69) / 12)


class Track:
    def __init__(self, seconds):
        self.n = int(seconds * SR)
        self.buf = [0.0] * self.n

    def add(self, f, start, length, amp, kind):
        s0 = int(start * SR)
        for i in range(int(length * SR)):
            if s0 + i >= self.n:
                break
            t = i / SR
            if kind == "box":      # 音乐盒：快起音、慢衰减
                env = min(t / 0.005, 1) * math.exp(-2.2 * t)
                v = math.sin(2 * math.pi * f * t) + 0.25 * math.sin(4 * math.pi * f * t) + 0.08 * math.sin(6 * math.pi * f * t)
            elif kind == "mallet":  # 木琴：更短、更脆
                env = min(t / 0.003, 1) * math.exp(-7 * t)
                v = math.sin(2 * math.pi * f * t) + 0.35 * math.sin(2 * math.pi * 4 * f * t) * math.exp(-25 * t)
            elif kind == "pluck":   # 短促的和弦拨奏
                env = min(t / 0.003, 1) * math.exp(-14 * t)
                v = math.sin(2 * math.pi * f * t)
            else:                   # 柔和铺底
                env = min(t / 0.8, 1) * min((length - t) / 0.8, 1)
                v = math.sin(2 * math.pi * f * t + 0.003 * math.sin(2 * math.pi * 5 * t) * f)
            self.buf[s0 + i] += amp * env * v

    def noise(self, start, length, amp, decay):
        s0, rnd = int(start * SR), random.Random(int(start * 1000))
        prev = 0.0
        for i in range(int(length * SR)):
            if s0 + i >= self.n:
                break
            x = rnd.uniform(-1, 1)
            hp, prev = x - prev, x      # 粗略的高通，听起来像沙锤
            self.buf[s0 + i] += amp * hp * math.exp(-decay * i / SR)

    def reverb(self, taps):
        out = self.buf[:]
        for delay, gain in taps:
            d = int(delay * SR)
            for i in range(d, self.n):
                out[i] += gain * self.buf[i - d]
        self.buf = out

    def save(self, path, fade_in, fade_out, total):
        for i in range(self.n):
            t = i / SR
            self.buf[i] *= (min(t / fade_in, 1) if fade_in else 1) * min((total - t) / fade_out, 1)
        peak = max(abs(x) for x in self.buf) or 1
        pcm = array.array("h", (int(x / peak * 0.85 * 32767) for x in self.buf))
        path.parent.mkdir(exist_ok=True)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())
        print("已生成", path)


def make_music():
    song = LULLABY if MUSIC == "lullaby" else PLAYFUL
    beat = 60 / song["bpm"]
    bar = 4 * beat
    bars = math.ceil(c.TOTAL / bar)
    tr = Track(c.TOTAL)
    plan = [(song["chords"][b % 8], song["melody"][b % 8]) for b in range(bars - 1)] + [song["ending"]]
    for b, (chord, melody) in enumerate(plan):
        t0 = b * bar
        tones = CHORD_TONES[chord]
        if MUSIC == "lullaby":
            for tone in tones:
                tr.add(freq(tone), t0, bar + 0.3, 0.05, "pad")
            tr.add(freq(tones[0]), t0, 2.0, 0.12, "box")
            for k in (1, 3):
                tr.add(freq(tones[2]) * 2, t0 + k * beat + beat / 2, 1.0, 0.06, "box")
        else:
            for k in (0, 2):                                   # 低音在 1、3 拍
                tr.add(freq(tones[0]), t0 + k * beat, 0.45, 0.20, "pluck")
            for k in (1, 3):                                   # 和弦在 2、4 拍
                for tone in tones[1:]:
                    tr.add(freq(tone) * 2, t0 + k * beat, 0.25, 0.05, "pluck")
            for k in range(8):                                 # 八分音符的沙锤
                tr.noise(t0 + k * beat / 2, 0.06, 0.05 if k % 2 else 0.03, 60)
        t = t0
        for name, beats in melody:
            if MUSIC == "lullaby":
                tr.add(freq(name), t, min(beats * beat + 1.2, 3.5), 0.22, "box")
            else:
                tr.add(freq(name), t, min(beats * beat + 0.4, 1.2), 0.24, "mallet")
            t += beats * beat
    tr.reverb(((0.113, 0.28), (0.171, 0.22), (0.257, 0.16), (0.389, 0.1)) if MUSIC == "lullaby"
              else ((0.09, 0.15), (0.17, 0.08)))
    # 开头不淡入：第 1 帧就要有音乐
    tr.save(BGM, 0 if MUSIC != "lullaby" else 0.3, 1.5, c.TOTAL)


def make_sfx():
    """开头一串上行的“闪亮”音 + 每一句开始时一声轻快的“啵”。"""
    tr = Track(c.TOTAL)
    for k, name in enumerate(["C6", "E6", "G6", "C7"]):
        tr.add(freq(name), 0.0 + k * 0.06, 0.6, 0.30, "mallet")
    for i in range(len(c.SCENES)):
        s0 = int(c.scene_start(i) * SR)
        for j in range(int(0.09 * SR)):
            if s0 + j >= tr.n:
                break
            t = j / SR
            f = 420 + 5000 * t                                   # 快速上扬的“啵”
            tr.buf[s0 + j] += 0.5 * math.sin(2 * math.pi * f * t) * math.exp(-35 * t)
    tr.save(SFX, 0, 0.3, c.TOTAL)


# ---------------- 字幕和开头大字：透明 PNG，和画面同尺寸 ----------------
FONT = '<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@600;700&display=block" rel="stylesheet">'
TEXT = ("font-family: 'Fredoka', 'Segoe UI Emoji', 'Comic Sans MS', sans-serif; color: #FFFFFF; "
        "-webkit-text-stroke: {stroke}px #4A3B33; paint-order: stroke fill; text-shadow: 0 5px 0 rgba(74,59,51,.35);")


# 各画幅的字幕和开头大字位置。9:16 由 3:4 上下各补 267px 得到，字幕和大字都放进 Reels / Shorts 的安全区
# （顶部约 220px、底部约 330px 会被平台的按钮和文案挡住）
PAD916 = 267
LOOK = {"16x9": {"size": 60, "bottom": 46, "hook_size": 72, "hook_top": 28},
        "3x4": {"size": 66, "bottom": 70, "hook_size": 104, "hook_top": 170},
        "9x16": {"size": 70, "bottom": 360, "hook_size": 104, "hook_top": 300}}


def subtitle_html(line, w, h, fmt):
    portrait = fmt != "16x9"
    for word in HIGHLIGHT:
        line = line.replace(word, f"<b>{word}</b>")
    if portrait:  # 竖版画面窄，按句子换行，避免单个词掉到第二行
        line = re.sub(r"([.!?]</b>|[.!?]) ", r"\1<br>", line)
    size, bottom = LOOK[fmt]["size"], LOOK[fmt]["bottom"]
    return f"""<html><head>{FONT}<style>
  html, body {{ margin: 0; width: {w}px; height: {h}px; background: transparent; }}
  .sub {{ position: absolute; left: 5%; right: 5%; bottom: {bottom}px; text-align: center; font-weight: 600;
         font-size: {size}px; line-height: 1.25; letter-spacing: 1px; {TEXT.format(stroke=12)} }}
  b {{ color: #FF9F1C; font-weight: 600; }}
</style></head><body><div class="sub">{line}</div></body></html>"""


def hook_html(text, w, h, fmt):
    """开头 3 秒的大字悬念，放在画面上方（竖版避开平台顶部的按钮区）。"""
    size, top = LOOK[fmt]["hook_size"], LOOK[fmt]["hook_top"]
    return f"""<html><head>{FONT}<style>
  html, body {{ margin: 0; width: {w}px; height: {h}px; background: transparent; }}
  .hook {{ position: absolute; left: 4%; right: 4%; top: {top}px; text-align: center; }}
  span {{ display: inline-block; padding: 14px 44px 22px; border-radius: 80px; background: #FFE27A; border: 8px solid #4A3B33;
          box-shadow: 0 10px 0 rgba(74,59,51,.3); font-weight: 700; font-size: {size}px; line-height: 1.15;
          {TEXT.format(stroke=16)} }}
</style></head><body><div class="hook"><span>{text}</span></div></body></html>"""


def snap(page, html, path):
    page.set_content(html)
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(200)
    page.screenshot(path=str(path), omit_background=True)
    return path


def make_overlays(page, folder, w, h, fmt):
    """返回 [(png, 开始, 结束)]。"""
    page.set_viewport_size({"width": w, "height": h})
    tag = fmt
    items = []
    if c.TEASER and c.TEASER.get("hook"):
        items.append((snap(page, hook_html(c.TEASER["hook"], w, h, fmt), folder / f"_hook_{tag}.png"), 0.0, HOOK_END))
    for i, sc in enumerate(c.SCENES):
        png = snap(page, subtitle_html(sc["line"], w, h, fmt), folder / f"_sub_{tag}_{sc['name']}.png")
        items.append((png, c.scene_start(i), c.scene_start(i) + c.clip_len(sc)))
    return items


# ---------------- 合成 ----------------
def finalize(video, overlays, out, fmt):
    cmd = [FFMPEG, "-y", "-loglevel", "error", "-i", str(video)]
    for png, st, end in overlays:
        cmd += ["-loop", "1", "-t", f"{end - st:.3f}", "-i", str(png)]
    cmd += ["-i", str(BGM), "-i", str(SFX)]
    # 轻微提亮、提高饱和度：在手机信息流里更抢眼
    src = "[0:v]"
    f = []
    if fmt == "9x16":
        # 3:4 → 9:16：同一画面放大铺满并大幅模糊、稍微提亮作底，原画面居中放在上面
        # （直接延伸/镜像边缘会在镜头推近时拉出谷仓、鞋子之类的条纹）
        h = 1600 + 2 * PAD916
        f += ["[0:v]split[m][b0]",
              f"[b0]scale=-2:{h},crop=1200:{h},boxblur=40:3,eq=brightness=0.06:saturation=0.9[blur]",
              f"[blur][m]overlay=0:{PAD916}[tall]"]
        src = "[tall]"
    f.append(f"{src}eq=saturation=1.15:contrast=1.04:brightness=0.015[base]")
    last = "base"
    for i, (_, st, end) in enumerate(overlays):
        fade_in = "" if st == 0 else "fade=t=in:st=0.15:d=0.2:alpha=1,"   # 开头大字第 1 帧就要完整出现
        f.append(f"[{i + 1}:v]format=rgba,{fade_in}"
                 f"fade=t=out:st={end - st - 0.2:.3f}:d=0.2:alpha=1,setpts=PTS+{st}/TB[o{i}]")
        f.append(f"[{last}][o{i}]overlay=0:0:eof_action=pass[v{i}]")
        last = f"v{i}"
    m = len(overlays) + 1
    # 人声说话时自动压低音乐（sidechain），让孩子听清英文；音效不压
    f.append("[0:a]aresample=44100,asplit[voice][key]")
    f.append(f"[{m}:a]volume={MUSIC_VOL}[bgm]")
    f.append("[bgm][key]sidechaincompress=threshold=0.02:ratio=3:attack=30:release=500[duck]")
    f.append(f"[{m + 1}:a]volume=0.35[sfx]")
    f.append("[voice][duck][sfx]amix=inputs=3:duration=first:normalize=0[mix]")
    f.append("[mix]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[a]")  # 短视频平台常用响度
    cmd += ["-filter_complex", ";".join(f), "-map", f"[{last}]", "-map", "[a]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21", "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    for png, _, _ in overlays:
        png.unlink()
    print("已生成", out)


if __name__ == "__main__":
    c.require_cast(sorted({n for sc in c.SCENES for n in sc.get("cast", [])}), "输出成品")
    if not BGM.exists() or "--remusic" in sys.argv:
        make_music()
    if not SFX.exists() or "--remusic" in sys.argv:
        make_sfx()
    OUT.mkdir(exist_ok=True)
    tall = c.ROOT / "3x4" / "动画" / "配音版" / "完整版.mp4"
    jobs = [(c.ROOT / "动画" / "配音版" / "完整版.mp4", 1600, 900, "16x9"),
            (tall, 1200, 1600 + 2 * PAD916, "9x16")]     # 抖音 / 视频号 / 小红书 / Reels / Shorts，由 3:4 扩展
    jobs = [j for j in jobs if j[0].exists()]
    if not jobs:
        raise SystemExit("没找到 动画/配音版/完整版.mp4，先运行 voiceover.py")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page()
        overlays = [make_overlays(page, OUT, w, h, fmt) for _, w, h, fmt in jobs]
        browser.close()
    for (video, _, _, fmt), ov in zip(jobs, overlays):
        finalize(video, ov, OUT / f"{c.STORY.TITLE}_{fmt}.mp4", fmt)

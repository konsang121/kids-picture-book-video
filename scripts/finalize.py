"""第 5 步 成品：配音版完整视频 + 字幕 + 原创背景音乐 + 响度标准化。

用法：
    python finalize.py --project ...                 # 横版 + 竖版（有哪个做哪个）
    python finalize.py --project ... --music 0.15    # 调背景音乐音量（默认 0.22）
    python finalize.py --project ... --remusic       # 重新合成背景音乐

背景音乐由本脚本用正弦波现场合成（原创旋律、无采样），不存在版权问题；
字幕字体 Fredoka 是 SIL Open Font License 开源字体，可商用。
输出：成品/<TITLE>_16x9.mp4、成品/<TITLE>_3x4.mp4、配音/bgm.wav（TITLE 在 story.py 里）
"""
import array
import math
import re
import random
import subprocess
import sys
import wave

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

import common as c

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
OUT = c.ROOT / "成品"
BGM = c.ROOT / "配音" / "bgm.wav"
MUSIC_VOL = float(c.arg_value("--music", 0.22))
CLIP, TOTAL, SR = 5.0, 25.0, 44100

# 每句里要高亮成橙色的词
HIGHLIGHT = c.STORY.HIGHLIGHT

# ---------------- 原创音乐盒摇篮曲：96 BPM，4/4，每小节 2.5 秒，10 小节 = 25 秒 ----------------
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}
CHORDS = ["C", "Am", "F", "G", "C", "Am", "F", "G", "F", "C"]
MELODY = [  # (音, 拍数)，每小节 4 拍
    [("E5", 1), ("G5", 1), ("C6", 2)],
    [("B5", 1), ("A5", 1), ("E5", 2)],
    [("F5", 1), ("A5", 1), ("C6", 1), ("A5", 1)],
    [("G5", 3), ("D5", 1)],
    [("E5", 1), ("G5", 1), ("D6", 2)],
    [("C6", 1), ("B5", 1), ("A5", 2)],
    [("A5", 1), ("G5", 1), ("F5", 1), ("A5", 1)],
    [("G5", 2), ("B5", 1), ("D6", 1)],
    [("C6", 2), ("A5", 2)],
    [("C6", 4)],
]
CHORD_TONES = {"C": ["C3", "E3", "G3", "C4"], "Am": ["A2", "E3", "A3", "C4"],
               "F": ["F2", "C3", "F3", "A3"], "G": ["G2", "D3", "G3", "B3"]}


def freq(name):
    return 440 * 2 ** ((NOTE[name[:-1]] + 12 * (int(name[-1]) + 1) - 69) / 12)


def make_music():
    beat = 60 / 96
    n = int(TOTAL * SR)
    buf = [0.0] * n

    def add(f, start, length, amp, kind):
        s0 = int(start * SR)
        for i in range(int(length * SR)):
            if s0 + i >= n:
                break
            t = i / SR
            if kind == "box":    # 音乐盒：快起音、慢衰减，带一点泛音
                env = min(t / 0.005, 1) * math.exp(-2.2 * t)
                v = math.sin(2 * math.pi * f * t) + 0.25 * math.sin(4 * math.pi * f * t) + 0.08 * math.sin(6 * math.pi * f * t)
            else:                # 柔和铺底：慢起慢落
                env = min(t / 0.8, 1) * min((length - t) / 0.8, 1)
                v = math.sin(2 * math.pi * f * t + 0.003 * math.sin(2 * math.pi * 5 * t) * f)
            buf[s0 + i] += amp * env * v

    bar = 4 * beat
    for b, chord in enumerate(CHORDS):
        for tone in CHORD_TONES[chord]:
            add(freq(tone), b * bar, bar + 0.3, 0.05, "pad")
        add(freq(CHORD_TONES[chord][0]), b * bar, 2.0, 0.12, "box")   # 低音
        t = b * bar
        for name, beats in MELODY[b]:
            add(freq(name), t, min(beats * beat + 1.2, 3.5), 0.22, "box")
            t += beats * beat
        for k in (1, 3):  # 弱拍上轻轻的和弦分解音，像八音盒的伴奏
            add(freq(CHORD_TONES[chord][2]) * 2, b * bar + k * beat + beat / 2, 1.0, 0.06, "box")

    # 简单混响：几路衰减的回声
    out = buf[:]
    for delay, gain in ((0.113, 0.28), (0.171, 0.22), (0.257, 0.16), (0.389, 0.1)):
        d = int(delay * SR)
        for i in range(d, n):
            out[i] += gain * buf[i - d]
    # 结尾 2.5 秒淡出、开头 0.5 秒淡入，归一化
    for i in range(n):
        t = i / SR
        out[i] *= min(t / 0.5, 1) * min((TOTAL - t) / 2.5, 1)
    peak = max(abs(x) for x in out)
    pcm = array.array("h", (int(x / peak * 0.85 * 32767) for x in out))
    BGM.parent.mkdir(exist_ok=True)
    with wave.open(str(BGM), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("已生成", BGM)


# ---------------- 字幕：透明 PNG，和画面同尺寸 ----------------
def subtitle_html(line, w, h, portrait):
    for word in HIGHLIGHT:
        line = line.replace(word, f"<b>{word}</b>")
    if portrait:  # 竖版画面窄，按句子换行，避免单个词掉到第二行
        line = re.sub(r"([.!?]</b>|[.!?]) ", r"\1<br>", line)
    size, bottom = (66, 70) if portrait else (60, 46)
    return f"""<html><head>
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@600&display=block" rel="stylesheet">
<style>
  html, body {{ margin: 0; width: {w}px; height: {h}px; background: transparent; }}
  .sub {{ position: absolute; left: 5%; right: 5%; bottom: {bottom}px; text-align: center;
         font-family: 'Fredoka', 'Comic Sans MS', sans-serif; font-weight: 600; font-size: {size}px; line-height: 1.25;
         color: #FFFFFF; -webkit-text-stroke: 12px #4A3B33; paint-order: stroke fill;
         text-shadow: 0 5px 0 rgba(74,59,51,.35); letter-spacing: 1px; }}
  b {{ color: #FF9F1C; font-weight: 600; }}
</style></head><body><div class="sub">{line}</div></body></html>"""


def make_subtitles(page, folder, w, h, portrait):
    page.set_viewport_size({"width": w, "height": h})
    pngs = []
    for sc in c.SCENES:
        name, line = sc["name"], sc["line"]
        page.set_content(subtitle_html(line, w, h, portrait))
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(200)
        png = folder / f"_sub_{'3x4' if portrait else '16x9'}_{name}.png"
        page.screenshot(path=str(png), omit_background=True)
        pngs.append(png)
    return pngs


# ---------------- 合成 ----------------
def finalize(video, pngs, out):
    cmd = [FFMPEG, "-y", "-loglevel", "error", "-i", str(video)]
    for p in pngs:
        cmd += ["-loop", "1", "-t", str(CLIP), "-i", str(p)]
    cmd += ["-i", str(BGM)]
    f, last = [], "0:v"
    for i in range(len(pngs)):
        st = i * CLIP
        f.append(f"[{i + 1}:v]format=rgba,fade=t=in:st=0.25:d=0.35:alpha=1,setpts=PTS+{st}/TB[s{i}]")
        f.append(f"[{last}][s{i}]overlay=0:0:eof_action=pass[v{i}]")
        last = f"v{i}"
    m = len(pngs) + 1
    # 人声说话时自动压低音乐（sidechain），让孩子听清英文
    f.append("[0:a]aresample=44100,asplit[voice][key]")
    f.append(f"[{m}:a]volume={MUSIC_VOL}[bgm]")
    f.append("[bgm][key]sidechaincompress=threshold=0.02:ratio=3:attack=30:release=500[duck]")
    f.append("[voice][duck]amix=inputs=2:duration=first:normalize=0[mix]")
    f.append("[mix]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[a]")  # 短视频平台常用响度
    cmd += ["-filter_complex", ";".join(f), "-map", f"[{last}]", "-map", "[a]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21", "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    for p in pngs:
        p.unlink()
    print("已生成", out)


if __name__ == "__main__":
    if not BGM.exists() or "--remusic" in sys.argv:
        make_music()
    OUT.mkdir(exist_ok=True)
    jobs = [(c.ROOT / "动画" / "配音版" / "完整版.mp4", 1600, 900, False, f"{c.STORY.TITLE}_16x9.mp4"),
            (c.ROOT / "3x4" / "动画" / "配音版" / "完整版.mp4", 1200, 1600, True, f"{c.STORY.TITLE}_3x4.mp4")]
    jobs = [j for j in jobs if j[0].exists()]
    if not jobs:
        raise SystemExit("没找到 动画/配音版/完整版.mp4，先运行 voiceover.py")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page()
        subs = [make_subtitles(page, OUT, w, h, portrait) for _, w, h, portrait, _ in jobs]
        browser.close()
    for (video, _, _, _, name), pngs in zip(jobs, subs):
        finalize(video, pngs, OUT / name)

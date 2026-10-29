"""第 4 步 配音：edge-tts 英文童声，合进每段动画，并拼成完整版（预告 + 5 段）。

用法：
    python voiceover.py --project ...                                  # 默认童声 en-US-AnaNeural，语速 -5%
    python voiceover.py --project ... --voice en-US-JennyNeural --rate -10%

开口时间：预告和第一句从第 0 秒立刻开口（观众 1~2 秒内决定去留），其余每段 0.15 秒后开口。
输出：配音/*.mp3，动画/配音版/*.mp4 + 完整版.mp4（横版、竖版有哪个做哪个）
"""
import asyncio
import re
import subprocess

import edge_tts
import imageio_ffmpeg

import common as c

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VOICE_DIR = c.ROOT / "配音"
VOICE = c.arg_value("--voice", "en-US-AnaNeural")
RATE = c.arg_value("--rate", "-5%")
TRIM = "silenceremove=start_periods=1:start_threshold=-45dB"   # 去掉 edge-tts 开头自带的约 0.2 秒静音


def segments():
    """(名字, 句子, 时长, 开口时间)，按播放顺序。"""
    out = [("00_teaser", c.TEASER["line"], c.TEASER_SECONDS, 0.0)] if c.TEASER else []
    for i, s in enumerate(c.SCENES):
        out.append((s["name"], s["line"], c.clip_len(s), 0.0 if i == 0 else 0.15))
    return out


def duration(path):
    out = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True, errors="ignore").stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def speech_length(path):
    """去掉开头静音后，说话持续多久（edge-tts 的音频末尾还带约 1 秒静音）。"""
    out = subprocess.run([FFMPEG, "-i", str(path), "-af", f"{TRIM},silencedetect=noise=-40dB:d=0.15", "-f", "null", "-"],
                         capture_output=True, text=True, errors="ignore").stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    return starts[-1] if starts and starts[-1] > 0 else duration(path)


async def speak_all():
    VOICE_DIR.mkdir(exist_ok=True)
    ok = True
    for name, line, length, start in segments():
        mp3 = VOICE_DIR / f"{name}.mp3"
        await edge_tts.Communicate(line, VOICE, rate=RATE).save(str(mp3))
        d = speech_length(mp3)
        print(f"{name}: 说话 {d:.2f}s / 画面 {length:.1f}s  {line}")
        if start + d > length - 0.15:
            ok = False
            print(f"  ⚠ 这句太长，{length:.0f} 秒内放不下：缩短句子，或用 --rate +0% 加快语速")
    return ok


def dub(folder):
    out = folder / "配音版"
    out.mkdir(exist_ok=True)
    clips = []
    for name, _, length, start in segments():
        mp4 = out / f"{name}.mp4"
        delay = f"adelay={int(start * 1000)}:all=1," if start else ""
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(folder / f"{name}.mp4"), "-i", str(VOICE_DIR / f"{name}.mp3"),
                        "-filter_complex", f"[1:a]{TRIM},{delay}apad,atrim=0:{length}[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                        "-t", str(length), str(mp4)], check=True)
        clips.append(mp4)
    lst = out / "_list.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in clips), encoding="utf-8")
    full = out / "完整版.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                    "-movflags", "+faststart", str(full)], check=True)
    lst.unlink()
    print("已生成", out, f"（完整版 {duration(full):.1f}s）")


if __name__ == "__main__":
    asyncio.run(speak_all())
    for folder in (c.ROOT / "动画", c.ROOT / "3x4" / "动画"):
        if all((folder / f"{name}.mp4").exists() for name, *_ in segments()):
            dub(folder)
        elif folder.exists():
            print(f"跳过 {folder}：动画不全（先运行 animate.py）")

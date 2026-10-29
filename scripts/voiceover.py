"""第 4 步 配音：edge-tts 英文童声，合进每段动画，并拼成完整版。

用法：
    python voiceover.py --project ...                                  # 默认童声 en-US-AnaNeural，语速 -10%
    python voiceover.py --project ... --voice en-US-JennyNeural --rate -15%

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
START = 0.2      # 音频前面自带约 0.2s 静音，所以实际约 0.4s 开口
CLIP = 5.0       # 每段动画长度
VOICE = c.arg_value("--voice", "en-US-AnaNeural")
RATE = c.arg_value("--rate", "-10%")


def duration(path):
    out = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True, errors="ignore").stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def speech_end(path):
    """说话结束的时间（edge-tts 的音频末尾带约 1 秒静音）。"""
    out = subprocess.run([FFMPEG, "-i", str(path), "-af", "silencedetect=noise=-40dB:d=0.15", "-f", "null", "-"],
                         capture_output=True, text=True, errors="ignore").stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    return starts[-1] if starts and starts[-1] > 0 else duration(path)


async def speak_all():
    VOICE_DIR.mkdir(exist_ok=True)
    for s in c.SCENES:
        mp3 = VOICE_DIR / f"{s['name']}.mp3"
        await edge_tts.Communicate(s["line"], VOICE, rate=RATE).save(str(mp3))
        d = speech_end(mp3)
        print(f"{s['name']}: 说话 {d:.2f}s  {s['line']}")
        if START + d > CLIP - 0.2:
            print("  ⚠ 这句太长，5 秒内放不下：缩短句子，或用 --rate -0% 加快语速")


def dub(folder):
    out = folder / "配音版"
    out.mkdir(exist_ok=True)
    clips = []
    for s in c.SCENES:
        mp4 = out / f"{s['name']}.mp4"
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(folder / f"{s['name']}.mp4"),
                        "-i", str(VOICE_DIR / f"{s['name']}.mp3"),
                        "-filter_complex", f"[1:a]adelay={int(START * 1000)}:all=1,apad,atrim=0:{CLIP}[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(CLIP), str(mp4)],
                       check=True)
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
        if all((folder / f"{s['name']}.mp4").exists() for s in c.SCENES):
            dub(folder)

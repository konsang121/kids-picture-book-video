"""GPT 生图引擎（story.py 里写 ENGINE = "gpt" 时使用）。

和 DeepSeek 引擎的区别：
- 背景、配角设定图、每个场景里配角的姿势都由 GPT 直接画成图片（蜡笔风格，配角是透明底）
- 场景里的配角用定稿设定图做参考图（images/edits），保证每个镜头里长得一样
- 配角图片由脚本按 story.py 的坐标摆放；小特效（拟声线、星星）仍由 DeepSeek 画成 SVG
- 动画：配角整张图做预设动作（bounce/stomp/nod/munch/stretch/fly/roar/breathe），特效层由 DeepSeek 加 CSS 动画
- Lily 不变：character.js 画在最上层，只有 Lily 和特效套蜡笔滤镜

key：依次读环境变量 GPT_API_KEY，或 skill 根目录 .gpt_key_file 里写的 key 文件路径（文件里含 sk-... 即可）。
"""
import base64
import io
import os
import re
from pathlib import Path

import requests
from PIL import Image

import common as c

API = "https://zyx143.xyz/v1/images"
MODEL = "gpt-image-2.5-flare"
KEY_POINTER = c.SKILL / ".gpt_key_file"
SPRITE_DIR = c.ROOT / "sprites"          # 横竖版共用同一套配角姿势图

STYLE = ("Children's crayon picture-book illustration for ages 3-6: soft wax-crayon texture, bright cheerful pastel colors, "
         "thick soft rounded shapes with dark brown crayon outlines (#4A3B33), a few loose crayon hatching strokes, "
         "cute and friendly, nothing scary, suitable for YouTube Kids. No text, no letters, no labels anywhere.")


def api_key():
    if os.environ.get("GPT_API_KEY"):
        return os.environ["GPT_API_KEY"].strip()
    if KEY_POINTER.exists():
        f = Path(KEY_POINTER.read_text(encoding="utf-8").strip())
        if f.exists():
            keys = re.findall(r"sk-[A-Za-z0-9]+", f.read_text(encoding="utf-8"))
            if keys:
                return keys[-1]
    raise SystemExit("没找到 GPT key：设置环境变量 GPT_API_KEY，或在 skill 根目录建 .gpt_key_file 写上 key 文件的路径")


def _post(url, **kw):
    """这个 key 同时只能有 2 个请求：遇到 429（并发上限）或临时 5xx 就等一会儿再试。"""
    import time
    for attempt in range(12):
        for v in kw.get("files", []):           # 重试时文件要从头读
            v[1][1].seek(0)
        r = requests.post(url, headers={"Authorization": f"Bearer {api_key()}"}, timeout=400, **kw)
        if r.status_code not in (429, 500, 502, 503, 504):
            return r
        time.sleep(min(10 + 10 * attempt, 60))
    return r


def _image(r):
    if not r.ok:
        raise RuntimeError(f"GPT 生图失败 HTTP {r.status_code}: {r.text[:300]}")
    return Image.open(io.BytesIO(base64.b64decode(r.json()["data"][0]["b64_json"])))


def generate(prompt, size, quality="high", transparent=False):
    body = {"model": MODEL, "prompt": prompt, "n": 1, "size": size, "quality": quality, "output_format": "png"}
    if transparent:
        body["background"] = "transparent"
    return _image(_post(f"{API}/generations", json=body))


def edit(prompt, refs, size, quality="high", transparent=False):
    files = [("image[]", (Path(p).name, open(p, "rb"), "image/png")) for p in refs]
    data = {"model": MODEL, "prompt": prompt, "n": "1", "size": size, "quality": quality, "output_format": "png"}
    if transparent:
        data["background"] = "transparent"
    return _image(_post(f"{API}/edits", files=files, data=data))


def cover(im, w, h):
    """等比放大裁切到 w×h（接口返回的尺寸不一定是请求的尺寸）。"""
    s = max(w / im.width, h / im.height)
    im = im.convert("RGB").resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def data_uri(im, fmt="PNG"):
    buf = io.BytesIO()
    im.save(buf, fmt, **({"quality": 90} if fmt == "JPEG" else {}))
    return f"data:image/{fmt.lower()};base64," + base64.b64encode(buf.getvalue()).decode()


# ---------------- 设定图、背景、配角姿势 ----------------

def draw_cast(name):
    prompt = (f"CHARACTER MODEL SHEET of ONE supporting character for a children's picture book.\n{STYLE}\n\n"
              f"Character: {c.CAST[name]}\n\n"
              "Layout: plain flat cream paper background (#FFF8EC), nothing else in the background. Show the SAME character twice at "
              "the same size and with identical colors and markings: LEFT half = side view facing right, RIGHT half = front view facing "
              "the viewer. Both stand on the same invisible ground line with a soft oval shadow (a flying character hovers above its "
              "shadow). Full body visible, nothing cropped. Friendly happy face. No props, no other characters.")
    c.CAST_DIR.mkdir(exist_ok=True)
    generate(prompt, "1536x1024").save(c.CAST_DIR / f"{name}.png")
    c.set_approved([name], ok=False)
    print("已生成", c.CAST_DIR / f"{name}.png")


BG_SIZE = {"16x9": "1600x896", "3x4": "1200x1600"}


def draw_background():
    prompt = (f"{STYLE}\n\nA full-page BACKGROUND illustration for a children's picture book, "
              f"{'wide landscape 16:9' if not c.PORTRAIT else 'tall portrait 3:4'} format, eye-level view, no characters:\n"
              f"{c.STORY.BACKGROUND}\n\nComposition guide (approximate positions on a {c.W}x{c.H} canvas):\n{c.STORY.LAYOUT[c.FMT]}\n"
              "Keep the middle ground open and calm so characters can be placed there later. Simple, not too detailed.")
    im = cover(generate(prompt, BG_SIZE[c.FMT]), c.W, c.H)
    im.save(c.SRC / "_bg.png")
    print("已生成", c.SRC / "_bg.png")


def sprite_path(scene, name):
    return SPRITE_DIR / f"{scene['name']}_{name}.png"


def draw_sprite(scene, name, redo=False):
    """场景里某个配角的姿势图：透明底，用定稿设定图做参考。横竖版共用。"""
    f = sprite_path(scene, name)
    if f.exists() and not redo:
        return f
    for other in c.SCENES:   # 别的场景里同一个配角、同样的姿势已经画过：直接复用，保证一模一样（如浴缸）
        g = sprite_path(other, name)
        if other is not scene and other.get("sprites", {}).get(name) == scene["sprites"][name] and g.exists() and not redo:
            SPRITE_DIR.mkdir(exist_ok=True)
            f.write_bytes(g.read_bytes())
            return f
    prompt = (f"{STYLE}\n\nDraw the SAME character as in the reference model sheet - identical design, proportions, colors and "
              f"markings - as ONE single full-body figure (not a model sheet, only one view):\n{c.CAST[name]}\n\n"
              f"Pose in this scene: {scene['sprites'][name]}\n\n"
              "Fully transparent background: no ground, no shadow, no scenery, no other characters, no effects or sound lines. "
              "Whole body visible, nothing cropped.")
    im = edit(prompt, [c.CAST_DIR / f"{name}.png"], "1024x1024", transparent=True)
    SPRITE_DIR.mkdir(exist_ok=True)
    im = im.convert("RGBA")
    im.crop(im.getchannel("A").point(lambda a: 255 if a > 20 else 0).getbbox()).save(f)
    print("已生成", f)
    return f


# ---------------- 摆放 ----------------
# 场景里 "place_16x9" / "place_3x4": {"名字": {"x":..., "y":..., "h":...}}，(x, y) 是脚底中心（飞的角色是图片底边中心），h 是高度。
# 想让配角的某个部位贴到 Lily 手边时，写 {"anchor": "handR", "h": ..., "dx": 0, "dy": 0}：
# 配角最左边的点（朝左面向 Lily 时就是它伸过来的头或嘴）会对齐到 Lily 的右手（再偏移 dx, dy）。

def place(scene, name, pts):
    spec = scene["place_" + c.FMT][name]
    im = Image.open(sprite_path(scene, name))
    h = spec["h"]
    w = round(im.width * h / im.height)
    if "anchor" in spec:
        a = im.getchannel("A")
        col = next(x for x in range(im.width) if a.crop((x, 0, x + 1, im.height)).getbbox())
        band = a.crop((col, 0, min(col + max(im.width // 30, 4), im.width), im.height)).getbbox()
        ay = (band[1] + band[3]) / 2 * h / im.height
        hand = pts[spec["anchor"]]
        x0, y0 = hand["x"] + spec.get("dx", 0), hand["y"] + spec.get("dy", 0) - ay
    else:
        x0, y0 = spec["x"] - w / 2, spec["y"] - h
    return im, round(x0), round(y0), w, h


MOTION_CSS = """
.sp { transform-box: fill-box; transform-origin: 50% 100%; }
.m-bounce  { animation: m-bounce 0.6s ease-in-out infinite alternate; }
.m-stomp   { animation: m-stomp 0.5s ease-in-out infinite alternate; }
.m-nod     { animation: m-nod 0.8s ease-in-out infinite alternate; }
.m-munch   { animation: m-munch 0.35s ease-in-out infinite alternate; transform-origin: 70% 100%; }
.m-stretch { animation: m-stretch 1.0s ease-in-out infinite alternate; }
.m-fly     { animation: m-fly 1.1s ease-in-out infinite alternate; transform-origin: 50% 50%; }
.m-drift   { animation: m-drift 2.4s ease-in-out infinite alternate; }
.m-roar    { animation: m-roar 0.5s ease-in-out infinite alternate; }
.m-breathe { animation: m-breathe 1.2s ease-in-out infinite alternate; }
@keyframes m-bounce  { from { transform: translateY(0); } to { transform: translateY(-14px); } }
@keyframes m-stomp   { from { transform: translateY(0) rotate(-2deg); } to { transform: translateY(-10px) rotate(2deg); } }
@keyframes m-nod     { from { transform: rotate(-3deg); } to { transform: rotate(3deg); } }
@keyframes m-munch   { from { transform: rotate(0deg); } to { transform: rotate(-4deg); } }
@keyframes m-stretch { from { transform: scaleY(1); } to { transform: scaleY(1.05); } }
@keyframes m-fly     { from { transform: translateY(0) rotate(-3deg); } to { transform: translateY(-22px) rotate(3deg); } }
@keyframes m-drift   { from { transform: translateX(-18px); } to { transform: translateX(18px); } }
@keyframes m-roar    { from { transform: scale(1); } to { transform: scale(1.06) translateY(-6px); } }
@keyframes m-breathe { from { transform: scale(1); } to { transform: scale(1.02); } }
"""


def sprites_layer(scene, pts, animated, front=False):
    """配角图片层。animated=True 时加预设动作（每个配角错开一点时间）。
    摆放里写 "front": True 的配角（浴缸、被子）画在 Lily 前面，front=True 时只返回这些。"""
    out, boxes = [], []
    for k, name in enumerate(scene.get("cast", [])):
        if bool(scene["place_" + c.FMT][name].get("front")) != front:
            continue
        im, x, y, w, h = place(scene, name, pts)
        boxes.append((name, x, y, x + w, y + h))
        img = im.resize((w * 2, h * 2), Image.LANCZOS) if im.width > w * 2 else im   # 留 2 倍清晰度，镜头推近也不糊
        tag = f'<image href="{data_uri(img)}" x="{x}" y="{y}" width="{w}" height="{h}"/>'
        moves = scene.get("anim", {}).get(name, "bounce").split()
        if animated:
            for m in moves:
                tag = f'<g class="sp m-{m}" style="animation-delay:-{0.17 * k:.2f}s">{tag}</g>'
        if "fly" not in moves and not front:      # 站在地上的配角脚下加一块淡淡的影子
            tag = (f'<ellipse cx="{x + w / 2:.0f}" cy="{y + h - 4}" rx="{w * 0.4:.0f}" ry="{max(h * 0.035, 8):.0f}" '
                   f'fill="#6B5A3E" opacity="0.22"/>' + tag)
        out.append(tag)
    return "".join(out), boxes


def fx_prompt(scene, boxes, pts):
    occupied = "; ".join(f"{n}: x={a}..{b}, y={t}..{d}" for n, a, t, b, d in boxes)
    return (f"Draw ONLY small cute EFFECTS for a {'3:4 portrait' if c.PORTRAIT else '16:9'} picture-book page for the line: "
            f"\"{scene['line']}\" on a transparent canvas: no characters, no animals, no people, no sky, no ground, no full-canvas "
            f"rectangles. The characters are already placed as separate pictures in these boxes - draw the effects AROUND them, "
            f"never covering a face: {occupied}. Lily (a girl) occupies x={pts['left']}..{pts['right']}, y={pts['top']}..{pts['bottom']} "
            f"- keep that box empty.\n\nEffects wanted: {scene['fx_' + c.FMT]}\n\nColors: bright and cheerful (yellow #FFD84D, pink "
            f"#FF9EC4, sky blue #7CC4F2, mint #8EDFB0, white); stars and sparkles are FILLED with these colors - never black or dark "
            f"fills, only thin dark outlines.\n\n" + c.FORMAT.format(w=c.W, h=c.H))


def scene_svg(scene, bg_uri, sprites, fx, lily_svg, extra_style="", front=""):
    """完整一页：背景图 + 配角图 + 特效 + Lily（只有特效和 Lily 套蜡笔滤镜）+ 前景配角 + 纸纹。"""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {c.W} {c.H}" width="{c.W}" height="{c.H}">'
            f"<defs>{c.CRAYON_DEFS}</defs><style>{MOTION_CSS}{extra_style}</style>"
            f'<g id="camera"><image href="{bg_uri}" width="{c.W}" height="{c.H}"/>{sprites}'
            f'<g filter="url(#crayon)">{c.strip_svg(fx)}<g id="lily-slot">{lily_svg}</g></g>{front}'
            f'<rect width="{c.W}" height="{c.H}" filter="url(#paper)" opacity="0.6"/></g></svg>')

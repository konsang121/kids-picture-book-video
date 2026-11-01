"""第 3 步 动画：镜头推拉摇移（story.py 里的 camera）+ 角色小动作（DeepSeek 加 CSS 动画），逐帧导出 MP4。

每段 CLIP 秒（默认 4 秒）；如果 story.py 里有 TEASER，还会额外导出 00_teaser.mp4：
用最后一幕（所有角色同框）从近景快速拉开成全景，作为视频开头 2 秒的预告钩子。

用法：
    python animate.py --project ...            # 16:9 → 动画/
    python animate.py --project ... --3x4      # 3:4 → 3x4/动画/
    python animate.py --project ... 2 --redo   # 让模型重新设计第 2 个场景的角色动作
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

import common as c

REDO = "--redo" in sys.argv
OUT = c.SRC / "动画"
FPS = 25

ANIM_RULES = """You will receive the CHARACTER LAYER of a picture-book page as SVG. Add gentle, cute CSS animation to it.

Rules (strict):
- Keep EVERY existing drawing element (path, circle, ellipse, rect, polygon, line, polyline, use, defs) exactly as it is:
  same attributes, same order, nothing deleted, nothing redrawn.
- You may only: (a) wrap existing elements in new <g> groups with an id, (b) add ONE <style> block with @keyframes and rules.
- Wrap each character as a whole (e.g. #lily, #ghost, #cat) and wrap the moving parts (arm, tail, head, candies...)
  in their own groups, so you can animate them separately.
- NEVER animate an element that has a transform attribute (CSS transform would override it). Always animate a NEW wrapper <g>
  that has no transform attribute.
- Every animated group must have `transform-box: fill-box;` and a correct `transform-origin` (e.g. the shoulder end of an arm,
  the base of a tail, the bottom center of a bouncing body).
- Only animate transform and opacity. Use CSS @keyframes only: no JavaScript, no SMIL (<animate>), no filters.
- The clip is 4-5 seconds long; all animations start at 0s and something must already be moving in the first 0.3s; use ease-in-out and `infinite` or `alternate infinite` where it fits.
- Nothing may fade out, shrink away or disappear at the end: from 1s to 5s every character must stay fully visible.
- Keep motion small and smooth: translate up to 15px, rotate up to 20deg, scale 0.92-1.08 (a pop-in from scale 0 is allowed).
- Output the full SVG and nothing else."""

DRAW_TAGS = re.compile(r"<(path|circle|ellipse|rect|polygon|polyline|line|use)\b")


def bg_inner():
    return c.strip_svg(c.unhide((c.SRC / "_bg_raw.svg").read_text(encoding="utf-8"), c.hide_ids()))


def chars_layer(name, bg):
    """出图时保存的配角层（不含 Lily，Lily 每帧由 character.js 重新画）。"""
    return c.strip_svg((c.SRC / f"_cast_{name}.svg").read_text(encoding="utf-8"))


# Lily 每帧的动作参数：走路/跳跃/手势按周期推进 t；站立类动作轻轻上下起伏
LILY_PERIOD = {"walk": 0.8, "jump": 1.0, "wave": 0.9, "cheer": 1.0, "flap": 0.6, "pat": 1.1, "call": 1.4, "nose": 1.0,
               "touchNose": 0.7, "touchEars": 0.8, "touchEyes": 2.0, "touchMouth": 1.6, "touchAll": 4.0, "knock": 1.3,
               "brushTeeth": 0.5, "washFace": 1.0, "scrubHands": 0.6, "combHair": 1.4,
               "washHair": 0.7, "popBubble": 1.3, "shh": 2.0}
LILY_JS = """
window.__lilyBase = %s;
window.__lily = function (sec) {
  const P = %s, o = Object.assign({}, __lilyBase), per = P[o.action] || 1.4;
  // touchAll 是一整句的连贯动作：只走一遍，最后停在欢呼
  o.t = o.action === "touchAll" ? Math.min(sec / per, 0.999) : ((o.t || 0) + sec / per) %% 1;
  if (!(o.action in P)) o.y = o.y - 4 * o.scale * Math.abs(Math.sin(Math.PI * sec / 0.7));
  document.getElementById("lily-slot").innerHTML = Lily.draw(o);
};
__lily(0);
"""


def animate_chars(s, chars):
    cache = OUT / f"_anim_{s['name']}.svg"
    if cache.exists() and not REDO:
        return cache.read_text(encoding="utf-8")
    src = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {c.W} {c.H}">{chars}</svg>'
    want = len(DRAW_TAGS.findall(src))
    for attempt in range(3):
        svg = c.ask(ANIM_RULES, f'Picture-book line: "{s["line"]}"\n\nMotion to add (this layer has NO Lily in it - skip anything about Lily):\n{s["motion"]}\n\nCharacter layer SVG:\n{src}')
        got = len(DRAW_TAGS.findall(svg))
        if got >= want * 0.97 and "@keyframes" in svg:
            cache.write_text(svg, encoding="utf-8")
            return svg
        print(f"{s['name']}: 第 {attempt + 1} 次结果不合格（图形 {got}/{want}），重试")
    raise RuntimeError(f"{s['name']}: 模型没能在保留原图的前提下加上动画")


def camera_css(keys, seconds):
    """镜头关键帧 (时间%, 中心x, 中心y, 放大倍数) → CSS，保证画面不会移出画布边缘。"""
    frames = []
    for pct, cx, cy, s in keys:
        cx = min(max(cx, c.W / (2 * s)), c.W - c.W / (2 * s))
        cy = min(max(cy, c.H / (2 * s)), c.H - c.H / (2 * s))
        frames.append(f"{pct}% {{ transform: translate({c.W / 2}px, {c.H / 2}px) scale({s}) translate({-cx:.1f}px, {-cy:.1f}px); }}")
    return ("#camera { transform-origin: 0 0; animation: cam %ss ease-in-out forwards; }\n"
            "@keyframes cam { %s }" % (seconds, " ".join(frames)))


def page_html(s, bg, anim_svg, camera=None, seconds=None):
    hide = "".join(f"#{h}{{display:none}}" for h in s.get("hide", []))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {c.W} {c.H}" width="{c.W}" height="{c.H}">'
           f"<defs>{c.CRAYON_DEFS}</defs><style>{camera_css(camera or s['camera_' + c.FMT], seconds or c.clip_len(s))}\n{hide}</style>"
           f'<g id="camera"><rect width="{c.W}" height="{c.H}" fill="#FFF8EC"/>'
           f'<g filter="url(#crayon)">{bg}{c.strip_svg(anim_svg)}<g id="lily-slot"></g></g>'
           f'<rect width="{c.W}" height="{c.H}" filter="url(#paper)"/></g></svg>')
    script = c.CHARACTER_JS.read_text(encoding="utf-8") + LILY_JS % (json.dumps(c.lily_opts(s)), json.dumps(LILY_PERIOD))
    return f'<html><body style="margin:0;overflow:hidden;background:#FFF8EC">{svg}<script>{script}</script></body></html>'


def gpt_parts(s):
    """GPT 引擎：配角图片层（预设动作）+ 特效层（DeepSeek 加 CSS 动画）。"""
    import gpt
    _, pts = c.lily_render(c.lily_opts(s))
    sprites, _ = gpt.sprites_layer(s, pts, animated=True)
    front, _ = gpt.sprites_layer(s, pts, animated=True, front=True)
    fx = animate_chars(s, c.strip_svg((c.SRC / f"_fx_{s['name']}.svg").read_text(encoding="utf-8")))
    return sprites, fx, front


def page_html_gpt(s, bg_uri, parts, camera=None, seconds=None):
    import gpt
    sprites, fx, front = parts
    svg = gpt.scene_svg(s, bg_uri, sprites, fx, "", camera_css(camera or s["camera_" + c.FMT], seconds or c.clip_len(s)), front)
    script = c.CHARACTER_JS.read_text(encoding="utf-8") + LILY_JS % (json.dumps(c.lily_opts(s)), json.dumps(LILY_PERIOD))
    return f'<html><body style="margin:0;overflow:hidden;background:#FFF8EC">{svg}<script>{script}</script></body></html>'


def render_video(page, name, html, seconds):
    page.set_content(html)
    page.wait_for_timeout(300)
    page.evaluate("window.__a = document.getAnimations(); __a.forEach(a => a.pause())")
    frames = Path(tempfile.mkdtemp(prefix=f"frames_{name}_"))
    try:
        for f in range(int(round(FPS * seconds))):
            page.evaluate(f"__lily({f / FPS}); __a.forEach(a => a.currentTime = {f * 1000 / FPS})")
            page.screenshot(path=str(frames / f"{f:04d}.png"))
        mp4 = OUT / f"{name}.mp4"
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-framerate", str(FPS),
                        "-i", str(frames / "%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                        "-movflags", "+faststart", str(mp4)], check=True)
        print("已生成", mp4)
    finally:
        shutil.rmtree(frames)


if __name__ == "__main__":
    only = [a for a in c.positional() if a.isdigit()]   # 0 = 只做预告
    scenes = [s for i, s in enumerate(c.SCENES, 1) if not only or str(i) in only]
    OUT.mkdir(parents=True, exist_ok=True)
    if c.ENGINE == "gpt":
        import gpt
        bg_uri = gpt.data_uri(gpt.Image.open(c.SRC / "_bg.png").convert("RGB"), "JPEG")
        todo = scenes + ([c.SCENES[-1]] if c.TEASER and (not only or "0" in only) and c.SCENES[-1] not in scenes else [])
        with ThreadPoolExecutor(5) as pool:
            parts = dict(zip([t["name"] for t in todo], pool.map(gpt_parts, todo)))
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome")
            page = browser.new_page(viewport={"width": c.W, "height": c.H})
            for s in scenes:
                render_video(page, s["name"], page_html_gpt(s, bg_uri, parts[s["name"]]), c.clip_len(s))
            if c.TEASER and (not only or "0" in only):
                last = c.SCENES[-1]
                _, cx, cy, z = last["camera_" + c.FMT][0]
                cam = [(0, cx, cy, min(max(z, 1.2), 1.25)), (70, c.W / 2, c.H / 2, 1.0), (100, c.W / 2, c.H / 2, 1.0)]
                render_video(page, "00_teaser", page_html_gpt(last, bg_uri, parts[last["name"]], cam, c.TEASER_SECONDS),
                             c.TEASER_SECONDS)
            browser.close()
        raise SystemExit
    bg = bg_inner()
    with ThreadPoolExecutor(5) as pool:
        anims = list(pool.map(lambda s: animate_chars(s, chars_layer(s["name"], bg)), scenes))
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": c.W, "height": c.H})
        for s, anim in zip(scenes, anims):
            render_video(page, s["name"], page_html(s, bg, anim, seconds=c.clip_len(s)), c.clip_len(s))
        if c.TEASER and (not only or "0" in only):
            # 预告：最后一幕，从它镜头的第一个关键帧（近景）用 2 秒快速拉开到全景
            last = c.SCENES[-1]
            anim = animate_chars(last, chars_layer(last["name"], bg))
            _, cx, cy, z = last["camera_" + c.FMT][0]
            cam = [(0, cx, cy, min(max(z, 1.2), 1.25)),   # 不要推太近，否则上方的大字会挡住 Lily 的头
                    (70, c.W / 2, c.H / 2, 1.0), (100, c.W / 2, c.H / 2, 1.0)]
            render_video(page, "00_teaser", page_html(last, bg, anim, cam, c.TEASER_SECONDS), c.TEASER_SECONDS)
        browser.close()

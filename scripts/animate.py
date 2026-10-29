"""第 3 步 动画：镜头推拉摇移（story.py 里的 camera）+ 角色小动作（DeepSeek 加 CSS 动画），逐帧导出 5 秒 MP4。

用法：
    python animate.py --project ...            # 16:9 → 动画/
    python animate.py --project ... --3x4      # 3:4 → 3x4/动画/
    python animate.py --project ... 2 --redo   # 让模型重新设计第 2 个场景的角色动作
"""
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
FPS, SECONDS = 25, 5

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
- The clip is 5 seconds long; all animations start at 0s; use ease-in-out and `infinite` or `alternate infinite` where it fits.
- Nothing may fade out, shrink away or disappear at the end: from 1s to 5s every character must stay fully visible.
- Keep motion small and smooth: translate up to 15px, rotate up to 20deg, scale 0.92-1.08 (a pop-in from scale 0 is allowed).
- Output the full SVG and nothing else."""

DRAW_TAGS = re.compile(r"<(path|circle|ellipse|rect|polygon|polyline|line|use)\b")


def bg_inner():
    return c.strip_svg(c.unhide((c.SRC / "_bg_raw.svg").read_text(encoding="utf-8"), c.hide_ids()))


def chars_layer(name, bg):
    """从合成好的场景 SVG 里取出角色层（背景之后、蜡笔滤镜组结束之前的部分）。"""
    scene = (c.SRC / f"{name}.svg").read_text(encoding="utf-8")
    i = scene.index(bg) + len(bg)
    return scene[i:scene.rindex("</g><rect")]


def animate_chars(s, chars):
    cache = OUT / f"_anim_{s['name']}.svg"
    if cache.exists() and not REDO:
        return cache.read_text(encoding="utf-8")
    src = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {c.W} {c.H}">{chars}</svg>'
    want = len(DRAW_TAGS.findall(src))
    for attempt in range(3):
        svg = c.ask(ANIM_RULES, f'Picture-book line: "{s["line"]}"\n\nMotion to add:\n{s["motion"]}\n\nCharacter layer SVG:\n{src}')
        got = len(DRAW_TAGS.findall(svg))
        if got >= want * 0.97 and "@keyframes" in svg:
            cache.write_text(svg, encoding="utf-8")
            return svg
        print(f"{s['name']}: 第 {attempt + 1} 次结果不合格（图形 {got}/{want}），重试")
    raise RuntimeError(f"{s['name']}: 模型没能在保留原图的前提下加上动画")


def camera_css(keys):
    """镜头关键帧 (时间%, 中心x, 中心y, 放大倍数) → CSS，保证画面不会移出画布边缘。"""
    frames = []
    for pct, cx, cy, s in keys:
        cx = min(max(cx, c.W / (2 * s)), c.W - c.W / (2 * s))
        cy = min(max(cy, c.H / (2 * s)), c.H - c.H / (2 * s))
        frames.append(f"{pct}% {{ transform: translate({c.W / 2}px, {c.H / 2}px) scale({s}) translate({-cx:.1f}px, {-cy:.1f}px); }}")
    return ("#camera { transform-origin: 0 0; animation: cam %ss ease-in-out forwards; }\n"
            "@keyframes cam { %s }" % (SECONDS, " ".join(frames)))


def page_html(s, bg, anim_svg):
    hide = "".join(f"#{h}{{display:none}}" for h in s.get("hide", []))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {c.W} {c.H}" width="{c.W}" height="{c.H}">'
           f"<defs>{c.CRAYON_DEFS}</defs><style>{camera_css(s['camera_' + c.FMT])}\n{hide}</style>"
           f'<g id="camera"><rect width="{c.W}" height="{c.H}" fill="#FFF8EC"/>'
           f'<g filter="url(#crayon)">{bg}{c.strip_svg(anim_svg)}</g>'
           f'<rect width="{c.W}" height="{c.H}" filter="url(#paper)"/></g></svg>')
    return f'<html><body style="margin:0;overflow:hidden;background:#FFF8EC">{svg}</body></html>'


def render_video(page, name, html):
    page.set_content(html)
    page.wait_for_timeout(300)
    page.evaluate("window.__a = document.getAnimations(); __a.forEach(a => a.pause())")
    frames = Path(tempfile.mkdtemp(prefix=f"frames_{name}_"))
    try:
        for f in range(FPS * SECONDS):
            page.evaluate(f"__a.forEach(a => a.currentTime = {f * 1000 / FPS})")
            page.screenshot(path=str(frames / f"{f:04d}.png"))
        mp4 = OUT / f"{name}.mp4"
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-framerate", str(FPS),
                        "-i", str(frames / "%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                        "-movflags", "+faststart", str(mp4)], check=True)
        print("已生成", mp4)
    finally:
        shutil.rmtree(frames)


if __name__ == "__main__":
    only = [a for a in c.positional() if a.isdigit()]
    scenes = [s for i, s in enumerate(c.SCENES, 1) if not only or str(i) in only]
    OUT.mkdir(parents=True, exist_ok=True)
    bg = bg_inner()
    with ThreadPoolExecutor(5) as pool:
        anims = list(pool.map(lambda s: animate_chars(s, chars_layer(s["name"], bg)), scenes))
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": c.W, "height": c.H})
        for s, anim in zip(scenes, anims):
            render_video(page, s["name"], page_html(s, bg, anim))
        browser.close()

"""第 2 步 出图：DeepSeek 画 SVG（背景一次 + 每个场景的角色层），加蜡笔滤镜后用 Chrome 导出 PNG。

用法（--project 默认当前目录，竖版加 --3x4）：
    python generate.py --project D:\\桌面\\圣诞节绘本            # 背景 + 5 个场景
    python generate.py --project ... 3                         # 只重画第 3 个场景
    python generate.py --project ... bg                        # 只重画背景（输出 _bg_preview.png）
    python generate.py --project ... 0                         # 重画 Lily 定妆图（会覆盖 _lily_raw.svg，慎用）
"""
import common as c


def draw_lily():
    w, h = 1200, 900
    svg = c.ask(c.STYLE, f"Draw a character sheet of {c.lily_description()}\n\nShow Lily three times on a plain light background: "
                         f"front view (center, largest), side view (left), back view (right), full body, standing.\n\n"
                         + c.FORMAT.format(w=w, h=h))
    c.render("00_lily_character", c.crayonize(svg, w, h), w, h, c.ROOT)
    return svg


def draw_background():
    ids = c.hide_ids()
    groups = ("\n- These switchable groups MUST exist with these exact ids (both drawn, only one shown per scene): "
              + ", ".join(f'<g id="{i}">' for i in ids)) if ids else ""
    svg = c.ask(c.STYLE, f"Draw ONLY the background, no characters:\n{c.STORY.BACKGROUND}{groups}\n\n"
                         f"{c.STORY.LAYOUT[c.FMT]}\n\n" + c.FORMAT.format(w=c.W, h=c.H))
    missing = [i for i in ids if f'id="{i}"' not in svg]
    if missing:
        raise RuntimeError(f"背景缺少分组 {missing}，请重画背景：python generate.py bg")
    return svg


def draw_scene(i, lily_svg, bg_svg):
    s = c.SCENES[i - 1]
    ref = ("\n\nReference drawing of Lily (a character sheet with 3 views; draw Lily only ONCE). Copy the front view's face, "
           "hair, dress, tights and shoes exactly; her costume and props follow the description above, not the reference:\n" + lily_svg)
    chars = c.ask(c.STYLE + "\n\nMain character (must look exactly like this in every picture):\n" + c.lily_description() + ref,
                  f"Draw the CHARACTER LAYER of a {'3:4 portrait' if c.PORTRAIT else '16:9'} picture-book page for the line: \"{s['line']}\"\n\n"
                  f"The background is already drawn separately. Draw ONLY the characters, their props and small effects on a "
                  f"transparent canvas: no sky, no ground, no buildings, no full-canvas rectangles. Add a soft light-brown oval "
                  f"shadow (opacity 0.25) under each standing character. Draw ONLY the characters named in the scene - no extra animals or people.\n\n"
                  f"{c.STORY.LAYOUT[c.FMT]}\n\nScene: {s['action_' + c.FMT]}\n"
                  f"Lily is the main focus: large ({c.STORY.LILY_SIZE[c.FMT]}), interacting with the other character.\n\n"
                  + c.FORMAT.format(w=c.W, h=c.H))
    hide = "".join(f"#{h}{{display:none}}" for h in s.get("hide", []))
    scene = f"<style>{hide}</style>{c.strip_svg(c.unhide(bg_svg, c.hide_ids()))}{c.strip_svg(chars)}"
    c.render(s["name"], c.crayonize(scene, c.W, c.H), c.W, c.H)


def cached(f, draw, redo):
    if redo or not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(draw(), encoding="utf-8")
    return f.read_text(encoding="utf-8")


if __name__ == "__main__":
    args = c.positional()
    arg = args[0] if args else None
    if arg == "0":
        (c.ROOT / "_lily_raw.svg").write_text(draw_lily(), encoding="utf-8")
    lily = c.lily_reference()
    bg = cached(c.SRC / "_bg_raw.svg", draw_background, arg in (None, "bg"))
    if arg == "bg":
        first_hide = "".join(f"#{h}{{display:none}}" for h in c.SCENES[0].get("hide", []))
        c.render("_bg_preview", c.crayonize(f"<style>{first_hide}</style>{c.strip_svg(c.unhide(bg, c.hide_ids()))}", c.W, c.H), c.W, c.H)
    for i in range(1, len(c.SCENES) + 1):
        if arg in (None, str(i)):
            draw_scene(i, lily, bg)

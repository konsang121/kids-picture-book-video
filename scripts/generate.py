"""第 2 步 出图：DeepSeek 画 SVG（背景一次 + 每个场景的配角层），Lily 由 character.js 画，加蜡笔滤镜后用 Chrome 导出 PNG。

用法（--project 默认当前目录，竖版加 --3x4）：
    python generate.py --project D:\\桌面\\圣诞节绘本            # 背景 + 5 个场景
    python generate.py --project ... 3                         # 只重画第 3 个场景
    python generate.py --project ... bg                        # 只重画背景（输出 _bg_preview.png）
    python generate.py --project ... cast                      # 给 story.py 里 CAST 的配角出设定图（已定稿的跳过）
    python generate.py --project ... cast cow                  # 重画某个配角的设定图（会取消它的定稿）
    python generate.py --project ... approve cow sheep         # 用户确认后，把配角标记为定稿（只在用户明确同意后运行）

配角没有定稿时，出场了这个配角的场景不能出图（finalize.py 也不能输出成品）。
"""
import common as c


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


def draw_cast(name):
    """配角设定图：侧面 + 正面两个视图，四条腿的动物必须四条腿着地。"""
    w, h = 1200, 640
    svg = c.ask(c.STYLE, f"Draw a CHARACTER MODEL SHEET for a supporting character in a children's picture book:\n{c.CAST[name]}\n\n"
                         f"Background: ONE flat rect filled #FFF8EC and nothing else (no gradient, no clouds, no ground lines, no grass). "
                         f"Follow EVERY detail of the description exactly (colors, markings, ear and tail shapes, number of legs). "
                         f"Show the SAME character twice, same size and same colors: "
                         f"LEFT = side view facing right (x=80..560), RIGHT = front view (x=660..1120); both standing on the ground "
                         f"line y=560 with a soft oval shadow, about 380px tall. Natural animal anatomy and posture (never standing upright "
                         f"like a human unless the description says so). Friendly happy face, mouth closed. No props, no other characters.\n\n"
                         + c.FORMAT.format(w=w, h=h))
    c.CAST_DIR.mkdir(exist_ok=True)
    (c.CAST_DIR / f"{name}_raw.svg").write_text(svg, encoding="utf-8")
    c.render(name, c.crayonize(svg, w, h), w, h, c.CAST_DIR)
    c.set_approved([name], ok=False)      # 新画的设定图需要重新审核


def draw_scene(i, bg_svg):
    s = c.SCENES[i - 1]
    cast = s.get("cast", [])
    c.require_cast(cast, f"画第 {i} 个场景")
    lily_svg, pts = c.lily_render(c.lily_opts(s))
    cast_ref = "".join(
        f"\n\nSupporting character '{n}' (APPROVED design - copy its shapes, proportions, colors and markings exactly from the "
        f"reference sheet below; only change pose and facing as the scene needs, and keep natural animal anatomy):\n{c.CAST[n]}\n"
        f"Reference sheet (left = side view, right = front view):\n{c.cast_reference(n)}" for n in cast)
    who = (", ".join(cast) if cast else "no other characters - only the small effects named in the scene")
    lily_note = (f"The main character Lily (a little girl) is drawn SEPARATELY by another program and will be placed ON TOP of your layer. "
                 f"Do NOT draw Lily or any girl/person. Her body occupies the box x={pts['left']}..{pts['right']}, y={pts['top']}..{pts['bottom']}; "
                 f"her head center is at ({pts['head']['x']},{pts['head']['y']}); her left hand is at ({pts['handL']['x']},{pts['handL']['y']}) "
                 f"and her right hand is at ({pts['handR']['x']},{pts['handR']['y']}). Keep that box empty (except where a character must touch "
                 f"her hand), and place the other characters so they clearly interact with her at those positions. "
                 f"Ignore any instructions about Lily's own pose in the scene text - only use them to understand the interaction.")
    chars = c.ask(c.STYLE + cast_ref,
                  f"Draw the SUPPORTING-CHARACTER LAYER of a {'3:4 portrait' if c.PORTRAIT else '16:9'} picture-book page for the line: \"{s['line']}\"\n\n"
                  f"The background is already drawn separately. Draw ONLY: {who}, plus small effects (sound lines, sparkles, music notes), on a "
                  f"transparent canvas: no sky, no ground, no buildings, no full-canvas rectangles. Add a soft light-brown oval shadow "
                  f"(opacity 0.25) under each standing character. No extra animals or people.\n\n{lily_note}\n\n"
                  f"{c.STORY.LAYOUT[c.FMT]}\n\nScene: {s['action_' + c.FMT]}\n\n" + c.FORMAT.format(w=c.W, h=c.H))
    (c.SRC / f"_cast_{s['name']}.svg").write_text(chars, encoding="utf-8")   # 动画步骤从这里取配角层
    hide = "".join(f"#{h}{{display:none}}" for h in s.get("hide", []))
    scene = f"<style>{hide}</style>{c.strip_svg(c.unhide(bg_svg, c.hide_ids()))}{c.strip_svg(chars)}{lily_svg}"
    c.render(s["name"], c.crayonize(scene, c.W, c.H), c.W, c.H)


def cached(f, draw, redo):
    if redo or not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(draw(), encoding="utf-8")
    return f.read_text(encoding="utf-8")


if __name__ == "__main__":
    args = c.positional()
    arg = args[0] if args else None
    if arg == "cast":
        names = args[1:] or [n for n in c.CAST if c.unapproved([n])]
        for n in names:
            draw_cast(n)
        print("设定图在", c.CAST_DIR, "；请用户审核，确认后运行 generate.py approve <名字>")
        raise SystemExit
    if arg == "approve":
        c.set_approved(args[1:])
        print("已定稿：", ", ".join(args[1:]))
        raise SystemExit
    bg = cached(c.SRC / "_bg_raw.svg", draw_background, arg in (None, "bg"))
    if arg == "bg":
        first_hide = "".join(f"#{h}{{display:none}}" for h in c.SCENES[0].get("hide", []))
        c.render("_bg_preview", c.crayonize(f"<style>{first_hide}</style>{c.strip_svg(c.unhide(bg, c.hide_ids()))}", c.W, c.H), c.W, c.H)
    for i in range(1, len(c.SCENES) + 1):
        if arg in (None, str(i)):
            draw_scene(i, bg)

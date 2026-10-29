"""各步骤共用：项目目录、story.py 配置、DeepSeek 调用、蜡笔滤镜、Chrome 导出。

每个脚本都用 --project <目录> 指定项目（默认当前目录），竖版加 --3x4。
项目目录里必须有 story.py（模板见 skill 的 assets/story_template.py）。
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
# key 文件的位置写在 skill 根目录的 .deepseek_key_file 里（只有一行路径，不会上传到 GitHub）
KEY_POINTER = SKILL / ".deepseek_key_file"
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-flash"
BROWSER = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
VALUE_FLAGS = ("--project", "--voice", "--rate", "--music")


def arg_value(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def positional():
    """命令行里除了 --开关 和它们的取值以外的参数（场景编号、bg、0 等）。"""
    out, skip = [], False
    for a in sys.argv[1:]:
        if skip:
            skip = False
        elif a in VALUE_FLAGS:
            skip = True
        elif not a.startswith("--"):
            out.append(a)
    return out


ROOT = Path(arg_value("--project", os.getcwd())).resolve()
PORTRAIT = "--3x4" in sys.argv
FMT = "3x4" if PORTRAIT else "16x9"
W, H = (1200, 1600) if PORTRAIT else (1600, 900)
SRC = ROOT / "3x4" if PORTRAIT else ROOT     # 当前画幅的图片目录


def load_story():
    f = ROOT / "story.py"
    if not f.exists():
        raise SystemExit(f"{ROOT} 里没有 story.py，先从 {SKILL / 'assets' / 'story_template.py'} 复制一份再改")
    spec = importlib.util.spec_from_file_location("story", f)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


STORY = load_story()
SCENES = STORY.SCENES

# 节奏：短视频观众 1~2 秒内决定去留，所以每段 4 秒，开头先放一段预告（最后一幕的精华 + 一句最好玩的拟声词）
CLIP = float(getattr(STORY, "CLIP", 4.0))
TEASER = getattr(STORY, "TEASER", None)          # {"line": ..., "hook": ...}；None 表示不要预告开头
TEASER_SECONDS = 2.0 if TEASER else 0.0


def clip_len(scene):
    """每段的时长：默认 CLIP，单独一段可以在 story.py 里用 "clip" 加长（比如拟声词很多的最后一句）。"""
    return float(scene.get("clip", CLIP))


def scene_start(i):
    return TEASER_SECONDS + sum(clip_len(s) for s in SCENES[:i])


TOTAL = scene_start(len(SCENES))

# ---------------- 主角 Lily：只由 assets/character.js 绘制（造型已定稿，模型不画她） ----------------
# 每个场景在 story.py 里写 "lily_16x9" / "lily_3x4"：{view, facing, expression, action, prop, t, x, y, scale}
CHARACTER_JS = SKILL / "assets" / "character.js"
LILY_SCALE = {"16x9": 1.6, "3x4": 2.13}     # 绘本里 Lily 的默认大小（约 480px / 640px 高）


def lily_opts(scene):
    o = dict(scene["lily_" + FMT])
    o.setdefault("scale", LILY_SCALE[FMT])
    o["filter"] = False                      # 外层已经有蜡笔滤镜
    return o


def lily_render(opts):
    """调 node 用 character.js 画 Lily，返回 (svg 片段, 关键点)。"""
    js = ("const L=require(process.argv[1]);const o=JSON.parse(process.argv[2]);"
          "process.stdout.write(JSON.stringify({svg:L.draw(o),pts:L.points(o)}))")
    out = subprocess.run(["node", "-e", js, str(CHARACTER_JS), json.dumps(opts)], capture_output=True, text=True,
                         encoding="utf-8", check=True).stdout
    d = json.loads(out)
    return d["svg"], d["pts"]


STYLE = """Style rules:
- children's crayon picture book, bright cheerful colors, fresh and lively, eye-level view
- thick soft rounded shapes, dark outlines (#4A3B33, stroke-width 5-7, stroke-linecap round, stroke-linejoin round)
- everything cute and friendly, nothing scary, suitable for YouTube Kids, ages 3-6
- add a few loose crayon hatching lines (thin strokes, opacity 0.3-0.5) on walls, ground and clothes for a hand-drawn feel;
  NEVER put any lines or streaks in the sky (they look like rain) - the sky is only the smooth gradient plus 2-3 soft clouds"""

FORMAT = """Output format (strict):
- Output ONE complete SVG: <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"> ... </svg>
- No <text> elements, no words or letters anywhere, no <image>, no external references, no <filter>, no <script>.
- Gradients in <defs> are allowed.
- Only output the SVG code, nothing else."""

CRAYON_DEFS = """
<filter id="crayon" x="-2%" y="-2%" width="104%" height="104%">
  <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="3" seed="4" result="warp"/>
  <feDisplacementMap in="SourceGraphic" in2="warp" scale="6" xChannelSelector="R" yChannelSelector="G" result="wobbly"/>
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="8" result="grain"/>
  <feColorMatrix in="grain" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -3.2 2.75" result="grainA"/>
  <feComposite in="wobbly" in2="grainA" operator="in"/>
</filter>
<filter id="paper">
  <feTurbulence type="fractalNoise" baseFrequency="0.6" numOctaves="3" seed="2"/>
  <feColorMatrix type="matrix" values="0 0 0 0 0.55  0 0 0 0 0.45  0 0 0 0 0.35  0 0 0 0.12 0"/>
</filter>"""


# ---------------- 配角：先出设定图，用户确认定稿后才能进镜头 ----------------
# story.py 里 CAST = {"cow": "外形描述（英文，越具体越好）", ...}；每个场景用 "cast": ["cow"] 写明出场的配角。
# 设定图在 <项目>/cast/<名字>.svg/.png，定稿记录在 cast/approved.json。重画某个配角的设定图会取消它的定稿。
CAST = getattr(STORY, "CAST", {})
CAST_DIR = ROOT / "cast"
APPROVED = CAST_DIR / "approved.json"


def approved_cast():
    return json.loads(APPROVED.read_text(encoding="utf-8")) if APPROVED.exists() else {}


def set_approved(names, ok=True):
    data = approved_cast()
    for n in names:
        if ok:
            data[n] = {"svg_bytes": (CAST_DIR / f"{n}.svg").stat().st_size}
        else:
            data.pop(n, None)
    CAST_DIR.mkdir(exist_ok=True)
    APPROVED.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def unapproved(names):
    """还没定稿（或定稿后设定图又被改过）的配角。"""
    data = approved_cast()
    bad = []
    for n in names:
        f = CAST_DIR / f"{n}.svg"
        if n not in data or not f.exists() or data[n]["svg_bytes"] != f.stat().st_size:
            bad.append(n)
    return bad


def require_cast(names, what):
    bad = unapproved(names)
    if bad:
        raise SystemExit(f"配角 {bad} 还没有定稿，不能{what}。先运行 generate.py cast 出设定图，用户确认后再 generate.py approve {' '.join(bad)}")


def cast_reference(name):
    return (CAST_DIR / f"{name}_raw.svg").read_text(encoding="utf-8")


def api_key():
    """依次找：环境变量 DEEPSEEK_API_KEY → 环境变量 DEEPSEEK_KEY_FILE → .deepseek_key_file 里写的路径。
    key 文件里可以只有 key，也可以是 `Key：sk-...` 这样的格式。"""
    if os.environ.get("DEEPSEEK_API_KEY"):
        return os.environ["DEEPSEEK_API_KEY"]
    path = os.environ.get("DEEPSEEK_KEY_FILE") or (KEY_POINTER.read_text(encoding="utf-8").strip() if KEY_POINTER.exists() else "")
    if not path or not Path(path).exists():
        raise SystemExit("没找到 DeepSeek key：设置环境变量 DEEPSEEK_API_KEY，或在 skill 根目录建 .deepseek_key_file 写上 key 文件的路径")
    text = Path(path).read_text(encoding="utf-8")
    m = re.search(r"sk-[A-Za-z0-9]+", text)
    if not m:
        raise SystemExit(f"{path} 里没找到 sk- 开头的 key")
    return m.group(0)


def ask(system, user):
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "max_tokens": 60000,
    }).encode()
    req = urllib.request.Request(API_URL, body, {"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        content = json.load(r)["choices"][0]["message"]["content"]
    m = re.search(r"<svg[\s\S]*</svg>", content)
    if not m:
        raise RuntimeError("模型没有返回 SVG：\n" + content[:500])
    return m.group(0)


def strip_svg(svg):
    return re.sub(r"^<svg[^>]*>|</svg>$", "", svg.strip())


def unhide(svg, ids):
    """模型有时会自己给可切换的分组加 display:none，去掉它，显示与否由场景的 hide 决定。"""
    for i in ids:
        svg = re.sub(rf'(id="{re.escape(i)}")\s+style="[^"]*"', r"\1", svg)
    return svg


def hide_ids():
    return sorted({i for s in SCENES for i in s.get("hide", [])})


def crayonize(svg, w, h):
    """套上纸张底色和蜡笔滤镜。"""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f"<defs>{CRAYON_DEFS}</defs>"
            f'<rect width="{w}" height="{h}" fill="#FFF8EC"/>'
            f'<g filter="url(#crayon)">{strip_svg(svg)}</g>'
            f'<rect width="{w}" height="{h}" filter="url(#paper)"/></svg>')


def render(name, svg, w, h, out=None):
    out = out or SRC
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{name}.svg").write_text(svg, encoding="utf-8")
    html = out / f"_{name}.html"
    html.write_text(f'<html><body style="margin:0;overflow:hidden">{svg}</body></html>', encoding="utf-8")
    png = out / f"{name}.png"
    subprocess.run([BROWSER, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={w},{h}",
                    f"--screenshot={png}", html.as_uri()], check=True, capture_output=True, timeout=120)
    html.unlink()
    print("已生成", png)

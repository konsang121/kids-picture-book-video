"""每期一个 story.py：放在项目文件夹里，所有脚本都读它。

这是万圣节那一期的完整配置，做新主题时复制一份再改：
- TITLE / LILY_EXTRA / HIGHLIGHT：简单替换
- CLIP / TEASER / MUSIC：节奏和开头钩子（短视频观众 1~2 秒内决定去留，一般不用改）
- BACKGROUND / LAYOUT：新场景（坐标决定角色站哪、房子/门在哪，镜头和动作都依赖它）
- SCENES：5 句文案 + 每句的画面（横版、竖版各一份）、镜头、角色动作、要隐藏的背景分组
"""

TITLE = "万圣节"                     # 成品文件名前缀：成品/万圣节_16x9.mp4

CLIP = 4.0                           # 每段秒数；某一段说不完时，在那一段里加 "clip": 5.0
# 开头 2 秒预告：最后一幕从近景拉开 + 一句很短的问句（1.5 秒内说完）+ 画面上方的大字悬念
TEASER = {"line": "Who is at the door?", "hook": "Who is at the door? 👀"}
MUSIC = "playful"                    # "playful" 轻快（默认）/ "lullaby" 摇篮曲（睡前主题用）

# 本期 Lily 额外的服装/道具（和固定形象叠加）；不需要就留空字符串
LILY_EXTRA = ("purple witch hat (#8E5BD6): a wide flat brim plus a TALL cone with a SHARP pointed tip (tip bent slightly to one side), "
              "orange band (#FF8C1A); she carries an orange pumpkin-shaped candy bucket (#FF8C1A) with a black handle and a carved "
              "jack-o'-lantern face that is SMILING: two triangle eyes and a wide upward-curving U-shaped grin (never a frown)")

# 字幕里要高亮成橙色的词（原样出现在句子里）
HIGHLIGHT = ["Knock, knock!", "ghost", "Boo, boo, boo!", "black cat", "Meow, meow, meow!",
             "orange pumpkin", "Hello, pumpkin!", "Trick or treat!", "sweet"]

# 背景只画一次，5 个场景共用。可切换的部分（例如门开/门关）画成两个分组，场景里用 "hide" 隐藏不需要的那个
BACKGROUND = """- early-evening sky: smooth vertical gradient, lavender (#CDB8F5) at top to soft orange (#FFC98A) at the horizon, 2-3 soft white clouds
- soft green ground (#A8C686) with a few orange/red/yellow autumn leaves and tiny grass tufts
- a small one-story yellow cottage (#FFE27A walls) with a coral-orange roof (#E8774A), one round window left of the door,
  colorful round string lights along the roof edge, a wooden doorstep, two small pumpkins (smiling faces) on each side of the doorstep
- the door must be drawn TWICE, as two separate groups:
  <g id="door-closed">: the closed round-top blue wooden door (#5B9BE6) with plank lines and a small brass knob
  <g id="door-open">: the same door swung open (narrow panel hinged at the right edge of the doorway) showing a warm glowing
  yellow-orange interior (#FFD27F) inside the doorway
  Both groups are drawn at the same place; only one will be shown at a time."""

LAYOUT = {
    "16x9": """Canvas 1600x900 layout (use these exact coordinates):
- ground: from y=640 down to the bottom; characters stand with their feet around y=790-810
- cottage: front view, x=880..1560, walls y=330..700, a triangular gabled roof up to y=170
- door: x=1110..1330, round top at y=430, bottom at y=700; doorstep x=1080..1360, y=700..730
- free space for characters: x=150..1080 in front of the cottage, plus the doorway itself""",
    "3x4": """Canvas 1200x1600 (portrait 3:4) layout (use these exact coordinates):
- sky in the upper part; ground from y=1000 down to the bottom; characters stand with their feet around y=1340-1370
- keep y>1400 free of important content (only ground and a few leaves) - subtitles will go there
- cottage: front view, x=560..1140, walls y=640..1000, a triangular gabled roof up to y=470
- door: x=760..940, round top at y=730, bottom at y=1000; doorstep x=730..970, y=1000..1030
- free space for characters: x=60..1140 in front of the cottage (characters may overlap the bottom of the cottage), plus the doorway""",
}

LILY_SIZE = {"16x9": "about 480px tall, from y~320 to y~805", "3x4": "about 640px tall, from y~720 to y~1365"}

# camera：镜头关键帧 (时间%, 画面中心x, 画面中心y, 放大倍数)，放大倍数 1.0 = 全景；超出画布会自动收回
SCENES = [
    {
        "name": "01_knock",
        "line": "Knock, knock! Who is at the door?",
        "hide": ["door-open"],
        "action_16x9": "Lily stands at x~550 facing right toward the door, one hand cupped behind her ear as if listening, curious excited face, "
                       "the candy bucket in her other hand. Draw three short curved 'knock' motion lines near the door's right side (around x=1340, y=520). "
                       "Lily is the ONLY character in this picture: no cat, no ghost, no pumpkin character, no animals.",
        "action_3x4": "Lily stands at x~380 facing right toward the door, one hand cupped behind her ear as if listening, curious excited face, "
                      "the candy bucket in her other hand. Draw three short curved 'knock' motion lines near the door's right side (around x=965, y=830). "
                      "Lily is the ONLY character in this picture: no cat, no ghost, no pumpkin character, no animals.",
        "camera_16x9": [(0, 560, 500, 1.4), (100, 900, 520, 1.2)],     # 第一段从近景开始、立刻在动，不要从静止的全景开始
        "camera_3x4": [(0, 380, 1000, 1.4), (100, 650, 950, 1.25)],
        "motion": "Lily: gentle up-down bob (like breathing/excited bouncing) and a slight head-and-hat tilt toward the door as she listens. "
                  "Knock motion lines: blink in a knocking rhythm (knock-knock, pause, knock-knock) using opacity and a tiny scale pulse.",
    },
    {
        "name": "02_ghost",
        "line": "It's a little ghost. Boo, boo, boo!",
        "hide": ["door-closed"],
        "action_16x9": "A small fluffy white ghost with big round black eyes, pink cheeks and an open 'o' mouth floats in the doorway "
                       "(around x=1220, y=560). Lily laughs happily with one arm raised playfully toward the ghost. Funny, friendly, not scary.",
        "action_3x4": "A small fluffy white ghost with big round black eyes, pink cheeks and an open 'o' mouth floats in the doorway "
                      "(around x=850, y=860). Lily stands at x~380 and laughs happily with one arm raised playfully toward the ghost. Funny, friendly, not scary.",
        "camera_16x9": [(0, 650, 500, 1.3), (60, 950, 520, 1.2), (100, 950, 520, 1.25)],
        "camera_3x4": [(0, 450, 1000, 1.35), (100, 700, 950, 1.25)],
        "motion": "Ghost: pops in during the first 0.6s (scale from 0 to 1 with a little overshoot), then floats up and down and sways gently left-right. "
                  "Sparkles/puffs around the ghost twinkle. Lily: happy laughing bounce; her raised arm waves (rotate around the shoulder).",
    },
    {
        "name": "03_cat",
        "line": "It's a black cat. Meow, meow, meow!",
        "hide": ["door-closed"],
        "action_16x9": "A cute fluffy black cat with big green eyes, pink nose and a small orange bow sits on the ground at x~950, smiling, eyes closed happily. "
                       "Lily stands at x~650 leaning forward and gently pets the cat's head with one short arm (normal arm length), smiling warmly. "
                       "Candy bucket on the ground beside her feet.",
        "action_3x4": "A cute fluffy black cat (about 300px tall) with big green eyes, pink nose and a small orange bow sits on the ground at x~820 "
                      "(bottom at y~1360), smiling, eyes closed happily. Lily stands at x~430 leaning forward and gently pets the cat's head with one "
                      "short arm (normal arm length), smiling warmly. Candy bucket on the ground beside her feet.",
        "camera_16x9": [(0, 800, 450, 1.0), (100, 820, 580, 1.35)],
        "camera_3x4": [(0, 600, 800, 1.0), (100, 640, 1080, 1.3)],
        "motion": "Cat: tail wags (rotate around the tail base), head tilts happily into the petting, little hearts/sparkles/sound lines float up and fade. "
                  "Lily: the petting arm strokes back and forth gently (small rotation around the shoulder), body bobs softly.",
    },
    {
        "name": "04_pumpkin",
        "line": "It's a big orange pumpkin. Hello, pumpkin!",
        "hide": ["door-closed"],
        "action_16x9": "A huge round orange pumpkin character, as tall as Lily, with a friendly carved smiling face, rosy cheeks "
                       "and a green curly stem, stands on the ground at x~950. Lily waves hello with a big smile, holding the candy bucket in the other hand.",
        "action_3x4": "A huge round orange pumpkin character, almost as tall as Lily, with a friendly carved smiling face, rosy cheeks and a green "
                      "curly stem, stands on the ground at x~860 (bottom at y~1365). Lily stands at x~320 and waves hello with a big smile, "
                      "holding the candy bucket in the other hand.",
        "camera_16x9": [(0, 500, 520, 1.35), (100, 850, 520, 1.2)],
        "camera_3x4": [(0, 380, 1000, 1.35), (100, 650, 1050, 1.15)],
        "motion": "Pumpkin: bouncy wobble (squash-and-stretch with scaleY/scaleX around its bottom center) and, if it has arms, one arm waves. "
                  "Lily: her raised arm waves hello (rotate around the shoulder), small happy bounce; wave motion lines blink.",
    },
    {
        "name": "05_treat",
        "line": "Trick or treat! Here is a sweet for you!",
        "clip": 5.0,
        "hide": ["door-closed"],
        "action_16x9": "Lily stands in the CENTER, happily handing out colorful wrapped candies from her candy bucket. Around her: the tiny white ghost, "
                       "the fluffy black cat with orange bow, and the big smiling orange pumpkin, all joyful and receiving candies. A few colorful "
                       "wrapped candies float in the air. Place the group within x=200..1080.",
        "action_3x4": "Lily stands in the CENTER at x~600 (feet at y~1360), happily handing out colorful wrapped candies from her candy bucket. "
                      "The tiny white ghost floats on the left (around x=210, y=980); the fluffy black cat with orange bow sits on the right "
                      "(x~900, bottom at y~1365); the big smiling orange pumpkin (about 380px tall) stands behind the cat (x~1000, bottom at y~1300). "
                      "All joyful and receiving candies. A few colorful wrapped candies float in the air above them.",
        "camera_16x9": [(0, 650, 560, 1.45), (100, 800, 450, 1.0)],
        "camera_3x4": [(0, 600, 1050, 1.4), (100, 600, 800, 1.0)],
        "motion": "Floating candies drift up and down and rotate slightly, each with a different delay. Ghost floats up and down. "
                  "Cat and pumpkin bounce happily with different delays. Lily: gentle bounce, the arm giving candy moves slightly. Sparkles twinkle.",
    },
]

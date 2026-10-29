"""每期一个 story.py：放在项目文件夹里，所有脚本都读它。模板 = 动物系列第 1 期（农场动物）的完整配置。

做新一期时复制一份再改：
- TITLE / HIGHLIGHT / CLIP / TEASER / MUSIC：标题、高亮词、节奏和开头钩子
- CAST：本期配角的外形描述（出设定图 → 用户定稿后才能进镜头）
- BACKGROUND / LAYOUT：场景和坐标
- SCENES：每句一个字典：line、cast（出场配角）、lily_16x9 / lily_3x4（Lily 的位置、动作、表情，由 character.js 绘制）、
  action_16x9 / action_3x4（配角怎么摆、怎么和 Lily 互动）、camera、motion（配角动作）
Lily 的可用动作见 assets/character.js 开头的说明。
"""

TITLE = "农场动物"

# 节奏和开头钩子（针对“前 2 秒大量划走”）：每段 4 秒；先放 2 秒预告（最后一幕从近景拉开 + 一句问句 + 上方大字）
CLIP = 4.0
TEASER = {"line": "Who says moo?", "hook": "Who says moo? 🐮"}
MUSIC = "playful"


HIGHLIGHT = ["moo", "baa", "oink", "quack", "Moo", "cow", "sheep", "pig", "duck", "farm friends"]

BACKGROUND = """- bright sunny morning sky: smooth vertical gradient from light sky blue (#BFE3F7) at top to pale cream (#FFF4D6) at the horizon,
  2-3 soft white clouds and a small friendly sun with short rays in a top corner
- soft green meadow (#A8D68A) with a few tiny white and yellow flowers and small grass tufts
- a cute red barn (#E05A47 walls, white trim, darker red-brown roof #9E3B2F) with big closed double doors marked with a white X
  and a small round hay window under the roof peak
- a light-brown wooden fence along the horizon, a round yellow haystack, and a small light-blue pond (#9FD8F0) with two green lily pads
- no animals and no people"""

LAYOUT = {
    "16x9": """Canvas 1600x900 layout (use these exact coordinates):
- sky above y=600; meadow from y=600 down to the bottom; characters stand with their feet around y=790-810
- red barn: front view, x=1120..1540, walls y=320..640, roof up to y=180; double doors x=1250..1410, y=470..640
- wooden fence along the horizon: x=0..1100, y=560..640 (behind the characters)
- haystack: x=50..230, y=540..650
- pond: ellipse centered at (1330, 735), rx=150, ry=40, in front of the barn
- free space for characters: x=200..1250 on the meadow""",
    "3x4": """Canvas 1200x1600 (portrait 3:4) layout (use these exact coordinates):
- sky in the upper part; meadow from y=950 down to the bottom; characters stand with their feet around y=1340-1370
- keep y>1400 free of important content (only grass and a few flowers) - subtitles will go there
- red barn: front view, x=640..1140, walls y=620..960, roof up to y=470; double doors x=800..980, y=800..960
- wooden fence along the horizon: x=0..640, y=890..960
- haystack: x=40..200, y=870..970
- pond: ellipse centered at (920, 1040), rx=170, ry=40, in front of the barn
- free space for characters: x=60..1140 on the meadow (characters may overlap the bottom of the barn and the pond)""",
}

# Lily 由 character.js 绘制：每个场景的 lily_16x9 / lily_3x4 写她的位置（脚底中心）、动作和表情。

# 本期配角：外形描述要具体到颜色、花纹、配件和姿态。先出设定图，用户确认定稿后，场景才会拿它当参考来画。
CAST = {
    "cow": "A friendly cartoon dairy cow. Body: white rounded-rectangle body with exactly 3 big BLACK irregular patches "
           "(one on the back, one on the side, one on the rump) plus a black patch around its LEFT ear. Head: white, big round black eyes "
           "with white highlights, a wide PINK muzzle (#F7A8B8) with two dark nostrils, two short cream-colored horns (#F3E3B5) curving "
           "slightly upward, floppy white ears with pink insides. Accessory: a RED collar (#E05A47) with a small golden bell (#FFD24A). "
           "Four short sturdy white legs with BLACK hooves, a thin tail ending in a black tuft. No udder. Always stands on four legs.",
    "sheep": "A fluffy cartoon sheep. Body: a big round cloud of WHITE wool made of overlapping round puffs (scalloped outline). "
             "Head: soft medium-GREY face (#A9A9A9) and grey oval ears that stick out sideways, small black eyes with white highlights, "
             "pink cheeks, a small curly white wool tuft on top of the head. Four short DARK-GREY legs (#5E5E5E) with black hooves. "
             "Always stands on four legs.",
    "pig": "A chubby cartoon piglet. Body: round pink body (#F7A8B8) with a lighter pink belly, a short corkscrew curly tail. "
           "Head: big round pink head, a large oval darker-pink snout (#F08CA3) with two nostrils, small black eyes with highlights, "
           "rosy cheeks, two small upright rounded triangular ears. Four short pink legs with darker pink hooves. "
           "Always stands on four legs, no arms.",
    "duck": "A cute cartoon white duck. Body: plump white pear-shaped body (narrower at the top, wider at the bottom) flowing into the head, small white wings folded "
            "against the body (no colored wing patches), a short pointed tail feather tuft. Face: small black eyes with highlights, "
            "pink cheek, a flat bright ORANGE duck bill (#FF9A1F) that sticks out forward like a beak (not a mouth drawn on the face). "
            "Two short thick legs filled ORANGE (#FF9A1F) with orange webbed feet - the legs are orange, never white. Stands on two legs.",
}


SCENES = [
    {
        "name": "01_cow",
        "lily_16x9": {"action": "call", "expression": "happy", "x": 550, "y": 800},
        "lily_3x4": {"action": "call", "expression": "happy", "x": 350, "y": 1365},
        "cast": ["cow"],
        "line": "Who says moo? The cow says moo!",
        "hide": [],
        "action_16x9": "A friendly black-and-white spotted cow (pink nose, two small horns, a little golden bell on a collar), about 380px tall, "
                       "stands on the meadow at x~1000 facing Lily, mouth open saying 'moo', with three short curved sound lines near its mouth. "
                       "Lily stands at x~550 facing the cow, one hand cupped beside her mouth as if mooing back, big smile. "
                       "Only Lily and the cow in this picture: no other animals.",
        "action_3x4": "A friendly black-and-white spotted cow (pink nose, two small horns, a little golden bell on a collar), about 460px tall, "
                      "stands on the meadow at x~860 (bottom at y~1365) facing Lily, mouth open saying 'moo', with three short curved sound "
                      "lines near its mouth. Lily stands at x~350 facing the cow, one hand cupped beside her mouth as if mooing back, big smile. "
                      "Only Lily and the cow in this picture: no other animals.",
        "camera_16x9": [(0, 560, 500, 1.4), (100, 820, 540, 1.15)],
        "camera_3x4": [(0, 380, 1000, 1.4), (100, 620, 1000, 1.2)],
        "motion": "Cow: head nods up and down as it moos, the bell on its collar swings, tail swishes (rotate around the tail base). "
                  "Sound lines near its mouth pulse (opacity + small scale). Lily: happy bounce, the hand at her mouth moves slightly.",
    },
    {
        "name": "02_sheep",
        "lily_16x9": {"action": "pat", "expression": "happy", "x": 640, "y": 800},
        "lily_3x4": {"action": "pat", "expression": "happy", "x": 420, "y": 1365},
        "cast": ["sheep"],
        "line": "Who says baa? The sheep says baa!",
        "hide": [],
        "action_16x9": "A round fluffy white sheep with cloud-like curly wool, a soft grey face, small ears and short dark legs, about 320px tall, "
                       "stands on the meadow at x~1000 saying 'baa', with short curved sound lines near its mouth. Lily stands at x~640 "
                       "leaning forward and gently patting the fluffy wool with one hand (normal arm length), smiling warmly. "
                       "Only Lily and the sheep in this picture: no other animals.",
        "action_3x4": "A round fluffy white sheep with cloud-like curly wool, a soft grey face, small ears and short dark legs, about 400px tall, "
                      "stands on the meadow at x~860 (bottom at y~1365) saying 'baa', with short curved sound lines near its mouth. Lily stands "
                      "at x~420 leaning forward and gently patting the fluffy wool with one hand (normal arm length), smiling warmly. "
                      "Only Lily and the sheep in this picture: no other animals.",
        "camera_16x9": [(0, 1000, 540, 1.35), (100, 780, 520, 1.2)],
        "camera_3x4": [(0, 850, 1050, 1.35), (100, 600, 1000, 1.2)],
        "motion": "Sheep: fluffy body does a soft squash-and-stretch bounce around its bottom center, ears flick, sound lines pulse. "
                  "Lily: the patting arm moves gently up and down (small rotation around the shoulder), body bobs softly.",
    },
    {
        "name": "03_pig",
        "lily_16x9": {"action": "nose", "expression": "happy", "x": 580, "y": 800},
        "lily_3x4": {"action": "nose", "expression": "happy", "x": 360, "y": 1365},
        "cast": ["pig"],
        "line": "Who says oink? The pig says oink!",
        "hide": [],
        "action_16x9": "A chubby round pink pig (#F7A8B8) with a big round snout, floppy ears and a curly tail, about 300px tall, stands on "
                       "the meadow at x~1000 saying 'oink', happy face, short sound lines near its snout. Lily stands at x~580 giggling, "
                       "pushing the tip of her own nose up with one finger like a pig snout. "
                       "Only Lily and the pig in this picture: no other animals.",
        "action_3x4": "A chubby round pink pig (#F7A8B8) with a big round snout, floppy ears and a curly tail, about 380px tall, stands on "
                      "the meadow at x~860 (bottom at y~1365) saying 'oink', happy face, short sound lines near its snout. Lily stands at "
                      "x~360 giggling, pushing the tip of her own nose up with one finger like a pig snout. "
                      "Only Lily and the pig in this picture: no other animals.",
        "camera_16x9": [(0, 800, 450, 1.0), (100, 790, 560, 1.3)],
        "camera_3x4": [(0, 600, 800, 1.0), (100, 600, 1080, 1.3)],
        "motion": "Pig: curly tail wiggles quickly (rotate around the tail base), snout twitches (tiny scale pulse), floppy ears flap, "
                  "small happy hop. Sound lines pulse. Lily: giggling bounce with a slight head tilt.",
    },
    {
        "name": "04_duck",
        "lily_16x9": {"action": "flap", "expression": "surprised", "x": 560, "y": 800},
        "lily_3x4": {"action": "flap", "expression": "surprised", "x": 340, "y": 1365},
        "cast": ["duck"],
        "line": "Who says quack? The duck says quack!",
        "hide": [],
        "action_16x9": "A white duck with a bright orange beak and orange webbed feet, about 240px tall, stands on the meadow at x~1020 "
                       "next to the pond, wings spread wide, beak open saying 'quack', short sound lines near its beak. Lily stands at "
                       "x~560 flapping both arms out to the sides like wings, laughing. "
                       "Only Lily and the duck in this picture: no other animals.",
        "action_3x4": "A white duck with a bright orange beak and orange webbed feet, about 300px tall, stands on the meadow at x~880 "
                      "(bottom at y~1365), wings spread wide, beak open saying 'quack', short sound lines near its beak. Lily stands at "
                      "x~340 flapping both arms out to the sides like wings, laughing. "
                      "Only Lily and the duck in this picture: no other animals.",
        "camera_16x9": [(0, 600, 520, 1.35), (100, 850, 540, 1.2)],
        "camera_3x4": [(0, 380, 1000, 1.35), (100, 650, 1050, 1.15)],
        "motion": "Duck: wings flap (rotate each wing around its shoulder), body waddles side to side (small rotation around the feet), "
                  "beak opens and closes (tiny rotation). Lily: both arms flap up and down like wings (rotate around the shoulders), small hops.",
    },
    {
        "name": "05_friends",
        "lily_16x9": {"action": "cheer", "expression": "happy", "x": 650, "y": 800},
        "lily_3x4": {"action": "cheer", "expression": "happy", "x": 600, "y": 1365, "scale": 1.9},
        "cast": ["cow", "sheep", "pig", "duck"],
        "line": "Hello, farm friends! Moo, baa, oink, quack!",
        "clip": 6.0,                      # 4 个拟声词要 5 秒多，这一段加长
        "hide": [],
        "action_16x9": "A happy group on the meadow: Lily in the CENTER at x~650 waving both arms high. Around her, all smaller than Lily and "
                       "not overlapping her: the spotted cow on the far left (x~250, about 330px tall), the fluffy white sheep at x~440 "
                       "(about 260px tall), the pink pig at x~870 (about 240px tall), and the white duck at x~1040 (about 200px tall). "
                       "Everyone is smiling and looking at the viewer; a few little colorful music notes and sparkles float above them.",
        "action_3x4": "A happy group on the meadow: Lily in the CENTER at x~600 (about 560px tall, feet at y~1365) waving both arms high. "
                      "Around her, not overlapping her face or body: the spotted cow on the left (x~190, bottom at y~1300, about 360px tall), "
                      "the fluffy white sheep on the right (x~1000, bottom at y~1300, about 300px tall), the pink pig in front on the left "
                      "(x~330, bottom at y~1390, about 220px tall) and the white duck in front on the right (x~860, bottom at y~1390, about "
                      "200px tall). Everyone is smiling; a few little colorful music notes and sparkles float above them.",
        "camera_16x9": [(0, 650, 560, 1.45), (100, 800, 450, 1.0)],
        "camera_3x4": [(0, 600, 1050, 1.4), (100, 600, 800, 1.0)],
        "motion": "Everyone bounces happily with different delays. Lily waves both arms (rotate around the shoulders). Cow tail swishes, "
                  "sheep squashes softly, pig tail wiggles, duck wings flap. Music notes and sparkles float up and down and twinkle.",
    },
]

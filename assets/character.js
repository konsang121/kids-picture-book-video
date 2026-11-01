/**
 * character.js — MV 主角 Lily（紫色星星裙小女孩）的唯一绘制模块。
 * 造型已定稿 v1.0（2026-10-29，以 角色设定图.png 为准）。之后只加新表情/动作/道具，不改已有造型参数。
 * v1.1（2026-10-29）：新增绘本用的手势动作 wave/cheer/flap/pat/call/nose，新增 filter:false 选项和 Lily.points()。
 * v1.2（2026-10-29）：新增摸五官动作 touchNose/touchEars/touchEyes/touchMouth/touchAll（正面用），眨眼和亲亲嘴型只在这些动作里出现。
 * v1.3（2026-10-30）：新增服装 hat:"witch"（紫色巫师帽）、左手提的 carry:"pumpkinBucket"（南瓜糖果桶）、敲门动作 knock。
 * v1.4（2026-10-31）：新增好习惯动作 brushTeeth/washFace/scrubHands/combHair（正面用），牙刷、梳子、泡沫、水珠、肥皂泡由动作自带。
 * 这份（skill 的 assets/character.js）是唯一的主版本，绘本和 MV 都从这里取。
 *
 * 所有镜头都通过这里画角色，不要在镜头里重新画她，这样造型从头到尾一致。
 * 画风与绘本系列相同：圆润造型、深棕粗描边、明亮平涂，外面再套 crayonDefs() 里的蜡笔滤镜。
 *
 * 用法（浏览器 <script src="character.js"> 后用全局 Lily；Node 里 require("./character.js")）：
 *
 *   Lily.draw({
 *     view: "front",        // 朝向："front" 正面 | "side" 侧面 | "back" 背面
 *     facing: "right",      // 侧面朝哪边："right" | "left"
 *     expression: "happy",  // 表情："happy" 开心 | "shy" 害羞 | "sad" 难过 | "surprised" 惊讶
 *     action: "stand",      // 动作："stand" 站 | "walk" 走 | "jump" 跳 | "hug" 拥抱 | "hold" 手持道具
 *                           //       "wave" 挥手 | "cheer" 双手举高欢呼 | "flap" 双臂扇动 | "pat" 伸手抚摸（右手伸向画面右侧）
 *                           //       "call" 手放嘴边喊 | "nose" 手指推鼻头（学小猪）
 *                           //       （以下正面用）"touchNose" 点自己鼻子 | "touchEars" 双手摸耳朵 | "touchEyes" 双手指眼睛并眨眼
 *                           //       "touchMouth" 手放嘴边飞吻 | "touchAll" 依次摸鼻子→耳朵→眼睛→嘴巴→欢呼（t 走完一轮）
 *                           //       "knock" 右手在头旁边向画面右侧敲门（咚咚、停一下）
 *                           //       （以下正面用，道具和泡泡自带）"brushTeeth" 右手拿牙刷左右刷牙，嘴边有泡沫
 *                           //       "washFace" 闭眼双手捧在脸颊上画圈洗脸，手边溅出水珠 | "scrubHands" 双手在胸前搓，冒肥皂泡
 *                           //       "combHair" 右手拿梳子从上往下梳右边的头发
 *     hat: null,            // 服装帽子："witch" 紫色巫师帽（正面/侧面/背面都有）
 *     carry: null,          // 左手提着的东西（和右手道具 prop 分开）："pumpkinBucket" 南瓜糖果桶
 *                           //   左手要垂下来才提得住：不要和 cheer/flap/jump/hug/touch* 一起用
 *     prop: null,           // 道具（action 为 hold 或 hug 时）："balloon" | "flower" | "lollipop" | "book" | "teddy"
 *     t: 0,                 // 动作进度 0~1（走路一个循环、跳跃一次起落），做动画时逐帧递增
 *     x: 0, y: 0,           // 脚底中心在画面里的位置
 *     scale: 1,             // 1 = 身高约 300px
 *     filter: true,         // false = 不套自带的蜡笔滤镜（外层已经有蜡笔滤镜时用）
 *   })  // → 返回一段 SVG <g> 字符串，直接拼进镜头的 <svg> 里
 *
 *   Lily.crayonDefs()  // → <filter id="lily-crayon"> 等定义，放进镜头 <svg><defs> 里一次
 *   Lily.svg(opts, { width, height })  // → 单独一张完整 SVG（预览、导出用）
 *   Lily.points(opts)  // → 画面坐标里的 { handL, handR, head, top, left, right, bottom }，用来给其他角色定位
 *
 * 规则（模块内部保证）：
 * - 道具挂在手的位置上，先画道具再画手和拇指，看起来是“握着”，不会和手分开
 * - 道具的包围盒如果碰到脸，会自动向外侧移开（气球线、花茎会跟着变长、变斜，仍然连在手上）
 */
(function (root) {
  "use strict";

  // ---------------- 固定造型参数（改这里会影响所有镜头） ----------------
  const C = {
    line: "#4A3B33", skin: "#FFD9B8", cheek: "#FF9AA2", hair: "#5A3A22", bow: "#FF8C1A",
    dress: "#C9A7F2", dressShade: "#B08FE6", star: "#FFD93D", tightO: "#FF8C1A", tightW: "#FFFFFF",
    shoe: "#2B2B2B", eye: "#2B1D14", tear: "#8FD3FF", mouth: "#C2475A", white: "#FFFFFF",
  };
  const LW = 5;                                  // 描边粗细
  const HEAD = { x: 0, y: -232, r: 56 };         // 头（脚底为原点，向上为负）
  const SHOULDER = { x: 34, y: -160 };           // 正面肩点（右侧，左侧取负）
  const HIP = { x: 19, y: -88 };                 // 正面胯点
  const UPPER = 38, FORE = 34, LEG = 70;         // 上臂、前臂、腿长
  const FACE_BOX = { front: [-60, -292, 60, -172], side: [-6, -292, 66, -174], back: null };

  const VIEWS = ["front", "side", "back"];
  const EXPRESSIONS = ["happy", "shy", "sad", "surprised"];
  const ACTIONS = ["stand", "walk", "jump", "hug", "hold", "wave", "cheer", "flap", "pat", "call", "nose",
                   "touchNose", "touchEars", "touchEyes", "touchMouth", "touchAll", "knock",
                   "brushTeeth", "washFace", "scrubHands", "combHair", "washHair", "popBubble", "shh"];
  const GROOM = ["brushTeeth", "washFace", "scrubHands", "combHair", "washHair", "popBubble", "shh"];
  const HATS = ["witch"];
  const CARRY = ["pumpkinBucket"];
  const PROPS = ["balloon", "flower", "lollipop", "book", "teddy"];

  // ---------------- 小工具 ----------------
  const f = (n) => (Math.round(n * 10) / 10).toString();
  const pt = (p) => `${f(p.x)},${f(p.y)}`;
  const stroke = (w = LW) => `stroke="${C.line}" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round"`;

  function star(cx, cy, r, fill = C.star) {
    let d = "";
    for (let i = 0; i < 10; i++) {
      const a = -Math.PI / 2 + (i * Math.PI) / 5, rr = i % 2 ? r * 0.45 : r;
      d += `${i ? "L" : "M"}${f(cx + rr * Math.cos(a))},${f(cy + rr * Math.sin(a))}`;
    }
    return `<path d="${d}Z" fill="${fill}" ${stroke(2)}/>`;
  }

  /** 两段式手臂/腿的正向运动学。dir: 1 = 向画面右/前，-1 = 向左/后。角度从“竖直向下”量起。 */
  function limb(start, a1, a2, l1, l2, dir) {
    const elbow = { x: start.x + dir * Math.sin(a1) * l1, y: start.y + Math.cos(a1) * l1 };
    const end = { x: elbow.x + dir * Math.sin(a1 + a2) * l2, y: elbow.y + Math.cos(a1 + a2) * l2 };
    return { start, elbow, end };
  }

  /** 两段式手臂的反向运动学：让手落到 target，手肘朝下弯。 */
  function ik(start, target, l1, l2) {
    const dx = target.x - start.x, dy = target.y - start.y;
    const d = Math.min(Math.max(Math.hypot(dx, dy), Math.abs(l1 - l2) + 0.01), l1 + l2 - 0.01);
    const ux = dx / (Math.hypot(dx, dy) || 1), uy = dy / (Math.hypot(dx, dy) || 1);
    const a = (l1 * l1 - l2 * l2 + d * d) / (2 * d), h = Math.sqrt(Math.max(l1 * l1 - a * a, 0));
    const px = start.x + a * ux, py = start.y + a * uy;
    const e1 = { x: px - h * uy, y: py + h * ux }, e2 = { x: px + h * uy, y: py - h * ux };
    const elbow = e1.y >= e2.y ? e1 : e2;
    return { start, elbow, end: { x: start.x + d * ux, y: start.y + d * uy } };
  }

  function armPath(arm, dim = false) {
    const d = `M${pt(arm.start)} L${pt(arm.elbow)} L${pt(arm.end)}`;
    const skin = dim ? "#F2C7A3" : C.skin;
    return `<path d="${d}" fill="none" stroke="${C.line}" stroke-width="19" stroke-linecap="round" stroke-linejoin="round"/>` +
           `<path d="${d}" fill="none" stroke="${skin}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>`;
  }

  function hand(p, gripping, dim = false) {
    const skin = dim ? "#F2C7A3" : C.skin;
    let s = `<circle cx="${f(p.x)}" cy="${f(p.y)}" r="10" fill="${skin}" ${stroke(4)}/>`;
    if (gripping) s += `<path d="M${f(p.x - 7)},${f(p.y - 2)} Q${f(p.x)},${f(p.y - 9)} ${f(p.x + 7)},${f(p.y - 2)}" fill="none" ${stroke(3)}/>`;
    return s;
  }

  function legPath(hip, ankle, dim = false) {
    const d = `M${pt(hip)} L${pt(ankle)}`;
    return `<path d="${d}" stroke="${C.line}" stroke-width="23" stroke-linecap="round"/>` +
           `<path d="${d}" stroke="${C.tightW}" stroke-width="14" stroke-linecap="butt"/>` +
           `<path d="${d}" stroke="${C.tightO}" stroke-width="14" stroke-dasharray="8 8" stroke-linecap="butt" opacity="${dim ? 0.8 : 1}"/>`;
  }

  /** 侧面的腿：胯 → 膝 → 脚踝，带条纹袜和朝前的鞋。 */
  function bentLeg(hip, leg) {
    const d = `M${pt(hip)} L${pt(leg.elbow)} L${pt(leg.end)}`;
    return `<path d="${d}" fill="none" stroke="${C.line}" stroke-width="23" stroke-linecap="round" stroke-linejoin="round"/>` +
           `<path d="${d}" fill="none" stroke="${C.tightW}" stroke-width="14" stroke-linejoin="round"/>` +
           `<path d="${d}" fill="none" stroke="${C.tightO}" stroke-width="14" stroke-dasharray="8 8" stroke-linejoin="round"/>` +
           shoe(leg.end, 8);
  }

  function shoe(p, forward = 0) {
    return `<ellipse cx="${f(p.x + forward)}" cy="${f(p.y + 8)}" rx="${forward ? 21 : 17}" ry="11" fill="${C.shoe}" ${stroke(4)}/>`;
  }

  function bow(x, y, s = 1) {
    return `<g transform="translate(${f(x)},${f(y)}) scale(${s})">` +
      `<path d="M0,0 L-15,-10 L-15,10 Z M0,0 L15,-10 L15,10 Z" fill="${C.bow}" ${stroke(3)}/>` +
      `<circle r="5" fill="${C.bow}" ${stroke(3)}/></g>`;
  }

  // ---------------- 表情（脸部坐标：头中心为原点） ----------------
  function eyes(expr, xs, y, side, closed) {
    let s = "";
    for (const x of xs) {
      const inner = side ? 1 : -Math.sign(x);   // 眉毛内侧的方向
      if (closed || expr === "shy") {
        s += `<path d="M${x - 9},${y - 1} Q${x},${y + 7} ${x + 9},${y - 1}" fill="none" stroke="${C.eye}" stroke-width="4" stroke-linecap="round"/>`;
      } else {
        const r = expr === "surprised" ? 10.5 : expr === "sad" ? 8 : 9.5;
        s += `<circle cx="${x}" cy="${y}" r="${r}" fill="${C.eye}"/><circle cx="${x + 3}" cy="${y - 3.5}" r="3.2" fill="${C.white}"/>` +
             `<circle cx="${x - 3}" cy="${y + 3.5}" r="1.4" fill="${C.white}"/>`;
      }
      if (expr === "sad") {
        s += `<path d="M${x - inner * 10},${y - 13} L${x + inner * 9},${y - 19}" ${stroke(3.5)}/>`;   // 内侧上扬的八字眉
      } else if (expr === "surprised") {
        s += `<path d="M${x - 9},${y - 18} Q${x},${y - 25} ${x + 9},${y - 18}" fill="none" ${stroke(3.5)}/>`;
      }
    }
    return s;
  }

  function cheeks(expr, xs, y) {
    let s = "";
    for (const x of xs) {
      const r = expr === "shy" ? 12 : 9;
      s += `<ellipse cx="${x}" cy="${y}" rx="${r}" ry="${r * 0.7}" fill="${C.cheek}" opacity="${expr === "shy" ? 0.95 : 0.75}"/>`;
      if (expr === "shy") for (let k = -1; k <= 1; k++) s += `<path d="M${x + k * 6 - 2},${y - 3} l4,-5" stroke="#E0607A" stroke-width="2" stroke-linecap="round"/>`;
    }
    return s;
  }

  function mouth(expr, x, y, pucker) {
    if (pucker) return `<path d="M${x - 2},${y - 8} q8,4 0,8 q8,4 0,8" fill="none" stroke="${C.mouth}" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>`;
    switch (expr) {
      case "shy": return `<path d="M${x - 7},${y} q3.5,-3 7,0 q3.5,3 7,0" fill="none" ${stroke(3)}/>`;
      case "sad": return `<path d="M${x - 10},${y + 4} Q${x},${y - 5} ${x + 10},${y + 4}" fill="none" ${stroke(3.5)}/>`;
      case "surprised": return `<ellipse cx="${x}" cy="${y + 1}" rx="6.5" ry="8.5" fill="${C.mouth}" ${stroke(3)}/>`;
      default: return `<path d="M${x - 12},${y - 3} Q${x},${y + 12} ${x + 12},${y - 3} Q${x},${y + 3} ${x - 12},${y - 3}Z" fill="${C.mouth}" ${stroke(3)}/>`;
    }
  }

  /** 刷牙泡沫：嘴角两边几个小白泡。 */
  function foam() {
    return [[-17, 38, 5], [-22, 44, 3.5], [17, 41, 4.5], [22, 35, 3.5]]
      .map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}" fill="#FFFFFF" stroke="#8FD3FF" stroke-width="1.8"/>`).join("");
  }

  function tear(x, y) {
    return `<path d="M${x},${y} q-6,9 0,12 q6,-3 0,-12z" fill="${C.tear}" ${stroke(2)}/>`;
  }

  // ---------------- 头部 ----------------
  function headFront(expr, face = {}) {
    const r = HEAD.r;
    return `<ellipse cx="0" cy="-4" rx="${r + 10}" ry="${r + 9}" fill="${C.hair}" ${stroke()}/>` +
      `<circle cx="-70" cy="16" r="33" fill="${C.hair}" ${stroke()}/><circle cx="70" cy="16" r="33" fill="${C.hair}" ${stroke()}/>` +
      `<circle cx="0" cy="8" r="${r}" fill="${C.skin}" ${stroke()}/>` +
      `<path d="M-57,2 Q-52,-52 0,-58 Q52,-52 57,2 Q44,-18 24,-12 Q12,-28 0,-16 Q-12,-28 -24,-12 Q-44,-18 -57,2Z" fill="${C.hair}" ${stroke()}/>` +
      bow(-58, -12) + bow(58, -12) +
      eyes(expr, [-21, 21], 10, false, face.closed) + cheeks(expr, [-35, 35], 28) + mouth(expr, 0, 36, face.pucker) +
      (face.foam ? foam() : "") + (expr === "sad" ? tear(-31, 22) : "");
  }

  function headSide(expr) {
    const r = HEAD.r;
    return `<circle cx="-62" cy="18" r="31" fill="${C.hair}" ${stroke()}/>` +
      `<circle cx="6" cy="8" r="${r}" fill="${C.skin}" ${stroke()}/>` +
      `<path d="M58,0 Q62,10 60,18" fill="none" ${stroke(3)}/>` +                                   // 鼻尖
      `<path d="M44,-24 Q22,-62 -26,-52 Q-66,-30 -50,30 Q-38,40 -26,24 Q-22,-6 -2,-14 Q20,-28 44,-24Z" fill="${C.hair}" ${stroke()}/>` +
      bow(-48, -6, 0.95) +
      eyes(expr, [32], 8, true) + cheeks(expr, [30], 28) + mouth(expr, 44, 36) +
      (expr === "sad" ? tear(26, 20) : "");
  }

  function headBack() {
    const r = HEAD.r;
    return `<circle cx="-70" cy="16" r="33" fill="${C.hair}" ${stroke()}/><circle cx="70" cy="16" r="33" fill="${C.hair}" ${stroke()}/>` +
      `<ellipse cx="0" cy="0" rx="${r + 10}" ry="${r + 12}" fill="${C.hair}" ${stroke()}/>` +
      `<path d="M0,-66 L0,-10" ${stroke(3)} opacity="0.6"/>` +
      `<path d="M-30,30 Q-15,40 0,34 Q15,40 30,30" fill="none" ${stroke(3)} opacity="0.5"/>` +
      bow(-50, -14) + bow(50, -14);
  }

  // ---------------- 裙子 ----------------
  function dressFront(back = false) {
    let s = `<rect x="-9" y="-182" width="18" height="16" fill="${C.skin}" ${stroke(4)}/>` +
      `<path d="M-34,-174 Q0,-182 34,-174 L64,-90 Q0,-78 -64,-90 Z" fill="${C.dress}" ${stroke()}/>` +
      `<path d="M-56,-98 Q0,-88 56,-98" fill="none" stroke="${C.dressShade}" stroke-width="4" stroke-linecap="round"/>`;
    const stars = back ? [[-26, -140], [22, -120], [-12, -104], [36, -100]] : [[-20, -146], [18, -136], [-34, -112], [6, -110], [38, -104]];
    for (const [x, y] of stars) s += star(x, y, 7);
    return s;
  }

  function dressSide() {
    let s = `<rect x="-8" y="-182" width="16" height="16" fill="${C.skin}" ${stroke(4)}/>` +
      `<path d="M-24,-174 Q2,-182 26,-174 L48,-90 Q2,-80 -42,-90 Z" fill="${C.dress}" ${stroke()}/>` +
      `<path d="M-36,-98 Q4,-90 42,-98" fill="none" stroke="${C.dressShade}" stroke-width="4" stroke-linecap="round"/>`;
    for (const [x, y] of [[-6, -144], [14, -120], [-18, -110], [28, -102]]) s += star(x, y, 7);
    return s;
  }

  const sleeve = (x, y) => `<ellipse cx="${f(x)}" cy="${f(y)}" rx="18" ry="15" fill="${C.dress}" ${stroke()}/>`;

  // ---------------- 道具（以手为锚点） ----------------
  /** 道具的“头部”相对手的偏移（花、棒棒糖、气球）；会被 clearFace 推离脸部。 */
  const PROP_OFFSET = { balloon: { x: 58, y: -196, r: 40 }, flower: { x: 14, y: -44, r: 17 }, lollipop: { x: 12, y: -44, r: 17 } };

  function clearFace(view, hp, prop) {
    const box = FACE_BOX[view];
    const o = { ...PROP_OFFSET[prop] };
    if (!box) return o;
    const dir = view === "side" ? 1 : Math.sign(hp.x) || 1;   // 向身体外侧（侧面是向前）推
    for (let i = 0; i < 40; i++) {
      const cx = hp.x + o.x * dir, cy = hp.y + o.y;
      const hit = cx + o.r > box[0] && cx - o.r < box[2] && cy + o.r > box[1] && cy - o.r < box[3];
      if (!hit) break;
      o.x += 4; o.y += i % 2 ? 2 : 0;
    }
    return o;
  }

  function drawProp(prop, hp, view) {
    if (!prop) return "";
    const dir = view === "side" ? 1 : Math.sign(hp.x) || 1;
    if (prop === "book") {
      const w = 46, h = 58, x = dir > 0 ? hp.x - 8 : hp.x - w + 8, y = hp.y - h + 10;
      return `<rect x="${f(x)}" y="${f(y)}" width="${w}" height="${h}" rx="5" fill="#5B9BE6" ${stroke(4)}/>` +
        `<rect x="${f(x + 6)}" y="${f(y + 6)}" width="${w - 12}" height="${h - 12}" rx="3" fill="none" stroke="#FFFFFF" stroke-width="2.5" opacity="0.7"/>` +
        star(x + w / 2, y + h / 2 - 2, 9);
    }
    if (prop === "teddy") {
      const x = hp.x, y = hp.y + 6;
      return `<circle cx="${f(x - 15)}" cy="${f(y - 30)}" r="9" fill="#C58B5A" ${stroke(3)}/><circle cx="${f(x + 15)}" cy="${f(y - 30)}" r="9" fill="#C58B5A" ${stroke(3)}/>` +
        `<ellipse cx="${f(x)}" cy="${f(y + 6)}" rx="22" ry="20" fill="#C58B5A" ${stroke(4)}/>` +
        `<circle cx="${f(x)}" cy="${f(y - 18)}" r="18" fill="#C58B5A" ${stroke(4)}/>` +
        `<ellipse cx="${f(x)}" cy="${f(y - 12)}" rx="8" ry="6" fill="#F3D3B0"/><circle cx="${f(x - 6)}" cy="${f(y - 21)}" r="2.5" fill="${C.eye}"/>` +
        `<circle cx="${f(x + 6)}" cy="${f(y - 21)}" r="2.5" fill="${C.eye}"/><circle cx="${f(x)}" cy="${f(y - 14)}" r="2.5" fill="${C.eye}"/>`;
    }
    const o = clearFace(view, hp, prop);
    const hx = hp.x, hy = hp.y, px = hx + dir * o.x, py = hy + o.y;
    if (prop === "balloon") {
      return `<path d="M${f(hx)},${f(hy)} C${f(hx + dir * 10)},${f(hy - 60)} ${f(px - dir * 20)},${f(py + 90)} ${f(px)},${f(py + 42)}" fill="none" ${stroke(2.5)}/>` +
        `<path d="M${f(px - 6)},${f(py + 46)} L${f(px + 6)},${f(py + 46)} L${f(px)},${f(py + 38)}Z" fill="#FF6F91" ${stroke(2.5)}/>` +
        `<ellipse cx="${f(px)}" cy="${f(py)}" rx="34" ry="40" fill="#FF6F91" ${stroke(4)}/>` +
        `<ellipse cx="${f(px - 12)}" cy="${f(py - 16)}" rx="7" ry="11" fill="#FFFFFF" opacity="0.6"/>`;
    }
    if (prop === "flower") {
      let s = `<path d="M${f(hx)},${f(hy + 6)} Q${f(hx + dir * 2)},${f((hy + py) / 2)} ${f(px)},${f(py)}" fill="none" stroke="#5DAE4A" stroke-width="5" stroke-linecap="round"/>` +
        `<path d="M${f((hx + px) / 2)},${f((hy + py) / 2 + 4)} q${f(dir * 12)},-8 ${f(dir * 16)},-2 q${f(-dir * 6)},8 ${f(-dir * 16)},2z" fill="#7CC96A" ${stroke(2)}/>`;
      for (let i = 0; i < 5; i++) {
        const a = (i * 2 * Math.PI) / 5 - Math.PI / 2;
        s += `<circle cx="${f(px + Math.cos(a) * 10)}" cy="${f(py + Math.sin(a) * 10)}" r="8" fill="#FF8FB1" ${stroke(2.5)}/>`;
      }
      return s + `<circle cx="${f(px)}" cy="${f(py)}" r="6.5" fill="${C.star}" ${stroke(2.5)}/>`;
    }
    if (prop === "lollipop") {
      return `<path d="M${f(hx)},${f(hy + 6)} L${f(px)},${f(py)}" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round"/>` +
        `<path d="M${f(hx)},${f(hy + 6)} L${f(px)},${f(py)}" fill="none" ${stroke(1.5)} opacity="0.5"/>` +
        `<circle cx="${f(px)}" cy="${f(py)}" r="17" fill="#FFB3D1" ${stroke(4)}/>` +
        `<path d="M${f(px)},${f(py)} m-9,0 a9,9 0 1,1 9,9 a6,6 0 1,1 -6,-6 a3,3 0 1,1 3,3" fill="none" stroke="#E0457B" stroke-width="3" stroke-linecap="round"/>`;
    }
    return "";
  }

  // ---------------- 动作 → 关节角度 ----------------
  function pose(view, action, t, prop) {
    const ph = Math.sin(2 * Math.PI * t);
    const p = {
      lift: 0, armL: [0.18, -0.08], armR: [0.18, -0.08], legL: 0, legR: 0, bend: 0,
      armsLast: false, grip: null,
    };
    if (action === "walk") {
      if (view === "side") { p.legL = -0.45 * ph; p.legR = 0.45 * ph; p.armL = [0.5 * ph, 0.2]; p.armR = [-0.5 * ph, 0.2]; }
      else { p.liftL = Math.max(0, ph) * 12; p.liftR = Math.max(0, -ph) * 12; p.armL = [0.18 + 0.12 * ph, -0.1]; p.armR = [0.18 - 0.12 * ph, -0.1]; }
      p.lift = 4 * Math.abs(ph);
    } else if (action === "jump") {
      const up = Math.sin(Math.PI * Math.min(Math.max(t || 0.5, 0), 1));
      p.lift = 55 * up; p.bend = up;
      p.armL = view === "side" ? [2.5 * up + 0.2 * (1 - up), 0.2] : [0.18 + 2.35 * up, 0.35 * up];
      p.armR = p.armL.slice();
      p.armsLast = up > 0.5;
    } else if (action === "hug") {
      if (view === "side") { p.armL = [1.25, 0.55]; p.armR = [1.35, 0.6]; }
      else { p.armL = [-0.35, -1.9]; p.armR = [-0.35, -1.9]; p.hugFront = true; }
      if (prop === "teddy") p.grip = "both";
    } else if (action === "wave") {
      p.armR = [2.55, -0.25 + 0.4 * ph]; p.armsLast = true;
    } else if (action === "cheer") {
      p.armL = [2.5, 0.2 + 0.15 * ph]; p.armR = [2.5, 0.2 - 0.15 * ph]; p.armsLast = true; p.lift = 3 * Math.abs(ph);
    } else if (action === "flap") {
      p.armL = [1.45 + 0.45 * ph, 0.15]; p.armR = [1.45 + 0.45 * ph, 0.15]; p.armsLast = true;
    } else if (action === "pat") {
      p.armR = [1.1, 0.35 + 0.22 * ph];
    } else if (action === "call") {
      p.targetR = { x: 46, y: -192 }; p.armsLast = true;
    } else if (action === "nose") {
      p.targetR = { x: 6, y: -208 + 2 * ph }; p.armsLast = true;
    } else if (action === "knock") {
      const k = t % 1, tap = Math.max(0, Math.sin(Math.PI * Math.min(k / 0.18, 1))) + Math.max(0, Math.sin(Math.PI * Math.min(Math.max((k - 0.22) / 0.18, 0), 1)));
      p.targetR = { x: 66 + 14 * Math.min(tap, 1), y: -198 }; p.armsLast = true; p.fist = true;
    } else if (action.startsWith("touch")) {
      Object.assign(p, touch(action, t)); p.armsLast = true;
    } else if (GROOM.includes(action)) {
      Object.assign(p, groom(action, t)); p.armsLast = true;
    } else if (action === "hold") {
      if (prop === "balloon") p.armR = view === "side" ? [0.7, 0.3] : [0.55, 0.1];
      else if (prop === "book") p.armR = view === "side" ? [0.45, 1.0] : [0.35, -0.75];
      else p.armR = view === "side" ? [0.35, 0.9] : [0.45, -0.95];
      p.grip = "right";
    }
    return p;
  }

  // ---------------- 摸五官（身体坐标：头中心 0,-232；眼 ±21,-222；嘴 0,-196） ----------------
  const REST_L = limb({ x: -SHOULDER.x, y: SHOULDER.y }, 0.18, -0.08, UPPER, FORE, -1).end;
  const REST_R = limb(SHOULDER, 0.18, -0.08, UPPER, FORE, 1).end;
  const lerp = (a, b, k) => ({ x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k });
  const ease = (k) => k * k * (3 - 2 * k);

  /** 每个摸五官动作在进度 t 时双手的目标位置和脸部变化。 */
  function touchKey(action, t) {
    const ph = Math.sin(2 * Math.PI * t), up = 0.5 + 0.5 * ph;
    switch (action) {
      case "touchNose":   // 食指点鼻头：来回轻点
        return { L: REST_L, R: lerp({ x: 24, y: -196 }, { x: 7, y: -208 }, up) };
      case "touchEars":   // 双手捂在头两侧，交替上下扭动
        return { L: { x: -62, y: -222 + 5 * ph }, R: { x: 62, y: -222 - 5 * ph } };
      case "touchEyes":   // 手指在眼角外侧，眨两次眼
        return { L: { x: -42, y: -226 }, R: { x: 42, y: -226 }, closed: Math.sin(4 * Math.PI * t) > 0.55 };
      case "touchMouth":  // 手放嘴边再向外送出飞吻
        return { L: REST_L, R: lerp({ x: 6, y: -190 }, { x: 62, y: -206 }, up), pucker: true };
      case "cheer":
        return { L: { x: -64, y: -266 }, R: { x: 64, y: -266 } };
    }
  }

  function touch(action, t) {
    let k;
    if (action === "touchAll") {
      const seq = ["touchNose", "touchEars", "touchEyes", "touchMouth", "cheer"];
      const u = (((t % 1) + 1) % 1) * seq.length, i = Math.floor(u), local = u - i;
      const cur = touchKey(seq[i], local * 0.999), prev = touchKey(seq[(i + seq.length - 1) % seq.length], 0.999);
      const m = ease(Math.min(local / 0.3, 1));   // 每段前 30% 从上一个动作滑过去
      k = { L: lerp(prev.L, cur.L, m), R: lerp(prev.R, cur.R, m), closed: m === 1 && cur.closed, pucker: cur.pucker };
    } else k = touchKey(action, t);
    return { targetL: k.L, targetR: k.R, face: { closed: !!k.closed, pucker: !!k.pucker } };
  }

  // ---------------- 好习惯（身体坐标：嘴 0,-196；右边发团中心 70,-216；手臂最远只够到头的高度） ----------------
  function groom(action, t) {
    const a = 2 * Math.PI * t, ph = Math.sin(a), c = Math.cos(a);
    switch (action) {
      case "brushTeeth":  // 右手在嘴边左右来回刷，牙刷头盖在嘴上
        return { targetL: REST_L, targetR: { x: 40 + 8 * ph, y: -192 }, item: "toothbrush", face: { foam: true } };
      case "washFace":    // 双手贴着脸颊画小圈，闭着眼，手边溅水珠
        return { targetL: { x: -40 + 5 * c, y: -206 + 5 * ph }, targetR: { x: 40 - 5 * c, y: -206 + 5 * ph }, face: { closed: true }, fx: "drops" };
      case "scrubHands":  // 双手在胸前一上一下地搓，冒肥皂泡
        return { targetL: { x: -9, y: -126 + 6 * ph }, targetR: { x: 9, y: -126 - 6 * ph }, fx: "bubbles" };
      case "combHair": {  // 梳子从发团上面慢慢梳下来（70%），再快速回到上面
        const k = ((t % 1) + 1) % 1, down = k < 0.7 ? ease(k / 0.7) : 1 - ease((k - 0.7) / 0.3);
        return { targetL: REST_L, targetR: lerp({ x: 66, y: -224 }, { x: 86, y: -198 }, down), item: "comb" };
      }
      case "washHair":    // 双手在头顶两侧一上一下地搓，闭着眼，头发上一团泡沫
        return { targetL: { x: -68 + 5 * c, y: -252 + 5 * ph }, targetR: { x: 68 - 5 * c, y: -252 - 5 * ph }, face: { closed: true }, fx: "suds" };
      case "popBubble": { // 右手食指往右上方戳，指尖的泡泡变大后“啪”地破掉
        const k = ((t % 1) + 1) % 1, reach = k < 0.55 ? ease(k / 0.55) : 1 - ease((k - 0.55) / 0.45);
        return { targetL: REST_L, targetR: lerp({ x: 52, y: -186 }, { x: 80, y: -262 }, reach), fx: "pop" };
      }
      case "shh":         // 食指竖在嘴前，闭着眼，头边飘出 z
        return { targetL: REST_L, targetR: { x: 4, y: -192 + 2 * ph }, face: { closed: true }, fx: "zzz" };
    }
  }

  /** 右手握着的好习惯道具：先画道具再画手，看起来是握着。 */
  function drawItem(item, hp) {
    const x = hp.x, y = hp.y;
    if (item === "toothbrush") {
      let s = `<path d="M${f(x + 18)},${f(y + 2)} L${f(x - 26)},${f(y - 1)}" stroke="${C.line}" stroke-width="13" stroke-linecap="round"/>` +
        `<path d="M${f(x + 18)},${f(y + 2)} L${f(x - 26)},${f(y - 1)}" stroke="#5BC0EB" stroke-width="6" stroke-linecap="round"/>` +
        `<rect x="${f(x - 48)}" y="${f(y - 9)}" width="26" height="12" rx="5" fill="#5BC0EB" ${stroke(3)}/>` +
        `<rect x="${f(x - 46)}" y="${f(y - 19)}" width="22" height="10" rx="2" fill="#FFFFFF" ${stroke(2.5)}/>`;
      for (let i = 1; i < 4; i++) s += `<path d="M${f(x - 46 + i * 5.5)},${f(y - 18)} v8" stroke="#8FD3FF" stroke-width="2"/>`;
      return s;
    }
    if (item === "comb") {
      // 梳子斜靠在右边发团上（向左上倾斜），齿朝着头发
      let s = `<g transform="translate(${f(x)},${f(y)}) rotate(-40)">` +
        `<rect x="-8" y="-50" width="16" height="48" rx="7" fill="#FF8FB1" ${stroke(3.5)}/>`;
      for (let i = 0; i < 6; i++) s += `<path d="M-8,${-44 + i * 6} h-9" ${stroke(3)}/>`;
      return s + `<circle cx="0" cy="-40" r="3" fill="#FFFFFF" opacity="0.8"/></g>`;
    }
    return "";
  }

  /** 洗脸的水珠、搓手的肥皂泡：随 t 循环飘出去，画在最上层。 */
  function groomFx(fx, t, hl, hr) {
    let s = "";
    if (fx === "drops") {
      for (const [hp, dir] of [[hl, -1], [hr, 1]]) {
        for (let i = 0; i < 3; i++) {
          const u = (((t * 2 + i / 3) % 1) + 1) % 1, x = hp.x + dir * (14 + 26 * u), y = hp.y - 12 - 22 * u + 40 * u * u;
          s += `<path d="M${f(x)},${f(y)} q-7,11 0,14 q7,-3 0,-14z" fill="${C.tear}" stroke="#2F86C0" stroke-width="2.5" opacity="${f(1 - u * 0.7)}"/>`;
        }
      }
    }
    if (fx === "bubbles") {
      const xs = [-46, -26, 0, 26, 46], cy = (hl.y + hr.y) / 2;   // 泡泡只升到下巴下面，不挡脸
      xs.forEach((dx, i) => {
        const u = (((t + i / xs.length) % 1) + 1) % 1, r = 8 + 3 * (i % 2), x = dx + 4 * Math.sin(2 * Math.PI * (u + i / 5)), y = cy - 8 - 36 * u;
        s += `<g opacity="${f(1 - u * u * 0.8)}"><circle cx="${f(x)}" cy="${f(y)}" r="${r}" fill="#FFFFFF" fill-opacity="0.9" stroke="#3FA7DB" stroke-width="2.8"/>` +
          `<circle cx="${f(x - r * 0.35)}" cy="${f(y - r * 0.35)}" r="${f(r * 0.25)}" fill="#FFFFFF"/></g>`;
      });
    }
    if (fx === "suds") {
      // 头顶的泡沫团（头中心 0,-232，头顶约 -292），外加几个往上飘的小泡泡
      [[-40, -286, 16], [-18, -298, 19], [8, -300, 18], [32, -292, 17], [52, -278, 13], [-56, -272, 12]].forEach(([x, y, r]) => {
        s += `<circle cx="${x}" cy="${y}" r="${r}" fill="#FFFFFF" stroke="#8FD3FF" stroke-width="2.5"/>`;
      });
      [-30, 10, 44].forEach((dx, i) => {
        const u = (((t + i / 3) % 1) + 1) % 1, y = -318 - 40 * u;
        s += `<circle cx="${f(dx + 6 * Math.sin(2 * Math.PI * (u + i / 3)))}" cy="${f(y)}" r="${7 + (i % 2) * 2}" fill="#FFFFFF" fill-opacity="0.85" stroke="#3FA7DB" stroke-width="2.4" opacity="${f(1 - u * 0.8)}"/>`;
      });
    }
    if (fx === "pop") {
      const k = ((t % 1) + 1) % 1, x = hr.x + 28, y = hr.y - 20;
      if (k < 0.55) {            // 泡泡慢慢变大
        const r = 10 + 12 * ease(k / 0.55);
        s += `<circle cx="${f(x)}" cy="${f(y - r * 0.4)}" r="${f(r)}" fill="#FFFFFF" fill-opacity="0.6" stroke="#3FA7DB" stroke-width="2.8"/>` +
          `<circle cx="${f(x - r * 0.35)}" cy="${f(y - r * 0.75)}" r="${f(r * 0.22)}" fill="#FFFFFF"/>`;
      } else if (k < 0.8) {      // 啪：一圈短线和小水点向外散开
        const u = (k - 0.55) / 0.25;
        for (let i = 0; i < 8; i++) {
          const a = (Math.PI * 2 * i) / 8, r1 = 14 + 16 * u, r2 = r1 + 10;
          s += `<path d="M${f(x + r1 * Math.cos(a))},${f(y - 8 + r1 * Math.sin(a))} L${f(x + r2 * Math.cos(a))},${f(y - 8 + r2 * Math.sin(a))}" stroke="#3FA7DB" stroke-width="3" stroke-linecap="round" opacity="${f(1 - u)}"/>`;
        }
      }
    }
    if (fx === "zzz") {
      // 头右上方飘起三个 z（用线画，不是文字）
      for (let i = 0; i < 3; i++) {
        const u = (((t * 0.5 + i / 3) % 1) + 1) % 1, z = 9 + 5 * i, x = 72 + 18 * i + 10 * u, y = -280 - 26 * i - 20 * u;
        s += `<path d="M${f(x - z)},${f(y - z)} h${f(2 * z)} l${f(-2 * z)},${f(2 * z)} h${f(2 * z)}" fill="none" stroke="#7C83D6" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" opacity="${f(0.35 + 0.65 * (1 - u))}"/>`;
      }
    }
    return s;
  }

  // ---------------- 服装：巫师帽（头部坐标，画在头发上面） ----------------
  function witchHat(view) {
    const P = "#8E5BD6", band = C.bow;
    if (view === "side") {
      return `<g transform="rotate(-8)"><ellipse cx="-2" cy="-52" rx="80" ry="15" fill="${P}" ${stroke()}/>` +
        `<path d="M-40,-58 L-6,-150 Q4,-162 24,-158 Q12,-150 10,-140 L40,-58 Z" fill="${P}" ${stroke()}/>` +
        `<path d="M-38,-62 Q0,-72 38,-62 L33,-78 Q0,-88 -33,-78 Z" fill="${band}" ${stroke(4)}/></g>`;
    }
    return `<ellipse cx="0" cy="-54" rx="88" ry="17" fill="${P}" ${stroke()}/>` +
      `<path d="M-42,-60 L-8,-152 Q2,-164 24,-160 Q12,-152 10,-142 L42,-60 Z" fill="${P}" ${stroke()}/>` +
      `<path d="M-40,-64 Q0,-74 40,-64 L35,-80 Q0,-90 -35,-80 Z" fill="${band}" ${stroke(4)}/>` +
      `<path d="M-14,-108 L-4,-128" stroke="#B48CF0" stroke-width="5" stroke-linecap="round" opacity="0.8"/>`;
  }

  /** 左手提着的南瓜糖果桶：提手挂在手上，桶垂在手下方。先画桶，再画手，看起来是握着提手。 */
  function drawCarry(item, hp) {
    if (item !== "pumpkinBucket") return "";
    const x = hp.x, y = hp.y + 40;
    return `<path d="M${f(x - 24)},${f(y - 12)} Q${f(x - 22)},${f(hp.y - 6)} ${f(x)},${f(hp.y)} Q${f(x + 22)},${f(hp.y - 6)} ${f(x + 24)},${f(y - 12)}" fill="none" stroke="#2B2B2B" stroke-width="4" stroke-linecap="round"/>` +
      `<ellipse cx="${f(x)}" cy="${f(y + 4)}" rx="30" ry="25" fill="#FF8C1A" ${stroke(4)}/>` +
      `<path d="M${f(x - 10)},${f(y - 20)} Q${f(x - 14)},${f(y + 4)} ${f(x - 10)},${f(y + 28)} M${f(x + 10)},${f(y - 20)} Q${f(x + 14)},${f(y + 4)} ${f(x + 10)},${f(y + 28)}" fill="none" stroke="#D96E0A" stroke-width="3"/>` +
      `<ellipse cx="${f(x)}" cy="${f(y - 18)}" rx="22" ry="6" fill="#5A3A22" ${stroke(3)}/>` +
      `<path d="M${f(x - 15)},${f(y)} l6,-9 l6,9 Z M${f(x + 3)},${f(y)} l6,-9 l6,9 Z" fill="#4A3B33"/>` +
      `<path d="M${f(x - 14)},${f(y + 9)} Q${f(x)},${f(y + 22)} ${f(x + 14)},${f(y + 9)}" fill="none" stroke="#4A3B33" stroke-width="4" stroke-linecap="round"/>`;
  }

  // ---------------- 组装 ----------------
  function body(o) {
    const { view, expression, action, prop } = o;
    const P = pose(view, action, o.t || 0, prop);
    const lift = P.lift || 0;
    let back = "", mid = "", front = "", top = "";
    const heldProp = action === "hold" || (action === "hug" && prop === "teddy") ? prop : null;

    if (view === "side") {
      const sh = { x: 0, y: -160 }, hip = { x: 0, y: -88 };
      const farArm = limb(sh, P.armL[0], P.armL[1], UPPER, FORE, 1);
      const nearArm = limb(sh, P.armR[0], P.armR[1], UPPER, FORE, 1);
      const knee = P.bend * 0.9;
      const farLeg = limb(hip, P.legL - knee * 0.3, knee, LEG / 2, LEG / 2, 1);
      const nearLeg = limb(hip, P.legR + knee * 0.2, knee, LEG / 2, LEG / 2, 1);
      back += armPath(farArm, true) + drawCarry(o.carry, farArm.end) + hand(farArm.end, !!o.carry, true);
      back += `<g opacity="0.85">${bentLeg(hip, farLeg)}</g>`;     // 远处的腿稍暗一点，看起来在后面
      mid += bentLeg(hip, nearLeg);
      mid += dressSide();
      lastPts = { handL: farArm.end, handR: nearArm.end };
      front += armPath(nearArm) + drawProp(heldProp, nearArm.end, "side") + sleeve(2, -160) + hand(nearArm.end, !!heldProp);
      top = `<g transform="translate(${HEAD.x},${HEAD.y})">${headSide(expression)}${o.hat ? witchHat("side") : ""}</g>`;
      return wrap(o, lift, back + mid + front + top, P);
    }

    // 正面 / 背面
    const sL = { x: -SHOULDER.x, y: SHOULDER.y }, sR = { x: SHOULDER.x, y: SHOULDER.y };
    const armL = P.targetL ? ik(sL, P.targetL, UPPER, FORE) : limb(sL, P.armL[0], P.armL[1], UPPER, FORE, -1);
    const armR = P.targetR ? ik(sR, P.targetR, UPPER, FORE) : limb(sR, P.armR[0], P.armR[1], UPPER, FORE, 1);
    lastPts = { handL: armL.end, handR: armR.end };
    const tuck = P.bend * 22;
    for (const [s, liftKey] of [[-1, "liftL"], [1, "liftR"]]) {
      const footLift = (P[liftKey] || 0) + tuck;
      const hipP = { x: s * HIP.x, y: HIP.y };
      const ankle = { x: s * (HIP.x + P.bend * 8), y: -14 - footLift };
      mid += legPath(hipP, ankle) + shoe(ankle);
    }
    const isBack = view === "back";
    mid += dressFront(isBack);

    let arms = "";
    if (P.hugFront && !isBack) {
      // 拥抱：手臂交叉抱在胸前（或抱着泰迪熊），手在身体前面
      arms += heldProp ? drawProp("teddy", { x: 0, y: -132 }, view) : "";
      arms += armPath(armL) + armPath(armR) + sleeve(-38, -160) + sleeve(38, -160) + hand(armL.end, !!heldProp) + hand(armR.end, !!heldProp);
    } else if (P.hugFront && isBack) {
      // 背面看拥抱：只露出弯到身前的手肘
      back += armPath({ start: sL, elbow: { x: -50, y: -128 }, end: { x: -30, y: -138 } }, true) +
              armPath({ start: sR, elbow: { x: 50, y: -128 }, end: { x: 30, y: -138 } }, true);
      arms += sleeve(-38, -160) + sleeve(38, -160);
    } else {
      arms += armPath(armL) + drawCarry(o.carry, armL.end) + hand(armL.end, !!o.carry);
      arms += armPath(armR) + drawProp(heldProp, armR.end, view) + drawItem(P.item, armR.end) + hand(armR.end, !!heldProp || !!P.fist || !!P.item);
      arms += sleeve(-38, -160) + sleeve(38, -160) + groomFx(P.fx, o.t || 0, armL.end, armR.end);
    }
    const head = `<g transform="translate(${HEAD.x},${HEAD.y})">${isBack ? headBack() : headFront(expression, P.face)}${o.hat ? witchHat(view) : ""}</g>`;
    const content = P.armsLast ? back + mid + head + arms : back + mid + arms + head;
    return wrap(o, lift, content, P);
  }

  let lastPts = null;

  function wrap(o, lift, content, P) {
    const mirror = o.view === "side" && o.facing === "left" ? -1 : 1;
    const s = o.scale || 1;
    const shadowW = 58 * (1 - 0.35 * Math.min(lift / 55, 1));
    return `<g class="lily" transform="translate(${f(o.x || 0)},${f(o.y || 0)}) scale(${f(s * mirror)},${f(s)})">` +
      `<ellipse cx="0" cy="4" rx="${f(shadowW)}" ry="9" fill="#4A3B33" opacity="0.15"/>` +
      `<g${o.filter === false ? "" : ' filter="url(#lily-crayon)"'} transform="translate(0,${f(-lift)})">${content}</g></g>`;
  }

  // ---------------- 对外接口 ----------------
  function draw(opts = {}) {
    const o = Object.assign({ view: "front", facing: "right", expression: "happy", action: "stand", prop: null, t: 0, x: 0, y: 0, scale: 1 }, opts);
    if (!VIEWS.includes(o.view)) throw new Error(`view 只能是 ${VIEWS.join("/")}`);
    if (!EXPRESSIONS.includes(o.expression)) throw new Error(`expression 只能是 ${EXPRESSIONS.join("/")}`);
    if (!ACTIONS.includes(o.action)) throw new Error(`action 只能是 ${ACTIONS.join("/")}`);
    if (o.prop && !PROPS.includes(o.prop)) throw new Error(`prop 只能是 ${PROPS.join("/")}`);
    if (o.action === "hold" && !o.prop) o.prop = "balloon";
    if (o.hat && !HATS.includes(o.hat)) throw new Error(`hat 只能是 ${HATS.join("/")}`);
    if (o.carry && !CARRY.includes(o.carry)) throw new Error(`carry 只能是 ${CARRY.join("/")}`);
    return body(o);
  }

  /** 画面坐标里的关键点：手、头中心、包围盒。 */
  function points(opts = {}) {
    const o = Object.assign({ view: "front", facing: "right", expression: "happy", action: "stand", prop: null, t: 0, x: 0, y: 0, scale: 1 }, opts);
    draw(o);
    const lift = pose(o.view, o.action, o.t || 0, o.prop).lift || 0;
    const m = o.view === "side" && o.facing === "left" ? -1 : 1, s = o.scale || 1;
    const w = (p) => ({ x: Math.round(o.x + s * m * p.x), y: Math.round(o.y + s * (p.y - lift)) });
    const hl = w(lastPts.handL), hr = w(lastPts.handR);
    return { handL: hl, handR: hr, head: w({ x: 0, y: HEAD.y + 8 }), top: Math.round(o.y + s * ((o.hat ? -396 : -302) - lift)), bottom: Math.round(o.y),
             left: Math.min(hl.x - (o.carry ? 32 * s : 0), hr.x, Math.round(o.x - s * 105)), right: Math.max(hl.x, hr.x, Math.round(o.x + s * 105)) };
  }

  function crayonDefs() {
    return `<filter id="lily-crayon" x="-10%" y="-10%" width="120%" height="120%">
  <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="3" seed="4" result="warp"/>
  <feDisplacementMap in="SourceGraphic" in2="warp" scale="4" xChannelSelector="R" yChannelSelector="G" result="wobbly"/>
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="8" result="grain"/>
  <feColorMatrix in="grain" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -3.2 2.75" result="grainA"/>
  <feComposite in="wobbly" in2="grainA" operator="in"/>
</filter>`;
  }

  function svg(opts = {}, frame = {}) {
    const w = frame.width || 400, h = frame.height || 460;
    const o = Object.assign({ x: w / 2, y: h - 40 }, opts);
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}">` +
      `<defs>${crayonDefs()}</defs>${frame.background ? `<rect width="${w}" height="${h}" fill="${frame.background}"/>` : ""}${draw(o)}</svg>`;
  }

  const Lily = { draw, svg, points, crayonDefs, VIEWS, EXPRESSIONS, ACTIONS, PROPS, HATS, CARRY, COLORS: C };
  if (typeof module !== "undefined" && module.exports) module.exports = Lily;
  else root.Lily = Lily;
})(typeof window !== "undefined" ? window : globalThis);

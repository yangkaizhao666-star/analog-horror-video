# -*- coding: utf-8 -*-
"""手机 UI 动效参数与节奏生成器（屏幕录屏式模拟恐怖专用）。

把参考视频《夜景模式》逐帧实测得到的"丝滑"手法固化为可复用参数：
缓动函数、动效规格表（时长/帧数/缓动）、逐帧变换、真人打字节奏、
通知横幅与相机倒计时进度。渲染时把本脚本输出的数值喂给 PIL 关键帧
或剪辑软件即可，脚本本身不生成图片、不依赖第三方库。

用法:
    python ui_motion.py selfcheck                 # 自检（含错误样例）
    python ui_motion.py spec                       # 列出全部动效规格
    python ui_motion.py ease EASE_NAME [--fps 30]  # 打印某缓动的逐帧进度
    python ui_motion.py type "要打的中文" [--fps 30] [--seed 7]
    python ui_motion.py frames MOTION_NAME [--fps 30]

仅依赖 Python 标准库。
"""
import argparse
import math
import random
import sys


def clamp01(p):
    if p < 0.0:
        return 0.0
    if p > 1.0:
        return 1.0
    return p


def linear(p):
    return p


def ease_in_quad(p):
    return p * p


def ease_out_quad(p):
    return 1.0 - (1.0 - p) ** 2


def ease_in_out_quad(p):
    return 2.0 * p * p if p < 0.5 else 1.0 - ((-2.0 * p + 2.0) ** 2) / 2.0


def ease_in_cubic(p):
    return p ** 3


def ease_out_cubic(p):
    return 1.0 - (1.0 - p) ** 3


def ease_in_out_cubic(p):
    if p < 0.5:
        return 4.0 * p ** 3
    return 1.0 - ((-2.0 * p + 2.0) ** 3) / 2.0


def ease_out_quint(p):
    return 1.0 - (1.0 - p) ** 5


def ease_in_quint(p):
    return p ** 5


def ease_out_back(p, overshoot=1.70158):
    """轻微过冲后回弹，用于卡片展开/通知落定，制造"有质量"的感觉。"""
    c1 = overshoot
    c3 = c1 + 1.0
    return 1.0 + c3 * (p - 1.0) ** 3 + c1 * (p - 1.0) ** 2


def cubic_bezier(x1, y1, x2, y2):
    """返回一个近似 CSS cubic-bezier(x1,y1,x2,y2) 的缓动函数。

    用二分法按 x 求参数 t，再取 y。贝塞尔曲线端点固定为 (0,0)、(1,1)。
    """
    def bx(t):
        return 3.0 * (1.0 - t) ** 2 * t * x1 + 3.0 * (1.0 - t) * t * t * x2 + t ** 3

    def by(t):
        return 3.0 * (1.0 - t) ** 2 * t * y1 + 3.0 * (1.0 - t) * t * t * y2 + t ** 3

    def fn(p):
        p = clamp01(p)
        if p <= 0.0:
            return 0.0
        if p >= 1.0:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(24):
            mid = (lo + hi) / 2.0
            if bx(mid) < p:
                lo = mid
            else:
                hi = mid
        return by((lo + hi) / 2.0)

    return fn


ios_ease_out = cubic_bezier(0.32, 0.72, 0.0, 1.0)
ios_ease_in = cubic_bezier(0.42, 0.0, 0.58, 1.0)

EASINGS = {
    "linear": linear,
    "ease_in_quad": ease_in_quad,
    "ease_out_quad": ease_out_quad,
    "ease_in_out_quad": ease_in_out_quad,
    "ease_in_cubic": ease_in_cubic,
    "ease_out_cubic": ease_out_cubic,
    "ease_in_out_cubic": ease_in_out_cubic,
    "ease_in_quint": ease_in_quint,
    "ease_out_quint": ease_out_quint,
    "ease_out_back": ease_out_back,
    "ios_ease_out": ios_ease_out,
    "ios_ease_in": ios_ease_in,
}


def lerp(a, b, p):
    return a + (b - a) * p


def ease_between(start, end, t, duration, easing_name):
    """t 为当前时间（秒），返回 start→end 的缓动插值；超出区间则夹到端点。"""
    if duration <= 0:
        raise ValueError("duration 必须为正数")
    if t <= 0:
        return start
    if t >= duration:
        return end
    p = t / duration
    return lerp(start, end, EASINGS[easing_name](p))


def eased_rect(rect0, rect1, t, duration, easing_name):
    """对矩形 (x, y, w, h) 整体插值，用于卡片缩放/收缩。"""
    return tuple(round(ease_between(a, b, t, duration, easing_name), 3)
                 for a, b in zip(rect0, rect1))


def alpha_fade(t, duration, fade_in=True):
    """透明度淡入/淡出，返回 0→1（或 1→0）。"""
    p = clamp01(t / duration) if duration > 0 else 1.0
    return p if fade_in else 1.0 - p


MOTION_SPEC = {
    "keyboard_up":      {"duration": 0.27, "fps": 30, "ease": "ease_out_cubic",
                         "note": "键盘从底部滑入，输入区同步上推"},
    "keyboard_down":    {"duration": 0.25, "fps": 30, "ease": "ease_in_cubic",
                         "note": "键盘向下滑出，输入区回落"},
    "app_open":         {"duration": 0.30, "fps": 30, "ease": "ios_ease_out",
                         "note": "圆角小卡片从图标位置放大到全屏，圆角渐隐"},
    "app_close":        {"duration": 0.40, "fps": 30, "ease": "ios_ease_in",
                         "note": "当前页卡片化（带圆角）收缩，露出下层界面"},
    "multitask_slide":  {"duration": 0.30, "fps": 30, "ease": "ease_out_cubic",
                         "note": "多任务卡片横向滑动，景深缩放+背景模糊"},
    "banner_in":        {"duration": 0.35, "fps": 30, "ease": "ease_out_back",
                         "note": "使用中顶部毛玻璃横幅滑入，不打断下层操作"},
    "banner_hold":      {"duration": 1.80, "fps": 30, "ease": "linear",
                         "note": "横幅停留（不变化）"},
    "banner_out":       {"duration": 0.30, "fps": 30, "ease": "ease_in_cubic",
                         "note": "横幅向上收起"},
    "lock_notice_in":   {"duration": 0.35, "fps": 30, "ease": "ease_out_back",
                         "note": "锁屏新通知从顶部滑入，旧通知整体下移让位"},
    "list_item_fade":   {"duration": 0.25, "fps": 30, "ease": "ease_out_quad",
                         "note": "列表新消息/评论从底部淡入并上推"},
    "bubble_send":      {"duration": 0.20, "fps": 30, "ease": "ease_out_quad",
                         "note": "自己的气泡从输入位置弹入并轻微放大"},
}


def frame_count(name, fps=None):
    """某动效在给定帧率下占用的帧数（向上取整，保证至少 1 帧）。"""
    spec = MOTION_SPEC[name]
    f = fps or spec["fps"]
    return max(1, int(math.ceil(spec["duration"] * f)))


def motion_frames(name, fps=None):
    """生成某动效逐帧的进度序列，返回 [(frame_index, time_sec, eased_progress)]。"""
    spec = MOTION_SPEC[name]
    f = fps or spec["fps"]
    n = frame_count(name, f)
    easing = EASINGS[spec["ease"]]
    out = []
    for i in range(n):
        t = (i + 1) / f
        p = clamp01(t / spec["duration"])
        out.append((i, round(t, 4), round(easing(p), 4)))
    return out


def typing_schedule(text, start=0.0, base_cps=6.0, jitter=0.12,
                    long_pause=0.55, pause_every=0, seed=None):
    """把一段文本转成逐字符出现的时间序列，模拟真人不均匀节奏。

    base_cps   : 平均每秒字符数（中文手机打字经验值 4–8）。
    jitter     : 每个字符间隔的随机抖动比例（0–1），制造连打/停顿。
    long_pause : 长停顿秒数；pause_every>0 时每隔若干字符插入一次（思考/选词）。
    返回 [(char, appear_time_sec)]，长度与文本一致，时间严格递增。
    """
    if not text:
        raise ValueError("text 不能为空")
    if base_cps <= 0:
        raise ValueError("base_cps 必须为正数")
    if not 0.0 <= jitter <= 1.0:
        raise ValueError("jitter 必须在 0–1 之间")
    rng = random.Random(seed)
    base_gap = 1.0 / base_cps
    schedule = []
    t = float(start)
    for i, ch in enumerate(text):
        if i > 0 and pause_every > 0 and i % pause_every == 0:
            t += long_pause
        gap = base_gap * (1.0 + rng.uniform(-jitter, jitter))
        gap = max(gap, base_gap * 0.3)
        t += gap
        schedule.append((ch, round(t, 3)))
    return schedule


def pinyin_states(text, seed=None):
    """演示拼音输入法状态机的时间线（未确认拼音→候选→上屏）。"""
    rng = random.Random(seed)
    states = []
    t = 0.0
    for word in text.split():
        composing = 0.25 + rng.uniform(0, 0.2)
        states.append({"at": round(t, 3), "state": "composing",
                       "display": "pinyin", "underlined": True})
        t += composing
        states.append({"at": round(t, 3), "state": "committed",
                       "display": word, "underlined": False})
        t += 0.12
    return states


def banner_timeline(start, fps=30):
    """一次完整横幅（滑入→停留→收起）的关键时间点，返回分段区间。"""
    tin = MOTION_SPEC["banner_in"]["duration"]
    hold = MOTION_SPEC["banner_hold"]["duration"]
    tout = MOTION_SPEC["banner_out"]["duration"]
    return [
        ("in", start, start + tin),
        ("hold", start + tin, start + tin + hold),
        ("out", start + tin + hold, start + tin + hold + tout),
    ]


def camera_countdown(start, seconds, t):
    """夜景拍摄倒计时：返回 (剩余数字, 圆环进度0–1)。"""
    if seconds <= 0:
        raise ValueError("seconds 必须为正数")
    elapsed = t - start
    if elapsed < 0:
        return seconds, 0.0
    if elapsed >= seconds:
        return 0, 1.0
    remaining = seconds - int(math.floor(elapsed))
    ring = clamp01(elapsed - math.floor(elapsed))
    return remaining, round(ring, 4)


def _approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


def selfcheck():
    failures = []

    overshoot_names = {"ease_out_back"}
    for name, fn in EASINGS.items():
        if not _approx(fn(1.0), 1.0):
            failures.append(f"{name} 终点错误: {fn(1.0)}")
        if name in overshoot_names:
            vals = [fn(k / 20.0) for k in range(21)]
            peak = max(range(len(vals)), key=lambda i: vals[i])
            if vals[peak] <= 1.0:
                failures.append(f"{name} 未出现过冲")
            if any(b < a - 1e-9 for a, b in zip(vals[:peak], vals[1:peak + 1])):
                failures.append(f"{name} 过冲前未单调上升")
            if any(b > a + 1e-9 for a, b in zip(vals[peak:], vals[peak + 1:])):
                failures.append(f"{name} 过冲后未单调回落")
            continue
        if not _approx(fn(0.0), 0.0):
            failures.append(f"{name} 起点错误: {fn(0.0)}")
        prev = -1.0
        for k in range(21):
            v = fn(k / 20.0)
            if v < prev - 1e-9:
                failures.append(f"{name} 非单调")
                break
            prev = v

    if not _approx(ease_between(0, 100, -1, 1, "linear"), 0):
        failures.append("ease_between 起点未夹住")
    if not _approx(ease_between(0, 100, 2, 1, "linear"), 100):
        failures.append("ease_between 终点未夹住")

    sched = typing_schedule("搬新家第一晚", seed=7)
    if len(sched) != len("搬新家第一晚"):
        failures.append("typing_schedule 长度不一致")
    times = [t for _, t in sched]
    if any(b <= a for a, b in zip(times, times[1:])):
        failures.append("typing_schedule 时间未严格递增")

    for bad in (lambda: typing_schedule(""),
                lambda: typing_schedule("x", base_cps=0),
                lambda: typing_schedule("x", jitter=2)):
        try:
            bad()
            failures.append("错误输入未被拦截")
        except ValueError:
            pass

    for name in MOTION_SPEC:
        n = frame_count(name, 30)
        if n < 1 or n != len(motion_frames(name, 30)):
            failures.append(f"{name} 帧数异常")
        last = motion_frames(name, 30)[-1][2]
        if not _approx(last, 1.0, 1e-6):
            failures.append(f"{name} 末帧未到达 1.0")

    if camera_countdown(0, 6, -1)[1] != 0.0:
        failures.append("倒计时起点进度错误")
    if camera_countdown(0, 6, 6) != (0, 1.0):
        failures.append("倒计时终点错误")

    if failures:
        print("自检失败：")
        for f in failures:
            print("  -", f)
        return 1
    print("自检通过：缓动端点/单调性、插值、打字节奏、错误拦截、帧数、倒计时均正确。")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="手机 UI 动效参数与节奏生成器")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("selfcheck")
    sub.add_parser("spec")

    pe = sub.add_parser("ease")
    pe.add_argument("name", choices=EASINGS)
    pe.add_argument("--fps", type=int, default=30)

    pt = sub.add_parser("type")
    pt.add_argument("text")
    pt.add_argument("--fps", type=int, default=30)
    pt.add_argument("--seed", type=int, default=7)

    pf = sub.add_parser("frames")
    pf.add_argument("name", choices=MOTION_SPEC)
    pf.add_argument("--fps", type=int, default=30)

    args = p.parse_args(argv)

    if args.cmd == "selfcheck":
        return selfcheck()
    if args.cmd == "spec":
        for name, s in MOTION_SPEC:
            print(f"{name:<16} {s['duration']:>4}s  {frame_count(name):>2}帧@30  "
                  f"{s['ease']:<15} {s['note']}")
        return 0
    if args.cmd == "ease":
        fn = EASINGS[args.name]
        for i in range(args.fps):
            pp = (i + 1) / args.fps
            print(f"frame {i:>2}  p={pp:.3f}  -> {fn(pp):.4f}")
        return 0
    if args.cmd == "type":
        for ch, t in typing_schedule(args.text, seed=args.seed):
            print(f"{t:>7.3f}s  {ch}")
        return 0
    if args.cmd == "frames":
        for i, t, prog in motion_frames(args.name, args.fps):
            print(f"frame {i:>2}  t={t:.3f}  progress={prog:.4f}")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

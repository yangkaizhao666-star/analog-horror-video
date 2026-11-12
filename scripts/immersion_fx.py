# -*- coding: utf-8 -*-
"""沉浸感与生理反馈参数生成器（屏幕录屏式模拟恐怖专用）。

把参考视频《线下面试》（1080×1920，30fps，106.5s）逐帧实测得到的
"参与感"手法固化为可复用参数与函数：

1. 心跳/震动：双搏（lub-dub）心跳波形，驱动画面缩放与位移；
2. 颜色反馈：冷蓝 → 暗红的分级渐变（含"红色渗入"阶段），输出 RGB；
3. 通知轰炸：不均匀间隔的连续推送时间点，制造"系统强制推进"感；
4. 持续微震：低频随机微抖，让静止的手机画面始终"活着"。

渲染时把输出数值喂给 PIL/ffmpeg/剪辑软件关键帧即可。脚本不生成图片、
仅依赖 Python 标准库。

用法:
    python immersion_fx.py selfcheck
    python immersion_fx.py heartbeat [--bpm 72] [--sec 3] [--fps 30]
    python immersion_fx.py color [--steps 12]
    python immersion_fx.py barrage --start 49 --end 76 --count 14 [--seed 5]
    python immersion_fx.py shake --sec 4 [--fps 30] [--seed 5]
"""
import argparse
import math
import random


def _gaussian(x, center, width):
    d = (x - center) / width
    return math.exp(-d * d)


def heartbeat_phase(t, bpm=72):
    """返回 t 时刻的心跳强度（0..1），自动按周期循环。

    强搏（lub）位于周期 0.0 处、弱搏（dub）位于约 0.28 周期处，
    弱搏幅度约为强搏的 0.55，与真实心音/脉搏触感一致。
    """
    period = 60.0 / bpm
    phase = (t % period) / period
    lub = _gaussian(phase, 0.06, 0.045)
    dub = 0.55 * _gaussian(phase, 0.30, 0.05)
    return min(1.0, lub + dub)


def heartbeat_scale(t, bpm=72, amp=0.02):
    """心跳驱动的画面缩放系数（amp 为相对幅度，2% 已可感知、不夸张）。"""
    return 1.0 + amp * heartbeat_phase(t, bpm)


COLOR_KEYFRAMES = [
    (0.00, (28, 42, 96)),
    (0.55, (34, 30, 82)),
    (0.72, (96, 24, 34)),
    (1.00, (128, 18, 22)),
]


def _lerp(a, b, p):
    return a + (b - a) * p


def color_grade(p):
    """返回进度 p 对应的叠加色 (R,G,B)，用于整屏调色层/染色。"""
    if p <= 0.0:
        return COLOR_KEYFRAMES[0][1]
    if p >= 1.0:
        return COLOR_KEYFRAMES[-1][1]
    for i in range(len(COLOR_KEYFRAMES) - 1):
        p0, c0 = COLOR_KEYFRAMES[i]
        p1, c1 = COLOR_KEYFRAMES[i + 1]
        if p0 <= p <= p1:
            local = (p - p0) / (p1 - p0) if p1 > p0 else 0.0
            return tuple(round(_lerp(c0[k], c1[k], local)) for k in range(3))
    return COLOR_KEYFRAMES[-1][1]


def barrage_schedule(start, end, count, seed=5):
    """返回 count 个通知的时间点（秒），间隔不均匀、整体前疏后密。"""
    rng = random.Random(seed)
    span = end - start
    points = []
    for i in range(1, count + 1):
        base = i / count
        biased = base ** 1.6
        jitter = rng.uniform(-0.015, 0.015) * span
        points.append(start + span * biased + jitter)
    points = sorted(max(start, min(end, p)) for p in points)
    out = []
    for i, t in enumerate(points):
        stack = 1 + min(2, int(i / max(1, count) * 3.2))
        out.append((round(t, 2), stack))
    return out


def micro_shake(t, fps=30, amp_px=5.0, seed=5, seed_px_h=0.0):
    """返回 t 时刻的微震位移 (dx, dy)，单位像素（基于 1080 宽画面）。"""
    rng = random.Random(seed)
    fx1 = rng.uniform(0.7, 1.3)
    fy1 = rng.uniform(0.7, 1.3)
    fx2 = rng.uniform(2.1, 3.3)
    fy2 = rng.uniform(2.1, 3.3)
    dx = amp_px * 0.7 * math.sin(2 * math.pi * fx1 * t) \
        + amp_px * 0.3 * math.sin(2 * math.pi * fx2 * t + 1.7)
    dy = amp_px * 0.7 * math.sin(2 * math.pi * fy1 * t + 0.9) \
        + amp_px * 0.3 * math.sin(2 * math.pi * fy2 * t + 0.4)
    return dx, dy


def _selfcheck():
    bpm = 72
    period = 60.0 / bpm
    vals = [heartbeat_phase(t / 1000, bpm) for t in range(int(period * 1000))]
    peaks = sum(1 for i in range(1, len(vals) - 1)
                if vals[i] > vals[i - 1] and vals[i] > vals[i + 1] and vals[i] > 0.2)
    assert peaks == 2, "心跳应含强/弱两个搏峰，实际 %d 个" % peaks
    assert color_grade(0) == (28, 42, 96)
    assert color_grade(1)[0] > color_grade(0)[0]
    sch = barrage_schedule(49, 76, 14)
    assert len(sch) == 14
    assert all(sch[i][0] <= sch[i + 1][0] for i in range(13))
    for k in range(300):
        dx, dy = micro_shake(k / 30.0)
        assert abs(dx) <= 5.01 and abs(dy) <= 5.01
    print("selfcheck OK：心跳双搏、颜色渐变、通知轰炸、微震有界均通过。")


def main():
    ap = argparse.ArgumentParser(description="沉浸感与生理反馈参数生成器")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("selfcheck")

    hb = sub.add_parser("heartbeat")
    hb.add_argument("--bpm", type=float, default=72)
    hb.add_argument("--sec", type=float, default=3.0)
    hb.add_argument("--fps", type=float, default=30)
    hb.add_argument("--amp", type=float, default=0.02)

    co = sub.add_parser("color")
    co.add_argument("--steps", type=int, default=12)

    ba = sub.add_parser("barrage")
    ba.add_argument("--start", type=float, required=True)
    ba.add_argument("--end", type=float, required=True)
    ba.add_argument("--count", type=int, required=True)
    ba.add_argument("--seed", type=int, default=5)

    sh = sub.add_parser("shake")
    sh.add_argument("--sec", type=float, default=4.0)
    sh.add_argument("--fps", type=float, default=30)
    sh.add_argument("--amp", type=float, default=5.0)
    sh.add_argument("--seed", type=int, default=5)

    a = ap.parse_args()

    if a.cmd == "selfcheck":
        _selfcheck()
    elif a.cmd == "heartbeat":
        n = int(a.sec * a.fps)
        print(" t(s)   strength  scale")
        for i in range(n):
            t = i / a.fps
            s = heartbeat_phase(t, a.bpm)
            print(f"{t:5.2f}   {s:.3f}    {heartbeat_scale(t, a.bpm, a.amp):.4f}")
    elif a.cmd == "color":
        for i in range(a.steps):
            p = i / (a.steps - 1)
            print(f"p={p:4.2f}  RGB={color_grade(p)}")
    elif a.cmd == "barrage":
        for t, stack in barrage_schedule(a.start, a.end, a.count, a.seed):
            print(f"t={t:6.2f}s  同时堆叠={stack}")
    elif a.cmd == "shake":
        n = int(a.sec * a.fps)
        for i in range(n):
            t = i / a.fps
            dx, dy = micro_shake(t, amp_px=a.amp, seed=a.seed)
            print(f"t={t:5.2f}  dx={dx:6.2f}  dy={dy:6.2f}")


if __name__ == "__main__":
    main()

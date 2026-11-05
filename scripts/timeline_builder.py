# -*- coding: utf-8 -*-
"""把消息流 JSON 转换为时间轴、镜头清单、音效清单与统计数据。

用法:
    python timeline_builder.py <message_flow.json>
仅依赖 Python 标准库。
"""
import json
import sys
from collections import Counter, defaultdict


def fmt_time(sec):
    sec = int(sec)
    return f"{sec // 60:02d}:{sec % 60:02d}"


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main(path):
    data = load(path)
    meta = data.get("meta", {})
    events = data.get("events", [])
    if not events:
        print("events 为空，无法生成时间轴")
        return 1

    events = sorted(events, key=lambda e: e.get("time_sec", 0))
    target = meta.get("target_duration_sec")
    last_t = events[-1].get("time_sec", 0)

    print("=" * 64)
    print(f"作品：{meta.get('title', '')}  （{meta.get('episode', '')}）")
    print(f"题材：{meta.get('horror_type', '')}  目标时长：{target}s  脚本末事件：{fmt_time(last_t)}({last_t}s)")
    print("=" * 64)

    # ---- 时间轴 ----
    print("\n【时间轴】")
    for e in events:
        t = fmt_time(e.get("time_sec", 0))
        typ = e.get("type", "?")
        window = e.get("window", "")
        if typ == "message":
            text = f"[{e.get('kind', 'text')}] {e.get('from', '')}: {e.get('content', '')}"
        elif typ in ("notification", "log"):
            text = f"{e.get('from', e.get('timestamp', ''))}：{e.get('content', '')}"
        elif typ == "title_card":
            text = f"标题卡：{e.get('title', '')} / {e.get('subtitle', '')}"
        elif typ == "scene":
            text = f"进入界面：{e.get('description', '')}"
        elif typ == "action":
            text = f"操作：{e.get('description', '')}"
        else:
            text = e.get("description", e.get("content", ""))
        sfx = f"  <音效:{e['sfx']}>" if e.get("sfx") else ""
        print(f"{t} | {typ:<11} | {window:<10} | 强度{e.get('intensity', '-')} | {text}{sfx}")

    # ---- 镜头清单（按 window 聚合）----
    print("\n【镜头清单（按界面分段）】")
    shots = []
    cur_window = None
    start = 0
    for i, e in enumerate(events):
        w = e.get("window", "未知")
        if w != cur_window:
            if cur_window is not None:
                end = e.get("time_sec", 0)
                shots.append((cur_window, start, end))
            cur_window = w
            start = e.get("time_sec", 0)
    shots.append((cur_window, start, last_t))

    for w, s, en in shots:
        count = sum(1 for e in events if e.get("window") == w)
        print(f"{w:<10} {fmt_time(s)}-{fmt_time(en)}  时长{en - s:>3}s  事件{count}条")

    # ---- 音效清单 ----
    print("\n【音效清单】")
    sfx_events = [e for e in events if e.get("sfx") or e.get("type") == "sfx"]
    if not sfx_events:
        print("（未标注音效，请在剧本中补充）")
    for e in sfx_events:
        name = e.get("sfx", e.get("description", ""))
        print(f"{fmt_time(e.get('time_sec', 0))}  {name}")

    # ---- 统计 ----
    print("\n【统计】")
    type_counter = Counter(e.get("type") for e in events)
    for typ, n in type_counter.most_common():
        print(f"  {typ}: {n}")

    # 各界面停留时长
    dwell = defaultdict(int)
    for w, s, en in shots:
        dwell[w] += en - s
    print("  界面停留时长：", dict(dwell))

    # 强度曲线（每 30 秒取最大强度）
    print("\n【强度曲线（每30秒窗口内最大强度）】")
    bucket = defaultdict(int)
    for e in events:
        b = e.get("time_sec", 0) // 30
        bucket[b] = max(bucket[b], e.get("intensity", 0))
    for b in range((last_t // 30) + 1):
        lvl = bucket.get(b, 0)
        print(f"  {fmt_time(b * 30)}: {'#' * lvl}{lvl}")

    # ---- 提示 ----
    print("\n【提示】")
    if target:
        if abs(last_t - target) > 20:
            print(f"  脚本末事件({last_t}s)与目标时长({target}s)差距较大，请增减消息或调整节奏。")
        else:
            print("  脚本时长与目标基本吻合。")
    if len(sfx_events) < 3:
        print("  音效点偏少，检查是否需要补充界面音与至少一次高潮突发声。")
    if not any(e.get("type") == "title_card" for e in events):
        print("  缺少结尾标题卡。")
    # 检查时间戳是否单调
    times = [e.get("time_sec", 0) for e in events]
    if times != sorted(times):
        print("  存在时间未按顺序排列的事件，已自动排序，请核对。")

    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python timeline_builder.py <message_flow.json>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))

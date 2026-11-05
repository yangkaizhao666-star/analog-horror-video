# -*- coding: utf-8 -*-
"""生成模拟恐怖中的"乱码异化"文本与刷屏串。

三种模式：
  garble  编码错位（UTF-8 字节被按 GBK 错误解码，还原原片"闃垮Ж灏卞湪"质感）
  rare    生僻字/异体字随机堆砌（信息系统崩坏、无法辨认）
  spam    把短串重复 N 次，模拟整屏刷屏攻击

用法:
  python garble_text.py garble "阿姨就在你门口"
  python garble_text.py rare --length 20
  python garble_text.py spam "绫夌绡" --repeat 30
仅依赖 Python 标准库。
"""
import argparse
import random
import sys

# 生僻字/异体字池：字形接近常用字但怪异，肉眼难辨
RARE_CHARS = list(
    "閪埼灏卞湪浣犻棬鍙鑳戒笉紑涓嬮棬鎴戝垰瑕佷笅妤煎掑瀮鍦剧鐢垫閲屾湁浜烘墤鍑烘潵"
    "闃垮Ж鐩稿綋浜庣瓛鐩栫焊灞曟ゼ姊鐧芥紨缁撶瓑寰呰繘涓ユ儏鍐佃"
    "鏂版湪鍝堝搱鍝堝搱鍝堝搱鍝堝搱鍝堝搱鍝堝搱鍝"
)


def garble(text, mode="utf8_gbk"):
    """编码错位产生 mojibake。"""
    if mode == "utf8_gbk":
        # 经典：UTF-8 字节流被按 GBK 解码
        return text.encode("utf-8").decode("gbk", errors="ignore")
    if mode == "gbk_utf8":
        return text.encode("gbk", errors="ignore").decode("utf-8", errors="ignore")
    if mode == "utf8_latin":
        return text.encode("utf-8").decode("latin-1", errors="ignore")
    raise ValueError(f"未知模式: {mode}")


def rare(length=20, seed=None):
    """随机生僻字堆砌，模拟完全无法辨认的崩坏消息。"""
    rng = random.Random(seed)
    chars = [rng.choice(RARE_CHARS) for _ in range(length)]
    # 偶尔插入问号/标点，贴近原片"閪埼？"
    for i in rng.sample(range(length), max(1, length // 8)):
        chars[i] = rng.choice(["？", "。", "…"])
    return "".join(chars)


def spam(token, repeat=30):
    """短串重复刷屏，填满消息区。"""
    return token * repeat


def main(argv=None):
    parser = argparse.ArgumentParser(description="模拟恐怖乱码/刷屏文本生成")
    sub = parser.add_subparsers(dest="command", required=True)

    p_g = sub.add_parser("garble", help="编码错位")
    p_g.add_argument("text")
    p_g.add_argument("--mode", default="utf8_gbk",
                     choices=["utf8_gbk", "gbk_utf8", "utf8_latin"])

    p_r = sub.add_parser("rare", help="生僻字堆砌")
    p_r.add_argument("--length", type=int, default=20)
    p_r.add_argument("--seed", type=int, default=None)

    p_s = sub.add_parser("spam", help="重复刷屏")
    p_s.add_argument("token")
    p_s.add_argument("--repeat", type=int, default=30)

    args = parser.parse_args(argv)
    if args.command == "garble":
        print(garble(args.text, args.mode))
    elif args.command == "rare":
        print(rare(args.length, args.seed))
    elif args.command == "spam":
        print(spam(args.token, args.repeat))
    return 0


if __name__ == "__main__":
    sys.exit(main())

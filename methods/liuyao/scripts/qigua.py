#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""六爻（京房纳甲）摇卦排盘（零第三方依赖，仅标准库）。

支持两种起卦方式：
1. 报数起卦法：给三个数字 a、b、c，取余定上卦、下卦、动爻。
2. 摇钱法：给六次摇卦结果（从初爻到上爻），每次用三枚铜钱摇出的
   "字"（有文字的一面，记为阳面）出现的枚数（0-3）表示：
     0 枚字（即三背）= 老阳，阳爻，动（变阴）
     1 枚字（即两背一字）= 少阳，阳爻，不动
     2 枚字（即两字一背）= 少阴，阴爻，不动
     3 枚字（即三字）= 老阴，阴爻，动（变阳）
   也可以直接传"老阳"/"少阳"/"少阴"/"老阴"四个词代替数字。

算法锚点（供 QA 对照，均已与常见京房纳甲资料交叉核对）
---------------------------------------------------
1. 纳甲：乾内卦（甲子、甲寅、甲辰）/外卦（壬午、壬申、壬戌）；
   坤内卦（乙未、乙巳、乙卯）/外卦（癸丑、癸亥、癸酉）。
   其余六卦内外用同一天干，见 GAN_SAME。地支起法见 ZHI_START，
   阳卦（乾坎艮震）顺行隔位、阴卦（巽离坤兑）逆行隔位。

2. 八宫卦变：本宫卦（自重）→一世（初爻变）→二世（第二爻再变）→
   三世（第三爻再变）→四世（第四爻再变）→五世（第五爻再变）→
   游魂（五世卦第四爻再变回）→归魂（游魂卦下卦换回本宫下卦）。
   乾宫锚点：乾为天、天风姤、天山遯、天地否、风地观、山地剥、
   火地晋、火天大有。

3. 世应：一世 1-4，二世 2-5，三世 3-6，四世 4-1，五世 5-2，
   本宫（六世/八纯）6-3，游魂 4-1，归魂 3-6。

4. 六亲：以本卦所属宫的五行为"我"，比较每一爻纳甲地支的五行：
   生我者父母、我生者子孙、克我者官鬼、我克者妻财、同我者兄弟。
   锚点（乾宫，我=金）：子水→子孙，寅木→妻财，辰土→父母，
   午火→官鬼，申金→兄弟，戌土→父母。

5. 六神：以起卦当日日干定初爻六神，顺序青龙、朱雀、勾陈、螣蛇、
   白虎、玄武，从初爻到上爻依次排列。甲乙起青龙；丙丁起朱雀；
   戊起勾陈；己起螣蛇；庚辛起白虎；壬癸起玄武。

6. 报数起卦：上卦 = ((a-1) % 8) + 1 对应卦；下卦 = ((b-1) % 8) + 1
   对应卦；动爻 = ((a+b+c-1) % 6) + 1（从初爻数起）。
   八卦序号：1 乾 2 兑 3 离 4 震 5 巽 6 坎 7 艮 8 坤。

7. 日干支：用公历儒略日（JDN）推六十甲子，与 methods/bazi/scripts/
   pai_pan.py 用同一锚点公式（1990-05-15 = 庚辰），但在本脚本内
   自包含实现，不依赖 bazi 模块，避免跨目录耦合。
"""

import argparse
import sys
from datetime import date

# ---------------------------------------------------------------------------
# 基础常量
# ---------------------------------------------------------------------------

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

# 八卦三爻（从下到上，1=阳，0=阴）
TRIGRAMS = {
    "乾": (1, 1, 1),
    "兑": (1, 1, 0),
    "离": (1, 0, 1),
    "震": (1, 0, 0),
    "巽": (0, 1, 1),
    "坎": (0, 1, 0),
    "艮": (0, 0, 1),
    "坤": (0, 0, 0),
}
TRIGRAM_BY_LINES = {lines: name for name, lines in TRIGRAMS.items()}

TRIGRAM_WUXING = {
    "乾": "金", "兑": "金",
    "离": "火",
    "震": "木", "巽": "木",
    "坎": "水",
    "艮": "土", "坤": "土",
}

# 纳干：内卦（下卦）/外卦（上卦）。除乾坤外，八卦内外纳同一个干。
GAN_INNER = {"乾": "甲", "坎": "戊", "艮": "丙", "震": "庚", "巽": "辛", "离": "己", "坤": "乙", "兑": "丁"}
GAN_OUTER = {"乾": "壬", "坎": "戊", "艮": "丙", "震": "庚", "巽": "辛", "离": "己", "坤": "癸", "兑": "丁"}

# 起支：内卦（下卦）/外卦（上卦）起始地支，以及顺逆方向。
# 阳卦（乾坎艮震）顺行；阴卦（巽离坤兑）逆行。
ZHI_INNER_START = {"乾": "子", "坎": "寅", "艮": "辰", "震": "子", "巽": "丑", "离": "卯", "坤": "未", "兑": "巳"}
ZHI_OUTER_START = {"乾": "午", "坎": "申", "艮": "戌", "震": "午", "巽": "未", "离": "酉", "坤": "丑", "兑": "亥"}
DIRECTION = {"乾": "顺", "坎": "顺", "艮": "顺", "震": "顺", "巽": "逆", "离": "逆", "坤": "逆", "兑": "逆"}

# 地支五行
ZHI_WUXING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

# 五行生克顺序：木生火、火生土、土生金、金生水、水生木；
# 隔一位相克：木克土、火克金、土克水、金克木、水克火。
WUXING5 = ["木", "火", "土", "金", "水"]
LIUQIN_BY_OFFSET = {0: "兄弟", 1: "子孙", 2: "妻财", 3: "官鬼", 4: "父母"}

# 八宫顺序与每宫 8 卦的传统卦名（本宫、一世、二世、三世、四世、五世、游魂、归魂）
GONG_ORDER = ["乾", "坎", "艮", "震", "巽", "离", "坤", "兑"]
SHIDAI_SEQUENCE = ["本宫", "一世", "二世", "三世", "四世", "五世", "游魂", "归魂"]
PALACE_GUA_NAMES = {
    "乾": ["乾为天", "天风姤", "天山遯", "天地否", "风地观", "山地剥", "火地晋", "火天大有"],
    "坎": ["坎为水", "水泽节", "水雷屯", "水火既济", "泽火革", "雷火丰", "地火明夷", "地水师"],
    "艮": ["艮为山", "山火贲", "山天大畜", "山泽损", "火泽睽", "天泽履", "风泽中孚", "风山渐"],
    "震": ["震为雷", "雷地豫", "雷水解", "雷风恒", "地风升", "水风井", "泽风大过", "泽雷随"],
    "巽": ["巽为风", "风天小畜", "风火家人", "风雷益", "天雷无妄", "火雷噬嗑", "山雷颐", "山风蛊"],
    "离": ["离为火", "火山旅", "火风鼎", "火水未济", "山水蒙", "风水涣", "天水讼", "天火同人"],
    "坤": ["坤为地", "地雷复", "地泽临", "地天泰", "雷天大壮", "泽天夬", "水天需", "水地比"],
    "兑": ["兑为泽", "泽水困", "泽地萃", "泽山咸", "水山蹇", "地山谦", "雷山小过", "雷泽归妹"],
}

# 世应爻位（1=初爻…6=上爻）
SHI_YING_POS = {
    "一世": (1, 4),
    "二世": (2, 5),
    "三世": (3, 6),
    "四世": (4, 1),
    "五世": (5, 2),
    "本宫": (6, 3),
    "游魂": (4, 1),
    "归魂": (3, 6),
}

# 报数起卦法：八卦序号表
BAGUA_NUM = {1: "乾", 2: "兑", 3: "离", 4: "震", 5: "巽", 6: "坎", 7: "艮", 8: "坤"}

# 六神
SIX_SPIRITS = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
SPIRIT_START_BY_GAN = {
    "甲": 0, "乙": 0,
    "丙": 1, "丁": 1,
    "戊": 2,
    "己": 3,
    "庚": 4, "辛": 4,
    "壬": 5, "癸": 5,
}

# 摇钱法：三枚铜钱中"字"面（有文字的一面，记为阳面）出现的枚数 -> (现在阴阳, 是否动爻, 名称)
# 0 枚字（三背）= 老阳，动；1 枚字（两背一字）= 少阳，不动；
# 2 枚字（两字一背）= 少阴，不动；3 枚字（三字）= 老阴，动。
COIN_INFO = {
    0: (1, True, "老阳"),
    1: (1, False, "少阳"),
    2: (0, False, "少阴"),
    3: (0, True, "老阴"),
}
COIN_WORDS = {"老阳": 0, "少阳": 1, "少阴": 2, "老阴": 3}

YAO_POS_NAME = {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}

YANG_LINE = "▅▅▅▅▅▅▅"
YIN_LINE = "▅▅▅　▅▅▅"


# ---------------------------------------------------------------------------
# 六十甲子日干支（自包含，不依赖 methods/bazi 模块）
# ---------------------------------------------------------------------------

def jdn(year, month, day):
    """格里历儒略日数（中午，整数）。与 methods/bazi/scripts/pai_pan.py 同一公式。"""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def day_gz_index(year, month, day):
    """日柱序号。锚点 1990-05-15 = 16（庚辰），与 pai_pan.py 一致。"""
    return (jdn(year, month, day) + 49) % 60


def day_ganzhi(d):
    """公历 date -> (日干, 日支)。"""
    idx = day_gz_index(d.year, d.month, d.day)
    return GAN[idx % 10], ZHI[idx % 12]


# ---------------------------------------------------------------------------
# 八宫六十四卦表
# ---------------------------------------------------------------------------

def _build_gua_table():
    table = {}
    for gong in GONG_ORDER:
        base = TRIGRAMS[gong]
        lines = list(base) + list(base)  # 本宫卦：上下同一卦
        seq_lines = [tuple(lines)]
        lines = list(lines)
        lines[0] ^= 1
        seq_lines.append(tuple(lines))  # 一世
        lines[1] ^= 1
        seq_lines.append(tuple(lines))  # 二世
        lines[2] ^= 1
        seq_lines.append(tuple(lines))  # 三世
        lines[3] ^= 1
        seq_lines.append(tuple(lines))  # 四世
        lines[4] ^= 1
        seq_lines.append(tuple(lines))  # 五世
        lines[3] ^= 1
        seq_lines.append(tuple(lines))  # 游魂：五世卦第四爻再变回
        final = list(lines)
        final[0:3] = list(base)
        seq_lines.append(tuple(final))  # 归魂：下卦换回本宫下卦

        for shidai, six, name in zip(SHIDAI_SEQUENCE, seq_lines, PALACE_GUA_NAMES[gong]):
            upper = six[3:6]
            lower = six[0:3]
            key = (upper, lower)
            table[key] = {"gong": gong, "shidai": shidai, "name": name, "lines": six}
    return table


GUA_TABLE = _build_gua_table()


# ---------------------------------------------------------------------------
# 纳甲 / 六亲 / 六神
# ---------------------------------------------------------------------------

def _zhi_index_after_steps(start_zhi, direction, steps):
    start_idx = ZHI.index(start_zhi)
    if direction == "顺":
        return (start_idx + 2 * steps) % 12
    return (start_idx - 2 * steps) % 12


def najia_liuyao(lower_name, upper_name):
    """返回六爻（初爻到上爻）纳甲 (干, 支) 列表。"""
    result = []
    gan_lower = GAN_INNER[lower_name]
    dir_lower = DIRECTION[lower_name]
    start_lower = ZHI_INNER_START[lower_name]
    for i in range(3):
        zhi = ZHI[_zhi_index_after_steps(start_lower, dir_lower, i)]
        result.append((gan_lower, zhi))

    gan_upper = GAN_OUTER[upper_name]
    dir_upper = DIRECTION[upper_name]
    start_upper = ZHI_OUTER_START[upper_name]
    for i in range(3):
        zhi = ZHI[_zhi_index_after_steps(start_upper, dir_upper, i)]
        result.append((gan_upper, zhi))
    return result


def liuqin_relation(gong_wuxing, zhi_wuxing):
    """以宫五行为"我"：生我者父母、我生者子孙、克我者官鬼、我克者妻财、同我者兄弟。"""
    mi = WUXING5.index(gong_wuxing)
    oi = WUXING5.index(zhi_wuxing)
    offset = (oi - mi) % 5
    return LIUQIN_BY_OFFSET[offset]


def six_spirits_for_day(day_gan):
    """从初爻到上爻的六神列表。"""
    start = SPIRIT_START_BY_GAN[day_gan]
    return [SIX_SPIRITS[(start + i) % 6] for i in range(6)]


def build_hexagram(lines6):
    """lines6: 6 元组（初爻到上爻，1=阳，0=阴）-> 完整卦信息 dict。"""
    lower = tuple(lines6[0:3])
    upper = tuple(lines6[3:6])
    info = GUA_TABLE[(upper, lower)]
    gong = info["gong"]
    shidai = info["shidai"]
    gong_wx = TRIGRAM_WUXING[gong]
    lower_name = TRIGRAM_BY_LINES[lower]
    upper_name = TRIGRAM_BY_LINES[upper]
    najia = najia_liuyao(lower_name, upper_name)
    liuqin = [liuqin_relation(gong_wx, ZHI_WUXING[zhi]) for _gan, zhi in najia]
    shi_pos, ying_pos = SHI_YING_POS[shidai]
    return {
        "lines": tuple(lines6),
        "name": info["name"],
        "gong": gong,
        "gong_wuxing": gong_wx,
        "shidai": shidai,
        "lower_name": lower_name,
        "upper_name": upper_name,
        "najia": najia,
        "liuqin": liuqin,
        "shi_pos": shi_pos,
        "ying_pos": ying_pos,
    }


# ---------------------------------------------------------------------------
# 两种起卦方式
# ---------------------------------------------------------------------------

def qigua_by_numbers(a, b, c):
    """报数起卦法。返回 (ben_lines, moving_positions, detail dict)。"""
    upper_num = ((a - 1) % 8) + 1
    lower_num = ((b - 1) % 8) + 1
    moving_pos = ((a + b + c - 1) % 6) + 1
    upper_name = BAGUA_NUM[upper_num]
    lower_name = BAGUA_NUM[lower_num]
    ben_lines = tuple(list(TRIGRAMS[lower_name]) + list(TRIGRAMS[upper_name]))
    detail = {
        "a": a, "b": b, "c": c,
        "upper_num": upper_num, "lower_num": lower_num,
        "upper_name": upper_name, "lower_name": lower_name,
        "moving_pos": moving_pos,
    }
    return ben_lines, {moving_pos}, detail


def qigua_by_coins(counts):
    """摇钱法。counts: 6 个 0-3 的整数（初爻到上爻）。"""
    ben_lines = tuple(COIN_INFO[c][0] for c in counts)
    moving_positions = {i + 1 for i, c in enumerate(counts) if COIN_INFO[c][1]}
    labels = [COIN_INFO[c][2] for c in counts]
    return ben_lines, moving_positions, {"counts": counts, "labels": labels}


def apply_moving(ben_lines, moving_positions):
    bian = list(ben_lines)
    for pos in moving_positions:
        bian[pos - 1] ^= 1
    return tuple(bian)


# ---------------------------------------------------------------------------
# 报告输出
# ---------------------------------------------------------------------------

def _shidai_label(shidai):
    if shidai == "本宫":
        return "本宫卦（六世/八纯）"
    return shidai + "卦"


def _hexagram_table(hexagram, moving_positions, spirits=None, show_shi_ying=True):
    lines = []
    header = ["爻位"]
    if spirits is not None:
        header.append("六神")
    if show_shi_ying:
        header.append("世应")
    header += ["卦画", "纳甲", "五行", "六亲", "动爻"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "---|" * len(header))

    for pos in range(6, 0, -1):
        idx = pos - 1
        row = [YAO_POS_NAME[pos]]
        if spirits is not None:
            row.append(spirits[idx])
        if show_shi_ying:
            mark = []
            if pos == hexagram["shi_pos"]:
                mark.append("世")
            if pos == hexagram["ying_pos"]:
                mark.append("应")
            row.append("、".join(mark) if mark else "")
        row.append(YANG_LINE if hexagram["lines"][idx] == 1 else YIN_LINE)
        gan, zhi = hexagram["najia"][idx]
        row.append(gan + zhi)
        row.append(ZHI_WUXING[zhi])
        row.append(hexagram["liuqin"][idx])
        row.append("●动" if pos in moving_positions else "")
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def format_report(result):
    lines = []
    lines.append("## 输入")
    lines.append("- 起卦方式：%s" % result["mode_label"])
    lines.extend(result["input_lines"])
    lines.append("- 起卦日期：%s（日干支：%s）" % (result["date_text"], result["day_gz"]))
    if result.get("question"):
        lines.append("- 所问之事：%s" % result["question"])
    lines.append("")

    ben = result["ben"]
    lines.append("## 本卦")
    lines.append("- 卦名：%s（%s宫 %s）" % (ben["name"], ben["gong"], _shidai_label(ben["shidai"])))
    lines.append("- 卦宫五行：%s（%s）" % (ben["gong"], ben["gong_wuxing"]))
    lines.append("- 六亲以宫五行为「我」：生我者父母、我生者子孙、克我者官鬼、我克者妻财、同我者兄弟")
    lines.append("- 世爻：第%d爻（%s）　应爻：第%d爻（%s）" % (
        ben["shi_pos"], YAO_POS_NAME[ben["shi_pos"]], ben["ying_pos"], YAO_POS_NAME[ben["ying_pos"]]
    ))
    lines.append("- 动爻数：%d" % len(result["moving_positions"]))
    lines.append("")
    lines.append(_hexagram_table(ben, result["moving_positions"], spirits=result["spirits"], show_shi_ying=True))
    lines.append("")

    lines.append("## 变卦")
    if result["bian"] is None:
        lines.append("- 六爻全静，无动爻，不生变卦。分析时以本卦世应生克关系为主要参考。")
    else:
        bian = result["bian"]
        lines.append("- 动爻：%s" % "、".join(
            "第%d爻（%s）" % (p, YAO_POS_NAME[p]) for p in sorted(result["moving_positions"])
        ))
        lines.append("- 卦名：%s（%s宫 %s）" % (bian["name"], bian["gong"], _shidai_label(bian["shidai"])))
        lines.append("- 卦宫五行：%s（%s）" % (bian["gong"], bian["gong_wuxing"]))
        lines.append(
            "- 说明：变卦六亲按变卦自身所属宫的五行重新计算（六亲是六十四卦各自固有的属性），"
            "世应、六神仍以本卦为准，变卦仅供比较动爻前后的五行生克变化（回头生/回头克/化进/化退等）。"
        )
        lines.append("")
        lines.append(_hexagram_table(bian, result["moving_positions"], spirits=None, show_shi_ying=False))
    lines.append("")

    lines.append("## 警告")
    if result["warnings"]:
        for w in result["warnings"]:
            lines.append("- %s" % w)
    else:
        lines.append("- 无")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_iso_date(text):
    try:
        parts = text.split("-")
        if len(parts) != 3:
            raise ValueError
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        return date(y, m, d)
    except ValueError:
        raise argparse.ArgumentTypeError("--date 需要 YYYY-MM-DD，收到 %r" % text)


def parse_coin_token(text):
    if text in COIN_WORDS:
        return COIN_WORDS[text]
    try:
        v = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "--coins 每项需要 0-3 的整数或 老阳/少阳/少阴/老阴，收到 %r" % text
        )
    if v not in (0, 1, 2, 3):
        raise argparse.ArgumentTypeError("--coins 每项需要 0-3 之间的整数，收到 %r" % text)
    return v


def build_parser():
    p = argparse.ArgumentParser(description="六爻（京房纳甲）摇卦排盘（无第三方依赖）")
    p.add_argument(
        "--numbers", nargs=3, type=int, metavar=("A", "B", "C"),
        help="报数起卦法：三个数字，依次决定上卦、下卦、动爻",
    )
    p.add_argument(
        "--coins", nargs=6, type=parse_coin_token,
        metavar=("Y1", "Y2", "Y3", "Y4", "Y5", "Y6"),
        help=(
            "摇钱法：从初爻到上爻，每次填三枚铜钱中「字」面（有文字的一面，记为阳面）出现的枚数"
            "（0=三背=老阳动，1=两背一字=少阳，2=两字一背=少阴，3=三字=老阴动），"
            "也可以直接填 老阳/少阳/少阴/老阴"
        ),
    )
    p.add_argument("--date", type=parse_iso_date, help="起卦公历日期 YYYY-MM-DD，默认当天")
    p.add_argument("--question", help="所问之事（可选，仅用于展示）")
    return p


def run(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.numbers and not args.coins:
        parser.error("必须提供 --numbers 或 --coins 其中一种起卦方式")
    if args.numbers and args.coins:
        parser.error("--numbers 与 --coins 互斥，只能用一种起卦方式")

    cast_date = args.date if args.date else date.today()
    day_gan, day_zhi = day_ganzhi(cast_date)
    spirits = six_spirits_for_day(day_gan)

    warnings = []
    input_lines = []

    if args.numbers:
        a, b, c = args.numbers
        ben_lines, moving_positions, detail = qigua_by_numbers(a, b, c)
        mode_label = "报数起卦法"
        input_lines.append("- 报数：a=%d, b=%d, c=%d" % (a, b, c))
        input_lines.append(
            "- 上卦取数：((%d-1) %% 8) + 1 = %d → %s；下卦取数：((%d-1) %% 8) + 1 = %d → %s"
            % (a, detail["upper_num"], detail["upper_name"], b, detail["lower_num"], detail["lower_name"])
        )
        input_lines.append(
            "- 动爻：((%d+%d+%d-1) %% 6) + 1 = 第%d爻" % (a, b, c, detail["moving_pos"])
        )
    else:
        counts = args.coins
        ben_lines, moving_positions, detail = qigua_by_coins(counts)
        mode_label = "摇钱法"
        input_lines.append(
            "- 约定：三枚铜钱以有文字的一面为「字」（阳面）、无字的一面为「背」（阴面）；"
            "三背=老阳(动)，两背一字=少阳，两字一背=少阴，三字=老阴(动)"
        )
        for i, label in enumerate(detail["labels"], start=1):
            input_lines.append("- 第%d次摇卦（%s）：%s" % (i, YAO_POS_NAME[i], label))

    ben = build_hexagram(ben_lines)

    bian = None
    if moving_positions:
        bian_lines = apply_moving(ben_lines, moving_positions)
        bian = build_hexagram(bian_lines)
    else:
        warnings.append("六爻全静（无动爻），请参考 methods/liuyao/references/liuqin-yongshen.md 中「六爻全静」的分析角度")

    if len(moving_positions) >= 4:
        warnings.append("动爻数达到%d条，超过3条时的取用请参考 GUIDE.md 边界情况表" % len(moving_positions))

    result = {
        "mode_label": mode_label,
        "input_lines": input_lines,
        "date_text": "%04d-%02d-%02d" % (cast_date.year, cast_date.month, cast_date.day),
        "day_gz": day_gan + day_zhi,
        "question": args.question,
        "ben": ben,
        "bian": bian,
        "moving_positions": moving_positions,
        "spirits": spirits,
        "warnings": warnings,
    }

    report = format_report(result)
    sys.stdout.write(report)
    if not report.endswith("\n"):
        sys.stdout.write("\n")
    return 0


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()

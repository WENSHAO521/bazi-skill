#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""紫微斗数排盘（零第三方依赖，仅标准库）。

本脚本只接受**农历**生日（年/月/日/是否闰月）+ 时辰 + 性别，不做阳历/农历互转。
若用户只有阳历生日，请先跑 methods/bazi/scripts/pai_pan.py --solar ... 拿 stdout
里的「农历」字段换算成 --lunar 参数，再跑本脚本（见 methods/ziwei/GUIDE.md）。

算法锚点（供 QA 对照，来源与置信度见 methods/ziwei/references/anxing-guize.md）
-------------------------------------------------------------------------
1. 命宫身宫：寅起正月，顺数至生月，逆数生时为命宫；顺数生时为身宫。
2. 命宫天干：五虎遁（甲己丙作首、乙庚戊为头、丙辛庚上、丁壬壬位、戊癸甲寅）。
3. 五行局：命宫干支纳音取数法（甲乙丙丁戊己庚辛壬癸→1122334455，
   子丑午未→1，寅卯申酉→2，辰巳戌亥→3；干支数相加，大于5减5，
   1木三局 2金四局 3水二局 4火六局 5土五局）。
   例：命宫壬午 → 壬5+午1=6→1 → 木三局。
4. 安紫微星诀：局数除农历生日，累加偏移直到整除；商数（模12）减一为起点，
   偏移量为偶数则顺加、奇数则逆减。
   例一：27日 木三局 → 27÷3整除（偏移0），商9，起点戌，戌不动 → 紫微在戌。
   例二：13日 火六局 → 18÷6整除（偏移5，奇），商3，起点辰，逆5步 → 紫微在亥。
   例三：6日  土五局 → 10÷5整除（偏移4，偶），商2，起点卯，顺4步 → 紫微在未。
5. 十四主星：
   紫微系（起点起，逆推）：紫微、天机、空一宫、太阳、武曲、天同、空二宫、廉贞。
   天府系（起点起，顺推）：天府、太阴、贪狼、巨门、天相、天梁、七杀、空三宫、破军。
   天府恒与紫微相冲（十二宫数值上互补：紫微偏移 + 天府偏移 = 12）。
6. 四化：按生年天干查禄/权/科/忌对照表（甲廉破武阳……癸破巨阴贪）。
7. 六吉：天魁天钺（年干）、左辅右弼（生月，辰顺戌逆）、文昌文曲（生时，戌逆辰顺）。
   六煞：擎羊陀罗（年干查禄存，禄前一位擎羊、禄后一位陀罗）、
        火星铃星（年支四组起点+生时顺数）、地空地劫（亥起，生时逆/顺数）。

交叉验证：以上规则均已用公开的开源实现（SylarLong/iztro，MIT 协议）与至少一个
独立网络来源核对，并用其中的书面数字例子在本脚本内重新推算过一遍，结果一致。
命宫/身宫/五行局另有一条独立可核对的公开测试数据（见 test_pai_pan_ziwei.py）。

已知的流派差异（本脚本采用较通行的一种说法，已在 references/anxing-guize.md 注明）：
- 闰月归属：本脚本采用「闰月前15天算本月、16日起算下月」的折中处理；
  也有门派整月按农历月份数直接处理，不做减半拆分。
- 火星铃星安法在个别门派间偏移一两步的说法也有流传，本脚本采用较通行的一种。
"""

import argparse
import sys

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
ZHI_LIST = list(ZHI)

# 五虎遁：年干 -> 寅宫天干（正月天干）
TIGER_RULE = {
    "甲": "丙", "己": "丙",
    "乙": "戊", "庚": "戊",
    "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬",
    "戊": "甲", "癸": "甲",
}

# 十干禄（禄存所在地支），按年干查
LU_ZHI = {
    "甲": "寅", "乙": "卯",
    "丙": "巳", "戊": "巳",
    "丁": "午", "己": "午",
    "庚": "申", "辛": "酉",
    "壬": "亥", "癸": "子",
}

# 天魁天钺（年干查两个地支）
KUI_YUE = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"),
    "辛": ("午", "寅"),
    "丙": ("亥", "酉"), "丁": ("亥", "酉"),
    "壬": ("卯", "巳"), "癸": ("卯", "巳"),
}

# 火星铃星起子时的地支（按年支分四组：值=(火星起点, 铃星起点)）
HUO_LING_START = {}
for _z in "寅午戌":
    HUO_LING_START[_z] = ("丑", "卯")
for _z in "申子辰":
    HUO_LING_START[_z] = ("寅", "戌")
for _z in "巳酉丑":
    HUO_LING_START[_z] = ("卯", "戌")
for _z in "亥卯未":
    HUO_LING_START[_z] = ("酉", "戌")

# 四化：生年干 -> (化禄, 化权, 化科, 化忌)
SIHUA = {
    "甲": ("廉贞", "破军", "武曲", "太阳"),
    "乙": ("天机", "天梁", "紫微", "太阴"),
    "丙": ("天同", "天机", "文昌", "廉贞"),
    "丁": ("太阴", "天同", "天机", "巨门"),
    "戊": ("贪狼", "太阴", "右弼", "天机"),
    "己": ("武曲", "贪狼", "天梁", "文曲"),
    "庚": ("太阳", "武曲", "太阴", "天同"),
    "辛": ("巨门", "太阳", "文曲", "文昌"),
    "壬": ("天梁", "紫微", "左辅", "武曲"),
    "癸": ("破军", "巨门", "太阴", "贪狼"),
}
SIHUA_LABELS = ("化禄", "化权", "化科", "化忌")

# 紫微星系：起点为 i=0，逐格逆推（数组下标即偏移量）
ZIWEI_GROUP = ["紫微", "天机", "", "太阳", "武曲", "天同", "", "", "廉贞"]
# 天府星系：起点为 i=0，逐格顺推
TIANFU_GROUP = ["天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "", "", "", "破军"]

# 十二宫名称，从命宫起（此方向与紫微星系推星方向一致）
PALACE_NAMES = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄", "迁移", "交友", "官禄", "田宅", "福德", "父母"]

FIVE_ELEMENTS_JU = {
    1: ("木", 3, "木三局"),
    2: ("金", 4, "金四局"),
    3: ("水", 2, "水二局"),
    4: ("火", 6, "火六局"),
    5: ("土", 5, "土五局"),
}

LUNAR_MONTH_NAMES = {
    1: "正月", 2: "二月", 3: "三月", 4: "四月", 5: "五月", 6: "六月",
    7: "七月", 8: "八月", 9: "九月", 10: "十月", 11: "十一月", 12: "十二月",
}
LUNAR_DAY_NAMES = {
    1: "初一", 2: "初二", 3: "初三", 4: "初四", 5: "初五", 6: "初六", 7: "初七",
    8: "初八", 9: "初九", 10: "初十", 11: "十一", 12: "十二", 13: "十三", 14: "十四",
    15: "十五", 16: "十六", 17: "十七", 18: "十八", 19: "十九", 20: "二十",
    21: "廿一", 22: "廿二", 23: "廿三", 24: "廿四", 25: "廿五", 26: "廿六",
    27: "廿七", 28: "廿八", 29: "廿九", 30: "三十",
}


# ---------------------------------------------------------------------------
# 基础换算：寅=0 的「相对宫位序号」与地支互转
# ---------------------------------------------------------------------------

def rel_of_zhi(zhi):
    """地支 -> 相对宫位序号（以寅=0，顺数为正方向，即地支表原顺序）。"""
    return (ZHI.index(zhi) - 2) % 12


def zhi_of_rel(rel):
    return ZHI[(rel + 2) % 12]


def gan_of_rel(year_gan, rel):
    """五虎遁展开：给定寅宫天干起点，任意宫位序号对应的天干（十干循环）。"""
    start = TIGER_RULE[year_gan]
    return GAN[(GAN.index(start) + rel) % 10]


def ganzhi_of_year(year):
    """农历年份 -> 生年干支（以正月初一为界，1984 年为甲子年）。"""
    idx = (int(year) - 4) % 60
    return GAN[idx % 10], ZHI[idx % 12]


# ---------------------------------------------------------------------------
# 命宫 / 身宫 / 五行局
# ---------------------------------------------------------------------------

def lunar_month_index(month, day, leap):
    """农历月 -> 0 起的月序号（正月=0）。

    闰月处理（较通行的一种做法，见模块文档「流派差异」）：
    闰月初一至十五按其本月算，十六起按下一个月算。
    """
    idx = month - 1
    if leap and day > 15:
        idx += 1
    return idx % 12


def compute_soul_body_index(month_idx, hour_idx):
    """命宫、身宫的相对宫位序号。

    寅起正月，顺数至生月 = month_idx；
    命宫：再从该月支起子时，逆数至生时 -> soul = month_idx - hour_idx。
    身宫：再从该月支起子时，顺数至生时 -> body = month_idx + hour_idx。
    """
    soul_rel = (month_idx - hour_idx) % 12
    body_rel = (month_idx + hour_idx) % 12
    return soul_rel, body_rel


def five_elements_ju(gan, zhi):
    """纳音取数法定五行局。返回 (五行, 局数字, 局名)。"""
    gan_num = GAN.index(gan) // 2 + 1
    zhi_num = (ZHI.index(zhi) % 6) // 2 + 1
    idx = gan_num + zhi_num
    while idx > 5:
        idx -= 5
    return FIVE_ELEMENTS_JU[idx]


def ziwei_start_index(ju_number, lunar_day):
    """安紫微星诀：返回紫微星的相对宫位序号（0=寅）。"""
    day = int(lunar_day)
    offset = 0
    while (day + offset) % ju_number != 0:
        offset += 1
    quotient = (day + offset) // ju_number
    quotient %= 12
    rel = quotient - 1
    if offset % 2 == 0:
        rel += offset
    else:
        rel -= offset
    return rel % 12


# ---------------------------------------------------------------------------
# 星曜安放
# ---------------------------------------------------------------------------

def place_major_stars(ziwei_rel):
    """十四主星 -> {相对宫位序号: [星名, ...]}，并返回天府相对宫位序号。"""
    tianfu_rel = (12 - ziwei_rel) % 12
    stars = {}
    for i, name in enumerate(ZIWEI_GROUP):
        if name:
            r = (ziwei_rel - i) % 12
            stars.setdefault(r, []).append(name)
    for i, name in enumerate(TIANFU_GROUP):
        if name:
            r = (tianfu_rel + i) % 12
            stars.setdefault(r, []).append(name)
    return stars, tianfu_rel


def place_lucky_evil_stars(year_gan, year_zhi, month_num, hour_idx):
    """六吉六煞 -> {相对宫位序号: [星名, ...]}。"""
    stars = {}

    def add(rel, name):
        stars.setdefault(rel % 12, []).append(name)

    # 六吉
    kui_zhi, yue_zhi = KUI_YUE[year_gan]
    add(rel_of_zhi(kui_zhi), "天魁")
    add(rel_of_zhi(yue_zhi), "天钺")

    zuo_rel = rel_of_zhi("辰") + (month_num - 1)
    you_rel = rel_of_zhi("戌") - (month_num - 1)
    add(zuo_rel, "左辅")
    add(you_rel, "右弼")

    chang_rel = rel_of_zhi("戌") - hour_idx
    qu_rel = rel_of_zhi("辰") + hour_idx
    add(chang_rel, "文昌")
    add(qu_rel, "文曲")

    # 六煞
    lu_rel = rel_of_zhi(LU_ZHI[year_gan])
    add(lu_rel + 1, "擎羊")
    add(lu_rel - 1, "陀罗")

    huo_start, ling_start = HUO_LING_START[year_zhi]
    add(rel_of_zhi(huo_start) + hour_idx, "火星")
    add(rel_of_zhi(ling_start) + hour_idx, "铃星")

    hai_rel = rel_of_zhi("亥")
    add(hai_rel - hour_idx, "地空")
    add(hai_rel + hour_idx, "地劫")

    return stars


# ---------------------------------------------------------------------------
# 排盘主流程
# ---------------------------------------------------------------------------

def compute(lunar_year, lunar_month, lunar_day, leap, shichen, sex):
    warnings = []

    if not (1 <= lunar_month <= 12):
        raise ValueError("农历月份需在 1-12 之间")
    if not (1 <= lunar_day <= 30):
        raise ValueError("农历日期需在 1-30 之间")
    if shichen not in ZHI_LIST:
        raise ValueError("时辰需是十二地支之一")

    year_gan, year_zhi = ganzhi_of_year(lunar_year)
    hour_idx = ZHI.index(shichen)

    month_idx = lunar_month_index(lunar_month, lunar_day, leap)
    month_num = month_idx + 1  # 闰月折算后的月序号（1-12），用于左辅右弼
    if leap and lunar_day > 15:
        warnings.append("闰月十六日及以后，命宫/左辅右弼按下一个月计算（较通行做法，另有门派整月按本月算）")

    soul_rel, body_rel = compute_soul_body_index(month_idx, hour_idx)
    soul_gan = gan_of_rel(year_gan, soul_rel)
    soul_zhi = zhi_of_rel(soul_rel)
    body_zhi = zhi_of_rel(body_rel)

    wuxing, ju_num, ju_name = five_elements_ju(soul_gan, soul_zhi)

    ziwei_rel = ziwei_start_index(ju_num, lunar_day)
    major_stars, tianfu_rel = place_major_stars(ziwei_rel)
    minor_stars = place_lucky_evil_stars(year_gan, year_zhi, month_num, hour_idx)

    lu, quan, ke, ji = SIHUA[year_gan]
    sihua_map = {lu: "化禄", quan: "化权", ke: "化科", ji: "化忌"}

    palaces = []
    for k, pname in enumerate(PALACE_NAMES):
        rel = (soul_rel - k) % 12
        gan = gan_of_rel(year_gan, rel)
        zhi = zhi_of_rel(rel)
        majors = major_stars.get(rel, [])
        minors = minor_stars.get(rel, [])
        tags = []
        for star in majors + minors:
            if star in sihua_map:
                tags.append("%s(%s)" % (star, sihua_map[star]))
        palaces.append(
            {
                "name": pname,
                "rel": rel,
                "ganzhi": gan + zhi,
                "majors": majors,
                "minors": minors,
                "sihua": tags,
                "is_body": rel == body_rel,
            }
        )

    if body_rel == soul_rel:
        warnings.append("身宫与命宫同宫")

    body_palace_name = PALACE_NAMES[(soul_rel - body_rel) % 12]

    return {
        "lunar_year": lunar_year,
        "lunar_month": lunar_month,
        "lunar_day": lunar_day,
        "leap": leap,
        "shichen": shichen,
        "sex": sex,
        "year_ganzhi": year_gan + year_zhi,
        "soul_ganzhi": soul_gan + soul_zhi,
        "soul_zhi": soul_zhi,
        "body_zhi": body_zhi,
        "body_palace_name": body_palace_name,
        "wuxing": wuxing,
        "ju_num": ju_num,
        "ju_name": ju_name,
        "ziwei_zhi": zhi_of_rel(ziwei_rel),
        "tianfu_zhi": zhi_of_rel(tianfu_rel),
        "palaces": palaces,
        "sihua": {"化禄": lu, "化权": quan, "化科": ke, "化忌": ji},
        "warnings": warnings,
    }


def format_report(r):
    lines = []
    lines.append("## 输入")
    leap_text = "闰" if r["leap"] else ""
    lines.append(
        "- 农历：%d年%s%s%s"
        % (
            r["lunar_year"],
            leap_text,
            LUNAR_MONTH_NAMES.get(r["lunar_month"], str(r["lunar_month"]) + "月"),
            LUNAR_DAY_NAMES.get(r["lunar_day"], str(r["lunar_day"])),
        )
    )
    lines.append("- 时辰：%s" % r["shichen"])
    lines.append("- 性别：%s" % r["sex"])
    lines.append("- 生年干支：%s" % r["year_ganzhi"])
    lines.append("")

    lines.append("## 命宫与身宫")
    lines.append("- 命宫：%s（干支：%s）" % (PALACE_NAMES[0], r["soul_ganzhi"]))
    lines.append("- 身宫：落在「%s」这一宫（地支：%s）" % (r["body_palace_name"], r["body_zhi"]))
    lines.append("- 五行局：%s（%s，局数 %d）" % (r["ju_name"], r["wuxing"], r["ju_num"]))
    lines.append("- 紫微星：%s宫；天府星：%s宫" % (r["ziwei_zhi"], r["tianfu_zhi"]))
    lines.append("")

    lines.append("## 十二宫与十四主星")
    lines.append("| 宫位 | 干支 | 主星 | 六吉六煞 | 四化 | 身宫 |")
    lines.append("|---|---|---|---|---|---|")
    for p in r["palaces"]:
        majors = "、".join(p["majors"]) if p["majors"] else "—"
        minors = "、".join(p["minors"]) if p["minors"] else "—"
        sihua = "、".join(p["sihua"]) if p["sihua"] else "—"
        body_mark = "是" if p["is_body"] else ""
        lines.append(
            "| %s | %s | %s | %s | %s | %s |"
            % (p["name"], p["ganzhi"], majors, minors, sihua, body_mark)
        )
    lines.append("")

    lines.append("## 四化")
    lines.append("- 生年干：%s" % r["year_ganzhi"][0])
    for label in SIHUA_LABELS:
        lines.append("- %s：%s" % (label, r["sihua"][label]))
    lines.append("")

    lines.append("## 警告")
    if r["warnings"]:
        for w in r["warnings"]:
            lines.append("- %s" % w)
    else:
        lines.append("- 无")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_lunar_date(text):
    try:
        parts = text.split("-")
        if len(parts) != 3:
            raise ValueError
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        return y, m, d
    except ValueError:
        raise argparse.ArgumentTypeError("--lunar 需要 YYYY-MM-DD（数字），收到 %r" % text)


def build_parser():
    p = argparse.ArgumentParser(description="紫微斗数排盘（只接受农历生日，标准库无第三方依赖）")
    p.add_argument("--lunar", required=True, help="农历 YYYY-MM-DD（年-月-日，均为数字）")
    p.add_argument("--leap", action="store_true", help="农历闰月")
    p.add_argument("--shichen", required=True, choices=ZHI_LIST, help="时辰地支")
    p.add_argument("--sex", required=True, choices=("男", "女"), help="性别（必填）")
    return p


def run(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    lunar_year, lunar_month, lunar_day = parse_lunar_date(args.lunar)

    try:
        result = compute(lunar_year, lunar_month, lunar_day, args.leap, args.shichen, args.sex)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    report = format_report(result)
    sys.stdout.write(report)
    if not report.endswith("\n"):
        sys.stdout.write("\n")
    return 0


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()

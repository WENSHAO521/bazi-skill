#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""时家奇门遁甲——排局之后的九宫布局（零第三方依赖，仅标准库）。

## 重要限制（务必先读）

本脚本 **不做"排局"**（即不从阳历/农历日期自动推算"阴遁/阳遁 + 几局"）。
原因见 `methods/qimen/references/paiju-guize.md` 开头的说明：排局依赖的
"置闰法 / 拆补法 / 茅山法"等置闰定局规则，不同流派、不同软件之间存在
真实且公开承认的分歧（同一时刻，不同起局法可能算出不同局数），凭记忆或
未经充分交叉验证的实现极易得出一个"看起来很精确、实际是错的"局数，
风险远高于诚实地要求用户提供这一步的结果。

因此本脚本的入口是"阴遁/阳遁 + 局数（1-9）+ 时干支"，这三项需要用户从
权威黄历 / 万年历 App，或专业奇门排盘软件查得（搜索"某年某月某日某时
奇门遁甲局数"通常就能查到，一般会直接标注"阳遁三局""阴遁七局"之类）。
拿到这三项之后，本脚本负责的是相对机械、争议小得多的后续步骤：

1. 九宫固定方位（洛书九宫）
2. 地盘六仪三奇排布（局数决定起始宫，阳遁顺、阴遁逆）
3. 值符值使判定（旬首所在地盘宫）
4. 天盘飞布（值符随时干飞，其余八星随同一旋转量整体跟随）
5. 八门飞布（值使随同一旋转量跟随）
6. 八神排布（以值符所在宫为起点，阳遁顺、阴遁逆）

这些规则的置信度分级见 `methods/qimen/references/paiju-guize.md`。凡是
交叉核对后仍不确定、或流派间有分歧的地方，参考文件里都做了标注，不要
把本脚本的输出当成"唯一正确答案"，应结合参考文件的说明向用户说明。

算法锚点（供 QA 对照）
---------------------
1. 六仪三奇字符顺序（不因局数变化）：
   阳遁：戊己庚辛壬癸丁丙乙
   阴遁：戊乙丙丁癸壬辛庚己
   起始宫 = 局数对应的洛书宫（1~9），随后按 1→2→3→...→9 的洛书数序
   （不是空间顺时针）依次把上面 9 个字符排入 9 个宫（含中五宫）。
   锚点：阳遁一局 → 坎1=戊、坤2=己、震3=庚、巽4=辛、中5=壬、乾6=癸、
        兑7=丁、艮8=丙、离9=乙。
   锚点：阴遁一局 → 坎1=戊、坤2=乙、震3=丙、巽4=丁、中5=癸、乾6=壬、
        兑7=辛、艮8=庚、离9=己。

2. 旬首寄宫（六甲寄宫，与地支无关的固定口诀）：
   甲子旬→戊，甲戌旬→己，甲申旬→庚，甲午旬→辛，甲辰旬→壬，甲寅旬→癸。
   由时干支所在的"旬"决定用哪一个仪；该仪在地盘上所在的宫即"旬首落宫"。

3. 值符 / 值使：旬首落宫的固定本位星为值符星，固定本位门为值使门。
   若旬首落于中五宫，按"中五寄坤二"的通行说法，改用坤二宫的本位星
   （天芮，此时值符星记作"天禽"）与本位门（死门）。

4. 天盘飞布："值符随时干"——在地盘上找到本时辰"时干"所在的宫（时干
   为"甲"时，用甲所寄的仪去找，即与旬首落宫相同），值符星（连同其余
   八星、地盘六仪三奇整体）按阳遁顺时针 / 阴遁逆时针，沿固定的八宫
   环（坎艮震巽离坤兑乾，中宫不在环上）整体旋转到该宫。八门、八神
   采用同一套旋转量（八神以值符所在的最终宫位为起点）。这是"转盘"
   一派的通行简化模型，"飞盘"一派的具体机械另有不同处理，详见参考
   文件的置信度说明。

5. 八神固定顺序（阳遁阴遁共 6 个相同、2 个不同）：
   值符、螣蛇、太阴、六合、勾陈（阳）/白虎（阴）、
   朱雀（阳）/玄武（阴）、九地、九天。
"""

import argparse
import importlib.util
import os
import sys
from datetime import date

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

# ---------------------------------------------------------------------------
# 九宫（洛书）固定信息
# ---------------------------------------------------------------------------

PALACE_NAME = {
    1: "坎", 2: "坤", 3: "震", 4: "巽", 5: "中",
    6: "乾", 7: "兑", 8: "艮", 9: "离",
}
PALACE_DIR = {
    1: "北", 2: "西南", 3: "东", 4: "东南", 5: "中",
    6: "西北", 7: "西", 8: "东北", 9: "南",
}
# 3x3 网格显示布局（洛书幻方，每行/列/对角线之和为 15）
GRID = [
    [4, 9, 2],
    [3, 5, 7],
    [8, 1, 6],
]

# 地盘六仪三奇字符顺序（永远以"戊"开头；阳遁顺六仪逆三奇，阴遁逆六仪顺三奇）
YANG_ORDER = "戊己庚辛壬癸丁丙乙"
YIN_ORDER = "戊乙丙丁癸壬辛庚己"
LIUYI = set("戊己庚辛壬癸")
SANQI = set("乙丙丁")

# 九星固定本位（洛书数序 1~9 与 8 宫一一对应；中五宫本位为天禽，飞布时寄坤二宫）
FIXED_STAR = {
    1: "天蓬", 2: "天芮", 3: "天冲", 4: "天辅",
    6: "天心", 7: "天柱", 8: "天任", 9: "天英",
}
TIANQIN = "天禽"

# 八门固定本位（中五宫无门）
FIXED_DOOR = {
    1: "休门", 2: "死门", 3: "伤门", 4: "杜门",
    6: "开门", 7: "惊门", 8: "生门", 9: "景门",
}

# 八宫环（坎艮震巽离坤兑乾），阳遁方向的固定物理顺时针顺序；中宫不在环上
RING = [1, 8, 3, 4, 9, 2, 7, 6]

# 八神固定顺序；index 4、5 阳遁阴遁用词不同（其余 6 个相同）
GOD_COMMON = ["值符", "螣蛇", "太阴", "六合"]
GOD_TAIL = ["九地", "九天"]

# 旬首（六甲寄宫）：旬首地支 -> 寄宫之仪
ZHI_TO_XUN_YI = {"子": "戊", "戌": "己", "申": "庚", "午": "辛", "辰": "壬", "寅": "癸"}


# ---------------------------------------------------------------------------
# 时干支 / 旬首
# ---------------------------------------------------------------------------

def validate_ganzhi(text):
    """校验并返回 (gan, zhi)；非法组合（如甲丑）报错。"""
    if len(text) != 2 or text[0] not in GAN or text[1] not in ZHI:
        raise ValueError("时干支需要是天干+地支两个字，如“庚午”，收到 %r" % text)
    gi, zi = GAN.index(text[0]), ZHI.index(text[1])
    if gi % 2 != zi % 2:
        raise ValueError("%r 不是有效的六十甲子组合（天干地支阴阳不匹配）" % text)
    return text[0], text[1]


def ganzhi_60_index(gan, zhi):
    """(gan, zhi) -> 六十甲子序号 0~59（甲子=0），用中国剩余定理暴力枚举。"""
    gi, zi = GAN.index(gan), ZHI.index(zhi)
    for i in range(60):
        if i % 10 == gi and i % 12 == zi:
            return i
    raise ValueError("无法定位 %s%s 的六十甲子序号" % (gan, zhi))


def find_xun_yi(gan, zhi):
    """时干支 -> 旬首所寄之仪（戊己庚辛壬癸之一）。"""
    idx60 = ganzhi_60_index(gan, zhi)
    xun_start = (idx60 // 10) * 10
    xun_zhi = ZHI[xun_start % 12]
    return ZHI_TO_XUN_YI[xun_zhi], "甲" + xun_zhi


# ---------------------------------------------------------------------------
# 地盘：六仪三奇排布
# ---------------------------------------------------------------------------

def build_dipan(ju, yang):
    """局数 + 阴阳遁 -> {宫: 干}，9 个宫（含中五宫）恰好各得一个不重复的字符。"""
    if not (1 <= ju <= 9):
        raise ValueError("局数必须是 1~9，收到 %r" % ju)
    order = YANG_ORDER if yang else YIN_ORDER
    palace_seq = [((ju - 1 + k) % 9) + 1 for k in range(9)]
    dipan = dict(zip(palace_seq, order))
    return dipan


def ring_index(palace, ring):
    """宫号在指定环中的下标；中五宫按通行说法寄坤二宫，用坤二宫的下标。"""
    return ring.index(2 if palace == 5 else palace)


# ---------------------------------------------------------------------------
# 排局综合计算
# ---------------------------------------------------------------------------

def compute(yang, ju, hour_gan, hour_zhi):
    hour_ganzhi_display = hour_gan + hour_zhi
    dipan = build_dipan(ju, yang)
    gan_to_palace = {g: p for p, g in dipan.items()}

    xun_yi, xun_gz = find_xun_yi(hour_gan, hour_zhi)
    xun_gong = gan_to_palace[xun_yi]

    target_symbol = xun_yi if hour_gan == "甲" else hour_gan
    if target_symbol not in gan_to_palace:
        raise ValueError("时干 %r 未能在地盘六仪三奇中找到对应宫位（不应发生，请检查输入）" % hour_gan)
    target_gong = gan_to_palace[target_symbol]

    ring = RING if yang else list(reversed(RING))
    src_idx = ring_index(xun_gong, ring)
    tgt_idx = ring_index(target_gong, ring)
    offset = (tgt_idx - src_idx) % 8
    # 值符/值使/八神的实际落宫永远是八宫环上的宫（中五宫本身不接星/门/神，
    # 若 target_gong 恰好是中五宫，落宫按"中五寄坤二"代理到坤二宫飞到的那一宫）
    landing_gong = ring[tgt_idx]

    # 值符星 / 值使门（旬首落宫的本位星/门；中五宫寄坤二宫）
    zhifu_home = 2 if xun_gong == 5 else xun_gong
    zhifu_star = TIANQIN if xun_gong == 5 else FIXED_STAR[zhifu_home]
    zhishi_men = FIXED_DOOR[zhifu_home]

    # 天盘干：地盘 8 个外宫随环整体旋转；中五宫的干寄坤二宫一起走
    tianpan_gan = {}
    tianpan_extra = {}  # 记录中五宫寄放到的宫位 -> (中五宫干)
    for p in range(1, 10):
        if p == 5:
            continue
        ridx = ring_index(p, ring)
        new_p = ring[(ridx + offset) % 8]
        tianpan_gan[new_p] = dipan[p]
    kun_ridx = ring_index(2, ring)
    kun_new_p = ring[(kun_ridx + offset) % 8]
    tianpan_extra[kun_new_p] = dipan[5]

    # 天盘星：同上；中五宫的天禽寄坤二宫一起走
    tianpan_star = {}
    for p, star in FIXED_STAR.items():
        ridx = ring_index(p, ring)
        new_p = ring[(ridx + offset) % 8]
        tianpan_star[new_p] = star
    tianqin_new_p = kun_new_p  # 天禽随坤二宫一起飞

    # 天盘门：8 个外宫随环整体旋转
    tianpan_men = {}
    for p, men in FIXED_DOOR.items():
        ridx = ring_index(p, ring)
        new_p = ring[(ridx + offset) % 8]
        tianpan_men[new_p] = men

    # 八神：以值符最终所在宫（target_gong）为起点，阳遁顺、阴遁逆填入八宫环
    god5 = "勾陈" if yang else "白虎"
    god6 = "朱雀" if yang else "玄武"
    god_seq = GOD_COMMON + [god5, god6] + GOD_TAIL
    gods = {}
    for j in range(8):
        p = ring[(tgt_idx + j) % 8]
        gods[p] = god_seq[j]

    return {
        "dipan": dipan,
        "hour_ganzhi_display": hour_ganzhi_display,
        "xun_gz": xun_gz,
        "xun_yi": xun_yi,
        "xun_gong": xun_gong,
        "target_symbol": target_symbol,
        "target_gong": target_gong,
        "zhifu_star": zhifu_star,
        "zhishi_men": zhishi_men,
        "landing_gong": landing_gong,
        "tianpan_gan": tianpan_gan,
        "tianpan_extra": tianpan_extra,
        "tianpan_star": tianpan_star,
        "tianqin_new_p": tianqin_new_p,
        "tianpan_men": tianpan_men,
        "gods": gods,
        "offset": offset,
        "yang": yang,
        "ju": ju,
    }


# ---------------------------------------------------------------------------
# 输出格式化
# ---------------------------------------------------------------------------

def cell_text(p, r):
    lines = []
    lines.append("%d %s(%s)" % (p, PALACE_NAME[p], PALACE_DIR[p]))
    if p == 5:
        lines.append("地盘：%s（五宫，寄坤二宫，无独立天盘/门/神）" % r["dipan"][5])
        extra_p = r["tianqin_new_p"]
        lines.append("→随坤二宫飞到 %d 宫（干:%s 星:天禽）" % (extra_p, r["dipan"][5]))
        return lines
    lines.append("地盘：%s" % r["dipan"][p])
    tg = r["tianpan_gan"].get(p, "—")
    if p in r["tianpan_extra"]:
        tg = "%s / %s(寄五宫)" % (tg, r["tianpan_extra"][p])
    lines.append("天盘：%s" % tg)
    star = r["tianpan_star"].get(p, "—")
    if p == r["tianqin_new_p"]:
        star = "%s / 天禽(寄)" % star
    lines.append("星：%s" % star)
    lines.append("门：%s" % r["tianpan_men"].get(p, "—"))
    lines.append("神：%s" % r["gods"].get(p, "—"))
    marks = []
    if p == r["xun_gong"]:
        marks.append("旬首落宫(%s)" % r["xun_gz"])
    if p == r["landing_gong"]:
        marks.append("值符值使落宫")
    if marks:
        lines.append("〔%s〕" % "、".join(marks))
    return lines


def format_report(r):
    lines = []
    lines.append("## 输入")
    lines.append("- 遁：%s" % ("阳遁" if r["yang"] else "阴遁"))
    lines.append("- 局数：%d 局" % r["ju"])
    lines.append("- 时干支：%s" % r["hour_ganzhi_display"])
    lines.append("")

    lines.append("## 值符值使")
    lines.append("- 旬首：%s（寄仪：%s，落地盘 %d 宫 / %s）" % (
        r["xun_gz"], r["xun_yi"], r["xun_gong"], PALACE_NAME[r["xun_gong"]]
    ))
    lines.append("- 时干目标宫（%s）：%d 宫 / %s%s" % (
        r["target_symbol"], r["target_gong"], PALACE_NAME[r["target_gong"]],
        "（中五宫，按通行说法代理到坤二宫）" if r["target_gong"] == 5 else "",
    ))
    lines.append("- 值符星：%s → 落 %d 宫（%s）" % (r["zhifu_star"], r["landing_gong"], PALACE_NAME[r["landing_gong"]]))
    lines.append("- 值使门：%s → 落 %d 宫（%s）" % (r["zhishi_men"], r["landing_gong"], PALACE_NAME[r["landing_gong"]]))
    lines.append("- 旋转量（沿八宫环，%s）：%d 步" % ("阳遁顺" if r["yang"] else "阴遁逆", r["offset"]))
    lines.append("")

    lines.append("## 九宫布局图")
    lines.append("（三行三列，对应传统洛书方位；每格：宫号/卦名(方位)、地盘干、天盘干、星、门、神）")
    lines.append("")
    for row in GRID:
        cells = [cell_text(p, r) for p in row]
        height = max(len(c) for c in cells)
        for c in cells:
            while len(c) < height:
                c.append("")
        for i in range(height):
            lines.append(" | ".join("%-22s" % c[i] for c in cells))
        lines.append("-" * 78)
    lines.append("")

    lines.append("## 地盘六仪三奇总表")
    for p in range(1, 10):
        lines.append("- %d 宫(%s)：%s" % (p, PALACE_NAME[p], r["dipan"][p]))
    lines.append("")

    lines.append("## 警告")
    warns = []
    if r["xun_gong"] == 5:
        warns.append("旬首落于中五宫，值符星/值使门按通行说法寄坤二宫计算，请留意")
    if r["target_gong"] == 5:
        warns.append("时干目标宫落于中五宫，按通行说法寄坤二宫计算，请留意")
    if not warns:
        lines.append("- 无")
    else:
        for w in warns:
            lines.append("- %s" % w)
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# --solar/--hour 便捷入口：算时干支（优先复用 bazi 的排盘逻辑，失败则自算）
# ---------------------------------------------------------------------------

def _try_import_bazi_paipan():
    here = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.normpath(os.path.join(here, "..", "..", "bazi", "scripts", "pai_pan.py"))
    if not os.path.isfile(candidate):
        return None
    try:
        spec = importlib.util.spec_from_file_location("_qimen_bazi_pai_pan", candidate)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


def _fallback_hour_ganzhi(solar_date, hour, minute):
    """自算兜底：不依赖 bazi 模块时，用儒略日 + 五鼠遁自行推日柱/时柱。

    与 methods/bazi/scripts/pai_pan.py 采用同一锚点：
    日柱 gz_index = (JDN + 49) % 60；23:00 起算次日日柱（夜子时）。
    """
    def jdn(y, m, d):
        a = (14 - m) // 12
        yy = y + 4800 - a
        mm = m + 12 * a - 3
        return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045

    from datetime import timedelta
    used = date(solar_date.year, solar_date.month, solar_date.day)
    if hour >= 23:
        used = used + timedelta(days=1)
    idx = (jdn(used.year, used.month, used.day) + 49) % 60
    day_gan, day_zhi = GAN[idx % 10], ZHI[idx % 12]

    total = hour * 60 + minute
    if total >= 23 * 60 or total < 60:
        hour_zhi = "子"
    else:
        hour_zhi = ZHI[((hour + 1) // 2) % 12]

    zi_shi_gan = {0: 0, 5: 0, 1: 2, 6: 2, 2: 4, 7: 4, 3: 6, 8: 6, 4: 8, 9: 8}
    day_gan_i = GAN.index(day_gan)
    hour_gan_i = (zi_shi_gan[day_gan_i] + ZHI.index(hour_zhi)) % 10
    return GAN[hour_gan_i], hour_zhi


def hour_ganzhi_from_clock(solar_date, hour, minute):
    mod = _try_import_bazi_paipan()
    if mod is not None:
        try:
            result = mod.compute(solar_date=solar_date, hour=hour, minute=minute, sex="男")
            h_gan, h_zhi = result["pillars"]["hour"][0], result["pillars"]["hour"][1]
            if h_gan != "未知":
                return h_gan, h_zhi
        except Exception:
            pass
    return _fallback_hour_ganzhi(solar_date, hour, minute)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_iso_date(text, flag):
    try:
        y, m, d = (int(x) for x in text.split("-"))
        return date(y, m, d)
    except ValueError:
        raise argparse.ArgumentTypeError("%s 需要 YYYY-MM-DD，收到 %r" % (flag, text))


def parse_hour(text):
    try:
        hh, mm = text.split(":")
        h, m = int(hh), int(mm)
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError
        return h, m
    except ValueError:
        raise argparse.ArgumentTypeError("--hour 需要 HH:MM，收到 %r" % text)


def build_parser():
    p = argparse.ArgumentParser(
        description="时家奇门遁甲——已知阴阳遁+局数后的九宫布局（不做排局，见脚本顶部说明）"
    )
    dun = p.add_mutually_exclusive_group(required=True)
    dun.add_argument("--yangdun", action="store_true", help="阳遁")
    dun.add_argument("--yindun", action="store_true", help="阴遁")
    p.add_argument("--ju", type=int, required=True, help="局数 1~9（需用户从黄历/专业软件查得）")
    p.add_argument("--hour-ganzhi", dest="hour_ganzhi", help="时干支，如“庚午”；与 --solar/--hour 二选一")
    p.add_argument("--solar", help="阳历 YYYY-MM-DD（配合 --hour 自动算时干支，便捷用法）")
    p.add_argument("--hour", help="出生/起局钟点 HH:MM（北京时间），需配合 --solar")
    return p


def run(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not (1 <= args.ju <= 9):
        parser.error("--ju 必须是 1~9")

    if args.hour_ganzhi and (args.solar or args.hour):
        parser.error("--hour-ganzhi 与 --solar/--hour 互斥，二选一")
    if bool(args.solar) != bool(args.hour):
        parser.error("--solar 与 --hour 必须同时提供")
    if not args.hour_ganzhi and not args.solar:
        parser.error("必须提供 --hour-ganzhi，或同时提供 --solar 和 --hour")

    if args.hour_ganzhi:
        try:
            hour_gan, hour_zhi = validate_ganzhi(args.hour_ganzhi)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
    else:
        solar_date = parse_iso_date(args.solar, "--solar")
        hour, minute = parse_hour(args.hour)
        hour_gan, hour_zhi = hour_ganzhi_from_clock(solar_date, hour, minute)

    yang = bool(args.yangdun)
    try:
        result = compute(yang, args.ju, hour_gan, hour_zhi)
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

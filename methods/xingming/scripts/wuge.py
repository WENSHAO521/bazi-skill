#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""姓名学五格剖象法（熊崎氏姓名学）计算脚本，零第三方依赖，仅标准库。

输入：姓名各字的**康熙字典繁体笔画数**（由调用方/用户提供，本脚本不做
简繁转换、不查字典、不猜测笔画，只接受数字）。

五格计算公式（单姓/复姓 × 单名/双名 四种组合）：
    姓氏：X1（复姓再加 X2）；名字：M1（双字名再加 M2）

    单姓单名：天格=X1+1        人格=X1+M1      地格=M1+1      外格=2(固定)     总格=X1+M1
    单姓双名：天格=X1+1        人格=X1+M1      地格=M1+M2     外格=M2+1        总格=X1+M1+M2
    复姓单名：天格=X1+X2       人格=X2+M1      地格=M1+1      外格=X1+1        总格=X1+X2+M1
    复姓双名：天格=X1+X2       人格=X2+M1      地格=M1+M2     外格=X1+M2       总格=X1+X2+M1+M2

每一格数值：
    1. 若 > 81，按 ((n-1) % 81) + 1 折算到 1-81 区间再查表
    2. 五行取个位数字（10 按 0 处理）：1、2→木；3、4→火；5、6→土；7、8→金；9、0→水
    3. 查 81 数吉凶表得吉凶等级与简短释义（与 references/81-shuli.md 同一份数据）

三才：天格→人格、人格→地格 两组五行生克关系（相生/相克/比和），
这是通用生克规则，不穷举具体组合表。

详见 methods/xingming/references/wuge-suanfa.md 与 methods/xingming/references/81-shuli.md。
"""

import argparse
import sys

# ---------------------------------------------------------------------------
# 81 数吉凶表（熊崎氏姓名学通行版本，仅供文化参考）
# 与 methods/xingming/references/81-shuli.md 同一份数据，如需修改请两边同步。
# ---------------------------------------------------------------------------

SHULI = {
    1: ("大吉", "太极之数，万物开泰，头脑聪明，能获成功发展"),
    2: ("大凶", "分离破坏之数，前途暗淡，进退不安"),
    3: ("大吉", "进取如意，成功发展，名利双收"),
    4: ("大凶", "破败之象，多陷困境，万事难成"),
    5: ("大吉", "福寿圆满，阴阳和合，五行俱备"),
    6: ("大吉", "安稳余庆，吉人天相，能得先人余荫"),
    7: ("吉", "刚毅果断，独立权威，排除万难"),
    8: ("吉", "意志刚健，勤勉发展，努力不懈可成功"),
    9: ("大凶", "穷乏困苦，虽有智谋但多陷逆境"),
    10: ("大凶", "万事终局，损耗劫难，凡事难成"),
    11: ("大吉", "稳健着实，复兴家运，得内外信望"),
    12: ("凶", "意志薄弱，家庭缘薄，谋事难成"),
    13: ("大吉", "智略超群，博学多才，能成大业"),
    14: ("凶", "破兆离散，家族缘薄，浮沉不定"),
    15: ("大吉", "福寿圆满，众望所归，德高望重"),
    16: ("大吉", "贵人得助，能获众望，成就大业"),
    17: ("吉", "刚强果决，排除万难，贯彻志望"),
    18: ("吉", "铁石志坚，内外有运，功成名就"),
    19: ("凶", "风云蔽日，辛苦重来，虽有智谋多受挫折"),
    20: ("大凶", "屋下藏金（一说屋下藏尸），非业破运，灾祸重重"),
    21: ("大吉", "明月中天，官运亨通，能成首领（女性用需留意过刚）"),
    22: ("凶", "秋草逢霜，中年多疾，虽出豪杰人生多波折"),
    23: ("大吉", "旭日升天，权威旺盛，能成大业（女性用需留意过刚）"),
    24: ("大吉", "家门余庆，白手成家，财源广进"),
    25: ("吉", "资性英敏，才略奇特，需留意言行圆融"),
    26: ("凶", "波澜重叠，英雄豪杰之数，但多起伏磨难"),
    27: ("半吉半凶", "欲望无止，中年前后易生变故，宜谦和自守"),
    28: ("凶", "鸡群一鹤，遭人嫉妒排挤，离散破财之象"),
    29: ("吉", "智谋优秀，财力归集，需留意欲望过度"),
    30: ("半吉半凶", "沉浮不定，凭借侥幸，得失参半"),
    31: ("大吉", "智勇兼备，心怀慈悲，统率众人可成大业"),
    32: ("大吉", "侥幸多得，意外惠泽，多受长辈提拔"),
    33: ("大吉", "家运隆昌，才德开展（女性用需留意过旺）"),
    34: ("大凶", "破家亡身，非业破运，灾祸不断"),
    35: ("吉", "温和平静，才能秀出，宜技艺文艺发展"),
    36: ("凶", "波澜重叠，侠肝义胆但风波不断，宜谨慎"),
    37: ("大吉", "权威显达，独立自主，忠实信义可成功"),
    38: ("半吉半凶", "磨铁成针，才能平凡但坚忍不拔可有小成"),
    39: ("大吉", "富贵荣华，云开见月（成功者多经历艰辛）"),
    40: ("凶", "一盛一衰，知进不知退，多有破折"),
    41: ("大吉", "德望高尚，事事如意，统帅众人可成大业"),
    42: ("半吉半凶", "博识多能，若能专心一艺尚可有成，否则难成"),
    43: ("凶", "散财破产，外美内苦，虽有智谋财来财去"),
    44: ("大凶", "破家亡身，事不如意，多陷逆境"),
    45: ("大吉", "顺风扬帆，新生泰运，智谋深远可成大业"),
    46: ("凶", "浪里淘沙，坎坷不平，历经艰辛方有所成"),
    47: ("大吉", "点铁成金，开花结果，多得贵人相助"),
    48: ("大吉", "德智兼备，可为师表，繁荣富贵"),
    49: ("半吉半凶", "吉凶参半，遇吉则吉，遇凶则凶，关键在配合三才"),
    50: ("半吉半凶", "一成一败，先甘后苦或先苦后甘"),
    51: ("半吉半凶", "盛衰交加，一盛一衰，宜守成戒骄"),
    52: ("大吉", "先见之明，草木逢春，眼光独到可获成功"),
    53: ("半吉半凶", "外美内苦，表面风光内心多忧，宜量力而行"),
    54: ("凶", "多难非运，虽有才智但多灾多难"),
    55: ("半吉半凶", "外美内苦，盛极将衰，宜谦逊守持"),
    56: ("凶", "事与愿违，浪费心力，事倍功半"),
    57: ("吉", "寒雪梅花，先苦后甘，努力奋斗终可成功"),
    58: ("半吉半凶", "先苦后甘，历经波折终有所成"),
    59: ("凶", "遭难非运，欠缺果断，事多不如意"),
    60: ("凶", "黑暗无光，事与愿违，多陷困境"),
    61: ("吉", "名利双收，云雾晴天，家门隆昌（宜内外和睦）"),
    62: ("凶", "衰败零落，基础不稳，信用缺乏"),
    63: ("大吉", "万物化育，繁荣富贵，事事如意"),
    64: ("凶", "见异思迁，多灾多难，家族缘薄"),
    65: ("大吉", "巨流归海，福寿圆满，家运昌隆"),
    66: ("凶", "内外不和，进退两难，波乱不绝"),
    67: ("大吉", "独立权威，事事如意，功成名就"),
    68: ("吉", "思虑周密，如愿以偿，发明创造可成功"),
    69: ("凶", "动摇不安，坎坷不平，多陷逆境"),
    70: ("凶", "惨淡萧条，辛苦不绝，凶变不断"),
    71: ("半吉半凶", "吉凶参半，努力可有所成，怠惰则败"),
    72: ("半吉半凶", "利害混合，先甘后苦或先苦后甘"),
    73: ("吉", "安乐自足，虽无大志但可平安一生"),
    74: ("凶", "沉迷懒惰，无智无勇，事多难成"),
    75: ("半吉半凶", "进不如退，宜静不宜动"),
    76: ("凶", "离散破财，家庭缘薄，破败之象"),
    77: ("半吉半凶", "先苦后甘，中年后运渐佳，晚境难料"),
    78: ("半吉半凶", "前半段渐入佳境，晚年多有起伏"),
    79: ("凶", "云雾散乱，苦尽未必甘来，精神易生颓废"),
    80: ("半吉半凶", "得而复失，历尽艰辛，晚年宜退守清静"),
    81: ("大吉", "还本归元，最高吉数，与 1 同论，万物复始"),
}

assert len(SHULI) == 81, "81 数吉凶表条目数不对"

# ---------------------------------------------------------------------------
# 五行
# ---------------------------------------------------------------------------

DIGIT_WUXING = {
    1: "木", 2: "木",
    3: "火", 4: "火",
    5: "土", 6: "土",
    7: "金", 8: "金",
    9: "水", 0: "水",
}

GENERATE = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROL = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

GE_LABELS = ("天格", "人格", "地格", "外格", "总格")


def fold_number(n):
    """> 81 时按 ((n-1) % 81) + 1 折算到 1-81。"""
    if n <= 81:
        return n
    return ((n - 1) % 81) + 1


def digit_wuxing(n):
    return DIGIT_WUXING[n % 10]


def lookup_shuli(n):
    folded = fold_number(n)
    grade, text = SHULI[folded]
    return folded, grade, text


def wuxing_relation(a, b):
    """a、b 是五行字（如"木"）。返回 (关系描述, 是否相生, 是否相克)。"""
    if a == b:
        return "比和（%s、%s 同属一行）" % (a, b)
    if GENERATE[a] == b:
        return "相生（%s生%s）" % (a, b)
    if GENERATE[b] == a:
        return "相生（%s生%s）" % (b, a)
    if CONTROL[a] == b:
        return "相克（%s克%s）" % (a, b)
    if CONTROL[b] == a:
        return "相克（%s克%s）" % (b, a)
    return "未知关系"


# ---------------------------------------------------------------------------
# 五格计算
# ---------------------------------------------------------------------------

def compute(surname, given):
    """surname: [X1] 或 [X1, X2]；given: [M1] 或 [M1, M2]。

    返回 dict，含 combo 说明与五格数值（天格/人格/地格/外格/总格）。
    """
    fu_xing = len(surname) == 2
    shuang_ming = len(given) == 2

    if len(surname) == 1:
        x1 = surname[0]
        x2 = None
    else:
        x1, x2 = surname

    if len(given) == 1:
        m1 = given[0]
        m2 = None
    else:
        m1, m2 = given

    if not fu_xing and not shuang_ming:
        combo = "单姓单名"
        tian = x1 + 1
        ren = x1 + m1
        di = m1 + 1
        wai = 2
        zong = x1 + m1
    elif not fu_xing and shuang_ming:
        combo = "单姓双名"
        tian = x1 + 1
        ren = x1 + m1
        di = m1 + m2
        wai = m2 + 1
        zong = x1 + m1 + m2
    elif fu_xing and not shuang_ming:
        combo = "复姓单名"
        tian = x1 + x2
        ren = x2 + m1
        di = m1 + 1
        wai = x1 + 1
        zong = x1 + x2 + m1
    else:
        combo = "复姓双名"
        tian = x1 + x2
        ren = x2 + m1
        di = m1 + m2
        wai = x1 + m2
        zong = x1 + x2 + m1 + m2

    values = {"天格": tian, "人格": ren, "地格": di, "外格": wai, "总格": zong}

    ge_results = {}
    for label in GE_LABELS:
        n = values[label]
        folded, grade, text = lookup_shuli(n)
        elem = digit_wuxing(folded)
        ge_results[label] = {
            "raw": n,
            "folded": folded,
            "grade": grade,
            "text": text,
            "wuxing": elem,
        }

    tian_ren_rel = wuxing_relation(ge_results["天格"]["wuxing"], ge_results["人格"]["wuxing"])
    ren_di_rel = wuxing_relation(ge_results["人格"]["wuxing"], ge_results["地格"]["wuxing"])

    return {
        "combo": combo,
        "surname": surname,
        "given": given,
        "ge": ge_results,
        "sancai": {
            "tian_ren": tian_ren_rel,
            "ren_di": ren_di_rel,
            "sequence": "%s-%s-%s" % (
                ge_results["天格"]["wuxing"],
                ge_results["人格"]["wuxing"],
                ge_results["地格"]["wuxing"],
            ),
        },
    }


def format_report(result):
    lines = []
    lines.append("## 输入")
    lines.append("- 姓氏笔画：%s" % "、".join(str(v) for v in result["surname"]))
    lines.append("- 名字笔画：%s" % "、".join(str(v) for v in result["given"]))
    lines.append("- 姓名字数组合：%s" % result["combo"])
    lines.append("")

    lines.append("## 五格")
    lines.append("| 五格 | 数值 | 五行 | 吉凶等级 |")
    lines.append("|---|---|---|---|")
    for label in GE_LABELS:
        g = result["ge"][label]
        folded_note = "" if g["folded"] == g["raw"] else "（折算为 %d）" % g["folded"]
        lines.append(
            "| %s | %d%s | %s | %s |"
            % (label, g["raw"], folded_note, g["wuxing"], g["grade"])
        )
    lines.append("")

    lines.append("## 数理吉凶")
    for label in GE_LABELS:
        g = result["ge"][label]
        lines.append("- %s（%d，%s）：%s — %s" % (label, g["raw"], g["grade"], g["wuxing"], g["text"]))
    lines.append("")

    lines.append("## 三才五行")
    lines.append("- 三才五行序列（天格-人格-地格）：%s" % result["sancai"]["sequence"])
    lines.append("- 天格 → 人格：%s" % result["sancai"]["tian_ren"])
    lines.append("- 人格 → 地格：%s" % result["sancai"]["ren_di"])
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        description="姓名学五格剖象法计算（康熙繁体笔画数，无第三方依赖）"
    )
    p.add_argument(
        "--surname",
        nargs="+",
        type=int,
        required=True,
        metavar="N",
        help="姓氏各字的康熙繁体笔画数，单姓传 1 个数字，复姓传 2 个",
    )
    p.add_argument(
        "--given",
        nargs="+",
        type=int,
        required=True,
        metavar="N",
        help="名字各字的康熙繁体笔画数，单名传 1 个数字，双名传 2 个",
    )
    return p


def run(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if len(args.surname) not in (1, 2):
        parser.error("--surname 只能传 1 个（单姓）或 2 个（复姓）笔画数")
    if len(args.given) not in (1, 2):
        parser.error("--given 只能传 1 个（单名）或 2 个（双名）笔画数")
    for n in list(args.surname) + list(args.given):
        if n < 1:
            parser.error("笔画数必须是正整数，收到 %r" % n)

    result = compute(args.surname, args.given)
    report = format_report(result)
    sys.stdout.write(report)
    if not report.endswith("\n"):
        sys.stdout.write("\n")
    return 0


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()

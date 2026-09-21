#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qigua.py 回归测试：纳甲装卦、八宫卦变、世应、六神起法、CLI 输出。"""

import importlib.util
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "qigua.py")
PY = sys.executable

_spec = importlib.util.spec_from_file_location("qigua", SCRIPT)
qigua = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qigua)


def run_qigua(*args):
    proc = subprocess.run(
        [PY, SCRIPT] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def section(stdout, title):
    marker = "## " + title
    start = stdout.find(marker)
    if start < 0:
        return ""
    rest = stdout[start + len(marker):]
    nxt = rest.find("\n## ")
    if nxt < 0:
        return rest
    return rest[:nxt]


def field(stdout, name):
    m = re.search(r"^- %s：(.+)$" % re.escape(name), stdout, re.M)
    return m.group(1).strip() if m else ""


class GuaTableTests(unittest.TestCase):
    """64 卦生成表内部一致性。"""

    def test_table_has_64_unique_entries(self):
        self.assertEqual(len(qigua.GUA_TABLE), 64)

    def test_qian_gong_names_and_shiying(self):
        expected = [
            ("乾为天", "本宫", 6, 3),
            ("天风姤", "一世", 1, 4),
            ("天山遯", "二世", 2, 5),
            ("天地否", "三世", 3, 6),
            ("风地观", "四世", 4, 1),
            ("山地剥", "五世", 5, 2),
            ("火地晋", "游魂", 4, 1),
            ("火天大有", "归魂", 3, 6),
        ]
        by_name = {info["name"]: info for info in qigua.GUA_TABLE.values()}
        for name, shidai, shi, ying in expected:
            self.assertIn(name, by_name)
            info = by_name[name]
            self.assertEqual(info["gong"], "乾")
            self.assertEqual(info["shidai"], shidai)
            self.assertEqual(qigua.SHI_YING_POS[shidai], (shi, ying))

    def test_kun_gong_names_and_shiying(self):
        expected = [
            ("坤为地", "本宫", 6, 3),
            ("地雷复", "一世", 1, 4),
            ("地泽临", "二世", 2, 5),
            ("地天泰", "三世", 3, 6),
            ("雷天大壮", "四世", 4, 1),
            ("泽天夬", "五世", 5, 2),
            ("水天需", "游魂", 4, 1),
            ("水地比", "归魂", 3, 6),
        ]
        by_name = {info["name"]: info for info in qigua.GUA_TABLE.values()}
        for name, shidai, shi, ying in expected:
            self.assertIn(name, by_name)
            info = by_name[name]
            self.assertEqual(info["gong"], "坤")
            self.assertEqual(info["shidai"], shidai)
            self.assertEqual(qigua.SHI_YING_POS[shidai], (shi, ying))

    def test_all_eight_gong_have_eight_gua_each(self):
        counts = {}
        for info in qigua.GUA_TABLE.values():
            counts[info["gong"]] = counts.get(info["gong"], 0) + 1
        self.assertEqual(counts, {g: 8 for g in qigua.GONG_ORDER})

    def test_gua_names_are_all_distinct(self):
        names = [info["name"] for info in qigua.GUA_TABLE.values()]
        self.assertEqual(len(names), len(set(names)))


class NajiaTests(unittest.TestCase):
    """纳甲装卦是否与标准京房纳甲表吻合。"""

    def test_qian_najia(self):
        result = qigua.najia_liuyao("乾", "乾")
        self.assertEqual(
            result,
            [("甲", "子"), ("甲", "寅"), ("甲", "辰"), ("壬", "午"), ("壬", "申"), ("壬", "戌")],
        )

    def test_kun_najia(self):
        result = qigua.najia_liuyao("坤", "坤")
        self.assertEqual(
            result,
            [("乙", "未"), ("乙", "巳"), ("乙", "卯"), ("癸", "丑"), ("癸", "亥"), ("癸", "酉")],
        )

    def test_kan_najia(self):
        result = qigua.najia_liuyao("坎", "坎")
        self.assertEqual(
            result,
            [("戊", "寅"), ("戊", "辰"), ("戊", "午"), ("戊", "申"), ("戊", "戌"), ("戊", "子")],
        )

    def test_zhen_najia(self):
        result = qigua.najia_liuyao("震", "震")
        self.assertEqual(
            result,
            [("庚", "子"), ("庚", "寅"), ("庚", "辰"), ("庚", "午"), ("庚", "申"), ("庚", "戌")],
        )

    def test_xun_najia(self):
        result = qigua.najia_liuyao("巽", "巽")
        self.assertEqual(
            result,
            [("辛", "丑"), ("辛", "亥"), ("辛", "酉"), ("辛", "未"), ("辛", "巳"), ("辛", "卯")],
        )

    def test_li_najia(self):
        result = qigua.najia_liuyao("离", "离")
        self.assertEqual(
            result,
            [("己", "卯"), ("己", "丑"), ("己", "亥"), ("己", "酉"), ("己", "未"), ("己", "巳")],
        )

    def test_gen_najia(self):
        result = qigua.najia_liuyao("艮", "艮")
        self.assertEqual(
            result,
            [("丙", "辰"), ("丙", "午"), ("丙", "申"), ("丙", "戌"), ("丙", "子"), ("丙", "寅")],
        )

    def test_dui_najia(self):
        result = qigua.najia_liuyao("兑", "兑")
        self.assertEqual(
            result,
            [("丁", "巳"), ("丁", "卯"), ("丁", "丑"), ("丁", "亥"), ("丁", "酉"), ("丁", "未")],
        )


class LiuqinTests(unittest.TestCase):
    """六亲判定：以宫五行为「我」。"""

    def test_qian_gong_liuqin_by_line(self):
        # 乾为天：子孙、妻财、父母、官鬼、兄弟、父母（初爻到上爻）
        hexagram = qigua.build_hexagram(qigua.TRIGRAMS["乾"] + qigua.TRIGRAMS["乾"])
        self.assertEqual(hexagram["liuqin"], ["子孙", "妻财", "父母", "官鬼", "兄弟", "父母"])

    def test_liuqin_relation_wuxing_cycle(self):
        self.assertEqual(qigua.liuqin_relation("金", "金"), "兄弟")
        self.assertEqual(qigua.liuqin_relation("金", "水"), "子孙")
        self.assertEqual(qigua.liuqin_relation("金", "木"), "妻财")
        self.assertEqual(qigua.liuqin_relation("金", "火"), "官鬼")
        self.assertEqual(qigua.liuqin_relation("金", "土"), "父母")


class SixSpiritsTests(unittest.TestCase):
    """六神起法：不同日干下的起点是否正确。"""

    def test_jiayi_starts_qinglong(self):
        self.assertEqual(qigua.six_spirits_for_day("甲")[0], "青龙")
        self.assertEqual(qigua.six_spirits_for_day("乙")[0], "青龙")

    def test_bingding_starts_zhuque(self):
        self.assertEqual(qigua.six_spirits_for_day("丙")[0], "朱雀")
        self.assertEqual(qigua.six_spirits_for_day("丁")[0], "朱雀")

    def test_wu_starts_gouchen(self):
        self.assertEqual(qigua.six_spirits_for_day("戊")[0], "勾陈")

    def test_ji_starts_tengshe(self):
        self.assertEqual(qigua.six_spirits_for_day("己")[0], "螣蛇")

    def test_gengxin_starts_baihu(self):
        self.assertEqual(qigua.six_spirits_for_day("庚")[0], "白虎")
        self.assertEqual(qigua.six_spirits_for_day("辛")[0], "白虎")

    def test_renkui_starts_xuanwu(self):
        self.assertEqual(qigua.six_spirits_for_day("壬")[0], "玄武")
        self.assertEqual(qigua.six_spirits_for_day("癸")[0], "玄武")

    def test_sequence_order(self):
        spirits = qigua.six_spirits_for_day("甲")
        self.assertEqual(spirits, ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"])


class BaoshuTests(unittest.TestCase):
    """报数起卦法的取余逻辑。"""

    def test_basic_case(self):
        ben_lines, moving, detail = qigua.qigua_by_numbers(7, 5, 3)
        self.assertEqual(detail["upper_name"], "艮")
        self.assertEqual(detail["lower_name"], "巽")
        self.assertEqual(detail["moving_pos"], 3)
        self.assertEqual(moving, {3})

    def test_wraparound_equivalence(self):
        """a=9 应与 a=1 取到同一个上卦（((9-1)%8)+1 == ((1-1)%8)+1 == 1 → 乾）。"""
        _, _, detail1 = qigua.qigua_by_numbers(1, 5, 3)
        _, _, detail9 = qigua.qigua_by_numbers(9, 5, 3)
        self.assertEqual(detail1["upper_name"], detail9["upper_name"])
        self.assertEqual(detail1["upper_name"], "乾")

    def test_moving_position_wraps_into_1_to_6(self):
        for a in range(1, 20):
            for b in range(1, 20):
                for c in range(1, 20):
                    _, moving, detail = qigua.qigua_by_numbers(a, b, c)
                    self.assertIn(detail["moving_pos"], range(1, 7))
                    self.assertEqual(moving, {detail["moving_pos"]})

    def test_number_8_maps_to_kun(self):
        _, _, detail = qigua.qigua_by_numbers(8, 8, 6)
        self.assertEqual(detail["upper_name"], "坤")
        self.assertEqual(detail["lower_name"], "坤")


class CoinTests(unittest.TestCase):
    """摇钱法：老阳/少阳/少阴/老阴对应阴阳与动爻判定。"""

    def test_lao_yang_is_yang_and_moving(self):
        ben_lines, moving, detail = qigua.qigua_by_coins([0, 1, 1, 1, 1, 1])
        self.assertEqual(ben_lines[0], 1)
        self.assertIn(1, moving)
        self.assertEqual(detail["labels"][0], "老阳")

    def test_lao_yin_is_yin_and_moving(self):
        ben_lines, moving, detail = qigua.qigua_by_coins([3, 1, 1, 1, 1, 1])
        self.assertEqual(ben_lines[0], 0)
        self.assertIn(1, moving)
        self.assertEqual(detail["labels"][0], "老阴")

    def test_shao_yang_not_moving(self):
        ben_lines, moving, detail = qigua.qigua_by_coins([1, 1, 1, 1, 1, 1])
        self.assertEqual(ben_lines[0], 1)
        self.assertNotIn(1, moving)

    def test_shao_yin_not_moving(self):
        ben_lines, moving, detail = qigua.qigua_by_coins([2, 1, 1, 1, 1, 1])
        self.assertEqual(ben_lines[0], 0)
        self.assertNotIn(1, moving)

    def test_all_static(self):
        _, moving, _ = qigua.qigua_by_coins([1, 1, 2, 2, 1, 2])
        self.assertEqual(moving, set())


class DayGanzhiTests(unittest.TestCase):
    def test_anchor_1990_05_15_is_gengchen(self):
        import datetime
        gan, zhi = qigua.day_ganzhi(datetime.date(1990, 5, 15))
        self.assertEqual(gan + zhi, "庚辰")


class CliTests(unittest.TestCase):
    """CLI 端到端：subprocess 调用脚本。"""

    def test_numbers_mode_golden(self):
        code, out, err = run_qigua("--numbers", "7", "5", "3", "--date", "2026-09-21")
        self.assertEqual(code, 0, err)
        self.assertIn("起卦方式：报数起卦法", out)
        self.assertIn("卦名：山风蛊", out)
        self.assertIn("日干支：戊戌", out)
        self.assertIn("●动", out)
        self.assertNotIn("Traceback", out)
        self.assertNotIn("Traceback", err)

    def test_coins_mode_golden(self):
        code, out, err = run_qigua(
            "--coins", "0", "1", "2", "3", "1", "2", "--date", "1990-05-15"
        )
        self.assertEqual(code, 0, err)
        self.assertIn("起卦方式：摇钱法", out)
        self.assertIn("日干支：庚辰", out)
        self.assertIn("卦名：水泽节", out)
        self.assertIn("变卦", out)
        self.assertIn("卦名：泽水困", out)

    def test_coins_mode_words_accepted(self):
        code, out, err = run_qigua(
            "--coins", "老阳", "少阳", "少阴", "老阴", "少阳", "少阴", "--date", "1990-05-15"
        )
        self.assertEqual(code, 0, err)
        self.assertIn("卦名：水泽节", out)

    def test_all_static_has_no_bian_gua_section_content(self):
        code, out, err = run_qigua(
            "--coins", "1", "1", "2", "2", "1", "2", "--date", "2026-09-21"
        )
        self.assertEqual(code, 0, err)
        self.assertIn("六爻全静", out)
        self.assertIn("动爻数：0", out)

    def test_missing_input_mode_errors(self):
        code, out, err = run_qigua("--date", "2026-09-21")
        self.assertNotEqual(code, 0)
        self.assertIn("必须提供 --numbers 或 --coins", err)

    def test_both_modes_conflict_errors(self):
        code, out, err = run_qigua(
            "--numbers", "1", "2", "3",
            "--coins", "1", "1", "1", "1", "1", "1",
        )
        self.assertNotEqual(code, 0)
        self.assertIn("互斥", err)

    def test_question_shown_when_given(self):
        code, out, err = run_qigua(
            "--numbers", "1", "2", "3", "--date", "2026-09-21", "--question", "近期财运如何",
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(field(out, "所问之事"), "近期财运如何")

    def test_six_spirits_column_present_in_ben_gua_only(self):
        code, out, err = run_qigua("--numbers", "7", "5", "3", "--date", "2026-09-21")
        self.assertEqual(code, 0, err)
        ben_section = section(out, "本卦")
        bian_section = section(out, "变卦")
        self.assertIn("| 六神 |", ben_section)
        self.assertNotIn("| 六神 |", bian_section)


if __name__ == "__main__":
    unittest.main()

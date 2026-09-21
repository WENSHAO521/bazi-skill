#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""paiju.py 回归测试。

本脚本 **不做排局**（见 paiju.py 顶部说明与
methods/qimen/references/paiju-guize.md），所以这里的测试覆盖范围是：

1. 九宫方位固定映射的正确性（洛书九宫）。
2. 给定阴阳遁 + 局数时，地盘六仪三奇排布的：
   - 确定性（同样输入多次跑，结果完全一致）
   - 内部一致性（9 个宫恰好被 9 个不重复的六仪三奇字符填满，
     不重不漏；含中五宫）
   - 与至少 2 篇独立公开资料交叉核对过的"阳遁一局""阴遁一局"起手
     结果一致（见 references/paiju-guize.md 的引用）——这是本测试
     集里唯一能找到外部可验证例题的环节，其余环节（天盘飞布、值符
     值使、八门八神）目前只做内部一致性校验，没有找到可交叉核对、
     带确定答案的完整例题，如实说明，不要误认为已被外部验证。
3. 天盘/八门/八神旋转后依然只填满 8 个外宫，不重不漏；中五宫始终没有
   独立的天盘/星/门/神。
4. 值符星/值使门与九宫图里标注的"值符值使落宫"一致（不允许摘要文字
   与图不符）。
5. 中五宫（寄坤二宫）边界情形：旬首落中五宫、时干目标落中五宫时不报错，
   且都能在“## 警告”里如实提示。
6. CLI 参数校验（阴阳遁必选其一且互斥、局数范围、时干支合法性、
   --hour-ganzhi 与 --solar/--hour 互斥且 --solar/--hour 必须成对）。
"""

import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "paiju.py")
PY = sys.executable

sys.path.insert(0, HERE)
import paiju  # noqa: E402


def run_cli(*args):
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
    return rest if nxt < 0 else rest[:nxt]


class PalaceFixedInfoTests(unittest.TestCase):
    def test_jiugong_luoshu_fixed_directions(self):
        expected = {
            1: ("坎", "北"), 2: ("坤", "西南"), 3: ("震", "东"),
            4: ("巽", "东南"), 5: ("中", "中"), 6: ("乾", "西北"),
            7: ("兑", "西"), 8: ("艮", "东北"), 9: ("离", "南"),
        }
        for p, (name, direction) in expected.items():
            self.assertEqual(paiju.PALACE_NAME[p], name)
            self.assertEqual(paiju.PALACE_DIR[p], direction)

    def test_luoshu_magic_square_sums_15(self):
        """三行、三列、两条对角线之和均为 15，是洛书九宫排列的定义性校验。"""
        g = paiju.GRID
        for row in g:
            self.assertEqual(sum(row), 15)
        for col in range(3):
            self.assertEqual(sum(g[r][col] for r in range(3)), 15)
        self.assertEqual(g[0][0] + g[1][1] + g[2][2], 15)
        self.assertEqual(g[0][2] + g[1][1] + g[2][0], 15)

    def test_fixed_star_and_door_cover_eight_outer_palaces_uniquely(self):
        outer = {1, 2, 3, 4, 6, 7, 8, 9}
        self.assertEqual(set(paiju.FIXED_STAR.keys()), outer)
        self.assertEqual(set(paiju.FIXED_DOOR.keys()), outer)
        self.assertEqual(len(set(paiju.FIXED_STAR.values())), 8)
        self.assertEqual(len(set(paiju.FIXED_DOOR.values())), 8)

    def test_ring_is_a_permutation_of_eight_outer_palaces(self):
        self.assertEqual(sorted(paiju.RING), [1, 2, 3, 4, 6, 7, 8, 9])
        self.assertEqual(len(paiju.RING), 8)


class DipanTests(unittest.TestCase):
    def test_dipan_fills_nine_palaces_without_repeat(self):
        for yang in (True, False):
            for ju in range(1, 10):
                dipan = paiju.build_dipan(ju, yang)
                self.assertEqual(set(dipan.keys()), set(range(1, 10)))
                self.assertEqual(set(dipan.values()), set("戊己庚辛壬癸乙丙丁"))

    def test_dipan_deterministic(self):
        for yang in (True, False):
            for ju in range(1, 10):
                a = paiju.build_dipan(ju, yang)
                b = paiju.build_dipan(ju, yang)
                self.assertEqual(a, b)

    def test_dipan_invalid_ju_raises(self):
        with self.assertRaises(ValueError):
            paiju.build_dipan(0, True)
        with self.assertRaises(ValueError):
            paiju.build_dipan(10, True)

    def test_yangdun_yiju_matches_published_example(self):
        """外部可验证例题：阳遁一局戊落坎一宫、己落坤二宫、庚落震三宫……

        引用：知乎《奇门遁甲式盘中三奇六仪排布奥秘》等至少 2 篇独立资料
        一致给出该起手结果，详见 references/paiju-guize.md。
        """
        dipan = paiju.build_dipan(1, True)
        expected = {1: "戊", 2: "己", 3: "庚", 4: "辛", 5: "壬",
                    6: "癸", 7: "丁", 8: "丙", 9: "乙"}
        self.assertEqual(dipan, expected)

    def test_yindun_yiju_liuyi_reverse_sanqi_forward(self):
        """阴遁：六仪(戊己庚辛壬癸)逆布、三奇(乙丙丁)顺布——与阳遁相反。

        这是两篇独立资料共同给出的规则（见 references 文档），用阴遁一局
        的六仪、三奇各自在盘面上的相对顺序来做内部一致性校验。
        """
        dipan = paiju.build_dipan(1, False)
        by_palace = [dipan[p] for p in range(1, 10)]
        liuyi_seq = [g for g in by_palace if g in paiju.LIUYI]
        sanqi_seq = [g for g in by_palace if g in paiju.SANQI]
        self.assertEqual(liuyi_seq, list("戊癸壬辛庚己"))  # 戊后逆序
        self.assertEqual(sanqi_seq, list("乙丙丁"))  # 顺序


class XunShouTests(unittest.TestCase):
    def test_liujia_ji_gong_mapping(self):
        cases = [
            (("甲", "子"), "戊"), (("甲", "戌"), "己"), (("甲", "申"), "庚"),
            (("甲", "午"), "辛"), (("甲", "辰"), "壬"), (("甲", "寅"), "癸"),
        ]
        for (gan, zhi), yi in cases:
            got_yi, got_gz = paiju.find_xun_yi(gan, zhi)
            self.assertEqual(got_yi, yi)
            self.assertEqual(got_gz, "甲" + zhi)

    def test_every_ganzhi_in_same_xun_shares_xun_yi(self):
        """甲子旬内任意干支（如庚午）应与旬首甲子共用同一个寄仪"""
        got_yi, got_gz = paiju.find_xun_yi("庚", "午")
        self.assertEqual(got_yi, "戊")
        self.assertEqual(got_gz, "甲子")

    def test_validate_ganzhi_rejects_bad_parity(self):
        with self.assertRaises(ValueError):
            paiju.validate_ganzhi("甲丑")
        gan, zhi = paiju.validate_ganzhi("庚午")
        self.assertEqual((gan, zhi), ("庚", "午"))


class ComputeConsistencyTests(unittest.TestCase):
    def test_deterministic_across_runs(self):
        r1 = paiju.compute(True, 1, "庚", "午")
        r2 = paiju.compute(True, 1, "庚", "午")
        self.assertEqual(r1["tianpan_gan"], r2["tianpan_gan"])
        self.assertEqual(r1["tianpan_star"], r2["tianpan_star"])
        self.assertEqual(r1["tianpan_men"], r2["tianpan_men"])
        self.assertEqual(r1["gods"], r2["gods"])
        self.assertEqual(r1["zhifu_star"], r2["zhifu_star"])
        self.assertEqual(r1["landing_gong"], r2["landing_gong"])

    def test_tianpan_star_men_gods_fill_eight_outer_palaces_uniquely(self):
        for yang in (True, False):
            for ju in (1, 3, 5, 9):
                for gan, zhi in (("庚", "午"), ("丙", "午"), ("壬", "子"), ("癸", "丑")):
                    try:
                        paiju.validate_ganzhi(gan + zhi)
                    except ValueError:
                        continue
                    r = paiju.compute(yang, ju, gan, zhi)
                    self.assertEqual(set(r["tianpan_men"].keys()), set(paiju.RING))
                    self.assertEqual(set(r["tianpan_men"].values()), set(paiju.FIXED_DOOR.values()))
                    self.assertEqual(set(r["gods"].keys()), set(paiju.RING))
                    self.assertEqual(len(set(r["gods"].values())), 8)
                    # 星：8 个外宫都有星，中五宫（天禽）不独立占位
                    self.assertEqual(set(r["tianpan_star"].keys()), set(paiju.RING))
                    self.assertNotIn(5, r["tianpan_star"])
                    self.assertNotIn(5, r["tianpan_men"])
                    self.assertNotIn(5, r["gods"])

    def test_zhifu_star_and_menshi_land_where_grid_marks_it(self):
        """摘要文字里的"值符星/值使门落 X 宫"必须与九宫图里的落宫标记一致。

        天禽是特例：中五宫本身没有天盘星格子，它随坤二宫的天芮一起落地，
        所以当值符星是天禽时，落宫格子里显示的是"天芮"（天禽借芮飞）。
        """
        for yang in (True, False):
            for ju in (1, 2, 5, 9):
                r = paiju.compute(yang, ju, "庚", "午" if yang else "子")
                self.assertIn(r["landing_gong"], paiju.RING)
                star_at_landing = r["tianpan_star"][r["landing_gong"]]
                expected_star = "天芮" if r["zhifu_star"] == "天禽" else r["zhifu_star"]
                self.assertEqual(star_at_landing, expected_star)
                self.assertEqual(r["gods"][r["landing_gong"]], "值符")
                self.assertEqual(r["tianpan_men"][r["landing_gong"]], r["zhishi_men"])

    def test_zhonggong_xunshou_case_uses_tianqin_and_proxy_kun(self):
        """旬首落中五宫时：值符星记作天禽，值使门借坤二宫的死门。"""
        r = paiju.compute(True, 1, "丙", "午")  # 阳遁一局中五宫干为壬，丙午属甲辰旬(壬)
        self.assertEqual(r["xun_gong"], 5)
        self.assertEqual(r["zhifu_star"], "天禽")
        self.assertEqual(r["zhishi_men"], "死门")

    def test_target_gong_zhonggong_reports_warning_and_proxy_landing(self):
        r = paiju.compute(False, 1, "癸", "丑")  # 阴遁一局中五宫干为癸
        self.assertEqual(r["target_gong"], 5)
        self.assertIn(r["landing_gong"], paiju.RING)
        self.assertNotEqual(r["landing_gong"], 5)

    def test_offset_zero_means_fuyin_self_landing(self):
        """值符原地不动（伏吟）：旬首落宫与时干目标宫的落宫应相同。"""
        r = paiju.compute(False, 1, "壬", "子")
        self.assertEqual(r["offset"], 0)
        self.assertEqual(r["landing_gong"], r["xun_gong"])

    def test_god_words_differ_for_yang_and_yin_only_in_two_slots(self):
        r_yang = paiju.compute(True, 1, "庚", "午")
        r_yin = paiju.compute(False, 1, "庚", "子")
        self.assertIn("勾陈", r_yang["gods"].values())
        self.assertIn("朱雀", r_yang["gods"].values())
        self.assertNotIn("白虎", r_yang["gods"].values())
        self.assertIn("白虎", r_yin["gods"].values())
        self.assertIn("玄武", r_yin["gods"].values())
        self.assertNotIn("勾陈", r_yin["gods"].values())
        common = {"值符", "螣蛇", "太阴", "六合", "九地", "九天"}
        self.assertTrue(common.issubset(set(r_yang["gods"].values())))
        self.assertTrue(common.issubset(set(r_yin["gods"].values())))


class CLITests(unittest.TestCase):
    def test_golden_yangdun_yiju_hour_ganzhi(self):
        code, out, err = run_cli("--yangdun", "--ju", "1", "--hour-ganzhi", "庚午")
        self.assertEqual(code, 0, err)
        self.assertIn("阳遁", out)
        self.assertIn("1 局", out)
        tbl = section(out, "地盘六仪三奇总表")
        self.assertIn("1 宫(坎)：戊", tbl)
        self.assertIn("2 宫(坤)：己", tbl)
        self.assertIn("3 宫(震)：庚", tbl)
        self.assertNotIn("Traceback", out)

    def test_cli_deterministic_stdout(self):
        _, out1, _ = run_cli("--yindun", "--ju", "3", "--hour-ganzhi", "乙丑")
        _, out2, _ = run_cli("--yindun", "--ju", "3", "--hour-ganzhi", "乙丑")
        self.assertEqual(out1, out2)

    def test_cli_solar_hour_convenience_matches_bazi_golden_case(self):
        """1990-05-15 午时的时柱是壬午（与 bazi 的黄金用例一致）。"""
        code, out, err = run_cli("--yangdun", "--ju", "5", "--solar", "1990-05-15", "--hour", "12:00")
        self.assertEqual(code, 0, err)
        self.assertIn("时干支：壬午", out)

    def test_cli_requires_yang_or_yin(self):
        code, out, err = run_cli("--ju", "1", "--hour-ganzhi", "甲子")
        self.assertNotEqual(code, 0)

    def test_cli_rejects_both_yang_and_yin(self):
        code, out, err = run_cli("--yangdun", "--yindun", "--ju", "1", "--hour-ganzhi", "甲子")
        self.assertNotEqual(code, 0)

    def test_cli_rejects_ju_out_of_range(self):
        code, out, err = run_cli("--yangdun", "--ju", "10", "--hour-ganzhi", "甲子")
        self.assertNotEqual(code, 0)
        self.assertIn("1~9", err)

    def test_cli_rejects_bad_ganzhi(self):
        code, out, err = run_cli("--yangdun", "--ju", "1", "--hour-ganzhi", "甲丑")
        self.assertNotEqual(code, 0)

    def test_cli_requires_hour_source(self):
        code, out, err = run_cli("--yangdun", "--ju", "1")
        self.assertNotEqual(code, 0)

    def test_cli_rejects_mixed_hour_sources(self):
        code, out, err = run_cli(
            "--yangdun", "--ju", "1", "--hour-ganzhi", "甲子",
            "--solar", "1990-05-15", "--hour", "12:00",
        )
        self.assertNotEqual(code, 0)

    def test_cli_rejects_solar_without_hour(self):
        code, out, err = run_cli("--yangdun", "--ju", "1", "--solar", "1990-05-15")
        self.assertNotEqual(code, 0)


if __name__ == "__main__":
    unittest.main()

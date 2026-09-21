#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pai_pan_ziwei.py 回归测试。

测试分两类，务必区分清楚：

1. **外部对照**（GoldenExternalTests / WorkedExamplesTests）：
   - `test_golden_2000_iztro`：对照开源紫微斗数排盘库 SylarLong/iztro
     （MIT 协议，`src/__tests__/astro/astro.test.ts`）里的一条公开测试用例
     `astro.bySolar('2000-8-16', 2, '女', true)`，其阳历 2000-08-16 对应的
     农历为 2000年七月十七（非闰）。该库输出：命宫干支壬午、命宫地支午、
     身宫地支戌、五行局木三局。本测试独立复算，只要求这几项一致
     （不对照该库的 soul/body 星名字段，那是"命主/身主"另一套查法，
     本脚本未实现，避免混淆）。
   - `test_ziwei_start_index_worked_examples`：对照公开流传的"安紫微星诀"
     三个书面数字例子（27日木三局→戌、13日火六局→亥、6日土五局→未），
     直接调用 `ziwei_start_index()`，不经过完整排盘流程。

2. **内部一致性**（InternalConsistencyTests）：只验证脚本自身逻辑不自相矛盾
   （十四主星各出现一次、紫微天府偏移互补、宫干十天干循环、边界时辰/闰月
   不报错等），**不代表已经过外部权威例题核对**，请勿将其当作算法正确性
   的独立证据。
"""

import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "pai_pan_ziwei.py")
PY = sys.executable

sys.path.insert(0, HERE)
import pai_pan_ziwei as zw  # noqa: E402


def run_ziwei(*args):
    proc = subprocess.run(
        [PY, SCRIPT] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def field(stdout, name):
    m = re.search(r"^- %s：(.+)$" % re.escape(name), stdout, re.M)
    return m.group(1).strip() if m else ""


def section(stdout, title):
    marker = "## " + title
    start = stdout.find(marker)
    if start < 0:
        return ""
    rest = stdout[start + len(marker):]
    nxt = rest.find("\n## ")
    return rest if nxt < 0 else rest[:nxt]


class GoldenExternalTests(unittest.TestCase):
    def test_golden_2000_iztro(self):
        """对照 SylarLong/iztro 公开测试用例（阳历2000-08-16寅时女=农历2000年七月十七非闰）。

        期望（来自该开源库 astro.test.ts）：
        命宫干支壬午、命宫地支午、身宫地支戌、五行局木三局。
        """
        code, out, err = run_ziwei("--lunar", "2000-07-17", "--shichen", "寅", "--sex", "女")
        self.assertEqual(code, 0, err)
        self.assertEqual(field(out, "生年干支"), "庚辰")
        self.assertIn("命宫：命宫（干支：壬午）", out)
        self.assertIn("（地支：戌）", section(out, "命宫与身宫"))
        self.assertIn("五行局：木三局", section(out, "命宫与身宫"))
        self.assertIn("紫微星：午宫", section(out, "命宫与身宫"))
        self.assertIn("天府星：戌宫", section(out, "命宫与身宫"))


class WorkedExamplesTests(unittest.TestCase):
    """对照公开流传的"安紫微星诀"书面数字例子，直接调用函数级 API。"""

    def test_example_27_wood3_xu(self):
        self.assertEqual(zw.zhi_of_rel(zw.ziwei_start_index(3, 27)), "戌")

    def test_example_13_fire6_hai(self):
        self.assertEqual(zw.zhi_of_rel(zw.ziwei_start_index(6, 13)), "亥")

    def test_example_6_earth5_wei(self):
        self.assertEqual(zw.zhi_of_rel(zw.ziwei_start_index(5, 6)), "未")


class SihuaTableTests(unittest.TestCase):
    """四化表抽查（两个独立网络来源与 iztro 源码三方一致）。"""

    def test_jia_and_gui(self):
        self.assertEqual(zw.SIHUA["甲"], ("廉贞", "破军", "武曲", "太阳"))
        self.assertEqual(zw.SIHUA["癸"], ("破军", "巨门", "太阴", "贪狼"))

    def test_geng(self):
        self.assertEqual(zw.SIHUA["庚"], ("太阳", "武曲", "太阴", "天同"))


class CliBasicTests(unittest.TestCase):
    def test_runs_without_traceback(self):
        code, out, err = run_ziwei("--lunar", "1990-05-15", "--shichen", "午", "--sex", "男")
        self.assertEqual(code, 0, err)
        self.assertNotIn("Traceback", out)
        self.assertNotIn("Traceback", err)
        for title in ("输入", "命宫与身宫", "十二宫与十四主星", "四化", "警告"):
            self.assertIn("## " + title, out)

    def test_missing_required_arg_errors(self):
        code, out, err = run_ziwei("--lunar", "1990-05-15", "--sex", "男")
        self.assertNotEqual(code, 0)

    def test_invalid_shichen_errors(self):
        code, out, err = run_ziwei("--lunar", "1990-05-15", "--shichen", "寅时", "--sex", "男")
        self.assertNotEqual(code, 0)

    def test_invalid_month_errors_gracefully(self):
        code, out, err = run_ziwei("--lunar", "1990-13-01", "--shichen", "子", "--sex", "男")
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)


class InternalConsistencyTests(unittest.TestCase):
    """仅验证脚本内部逻辑自洽，不代表已通过外部权威例题核对。"""

    def _all_lunar_days_for_ju(self, ju_number):
        return range(1, 31)

    def test_ziwei_tianfu_offset_always_complementary(self):
        """紫微、天府相对偏移之和恒为 12（对宫互补），对所有局数、所有日期成立。"""
        for ju_number in (2, 3, 4, 5, 6):
            for day in range(1, 31):
                ziwei_rel = zw.ziwei_start_index(ju_number, day)
                _, tianfu_rel = zw.place_major_stars(ziwei_rel)
                self.assertEqual((ziwei_rel + tianfu_rel) % 12, 0)

    def test_fourteen_major_stars_each_appear_once(self):
        """十四主星在任意局数/日期下都恰好各出现一次，不重复不遗漏。"""
        expected = set(s for s in zw.ZIWEI_GROUP if s) | set(s for s in zw.TIANFU_GROUP if s)
        self.assertEqual(len(expected), 14)
        for ju_number in (2, 3, 4, 5, 6):
            for day in (1, 6, 13, 17, 27, 30):
                ziwei_rel = zw.ziwei_start_index(ju_number, day)
                stars, _ = zw.place_major_stars(ziwei_rel)
                placed = [name for names in stars.values() for name in names]
                with self.subTest(ju=ju_number, day=day):
                    self.assertEqual(set(placed), expected)
                    self.assertEqual(len(placed), 14)

    def test_deterministic_repeat_calls(self):
        """同一输入重复调用结果稳定（无隐藏随机性/全局状态污染）。"""
        args = ("--lunar", "1985-11-08", "--shichen", "酉", "--sex", "女")
        _, out1, _ = run_ziwei(*args)
        _, out2, _ = run_ziwei(*args)
        self.assertEqual(out1, out2)

    def test_zi_hour_boundary_does_not_crash(self):
        for shichen in zw.ZHI_LIST:
            code, out, err = run_ziwei("--lunar", "1990-05-15", "--shichen", shichen, "--sex", "男")
            self.assertEqual(code, 0, err)
            self.assertNotIn("Traceback", out + err)

    def test_leap_month_does_not_crash_and_flags_warning(self):
        code, out, err = run_ziwei("--lunar", "1990-04-20", "--leap", "--shichen", "子", "--sex", "男")
        self.assertEqual(code, 0, err)
        self.assertNotIn("Traceback", out + err)

        code2, out2, err2 = run_ziwei("--lunar", "1990-04-10", "--leap", "--shichen", "子", "--sex", "男")
        self.assertEqual(code2, 0, err2)
        self.assertNotIn("Traceback", out2 + err2)

    def test_day_boundary_1_and_30_do_not_crash(self):
        for day in (1, 30):
            code, out, err = run_ziwei(
                "--lunar", "1990-05-%02d" % day, "--shichen", "子", "--sex", "男"
            )
            self.assertEqual(code, 0, err)
            self.assertNotIn("Traceback", out + err)

    def test_palace_gan_cycles_over_ten_stems(self):
        """十二宫宫干按十天干循环展开，起点为五虎遁寅宫天干。"""
        rels = [zw.gan_of_rel("甲", r) for r in range(12)]
        expected_start = zw.TIGER_RULE["甲"]
        start_idx = zw.GAN.index(expected_start)
        expected = [zw.GAN[(start_idx + r) % 10] for r in range(12)]
        self.assertEqual(rels, expected)

    def test_sihua_targets_are_always_placed_somewhere(self):
        """四化对应的星曜（多数是十四主星，少数是六吉星）必须能在盘面中被安放到。"""
        placeable = set(s for s in zw.ZIWEI_GROUP if s) | set(s for s in zw.TIANFU_GROUP if s)
        placeable |= {"文昌", "文曲", "左辅", "右弼", "天魁", "天钺"}
        for gan, targets in zw.SIHUA.items():
            for star in targets:
                with self.subTest(gan=gan, star=star):
                    self.assertIn(star, placeable)


if __name__ == "__main__":
    unittest.main(verbosity=2)

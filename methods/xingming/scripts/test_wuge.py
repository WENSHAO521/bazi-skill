#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wuge.py 回归：用 stdout 断言四种姓名字数组合的五格计算结果（手工验算）。"""

import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "wuge.py")
PY = sys.executable


def run_wuge(*args):
    proc = subprocess.run(
        [PY, SCRIPT] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def section(stdout, title):
    """截取 '## title' 到下一个 '##'（不含）。"""
    marker = "## " + title
    start = stdout.find(marker)
    if start < 0:
        return ""
    rest = stdout[start + len(marker):]
    nxt = rest.find("\n## ")
    if nxt < 0:
        return rest
    return rest[:nxt]


def ge_value(stdout, label):
    """从 '## 五格' 表格里读某一格的数值（表格第二列，去掉折算注释）。"""
    for line in stdout.splitlines():
        if line.startswith("| %s |" % label):
            cell = line.strip().strip("|").split("|")[1].strip()
            m = re.match(r"(\d+)", cell)
            return int(m.group(1)) if m else None
    return None


def combo_field(stdout):
    m = re.search(r"^- 姓名字数组合：(.+)$", stdout, re.M)
    return m.group(1).strip() if m else ""


class WugeComboTests(unittest.TestCase):
    def test_single_surname_single_given(self):
        """单姓单名：姓 7 画，名 8 画。
        天格=7+1=8 人格=7+8=15 地格=8+1=9 外格=2 总格=7+8=15
        """
        code, out, err = run_wuge("--surname", "7", "--given", "8")
        self.assertEqual(code, 0, err)
        self.assertEqual(combo_field(out), "单姓单名")
        self.assertEqual(ge_value(out, "天格"), 8)
        self.assertEqual(ge_value(out, "人格"), 15)
        self.assertEqual(ge_value(out, "地格"), 9)
        self.assertEqual(ge_value(out, "外格"), 2)
        self.assertEqual(ge_value(out, "总格"), 15)
        # 8→吉，15→大吉，9→大凶，2→大凶
        shuli = section(out, "数理吉凶")
        self.assertIn("天格（8，吉）", shuli)
        self.assertIn("人格（15，大吉）", shuli)
        self.assertIn("地格（9，大凶）", shuli)
        self.assertIn("外格（2，大凶）", shuli)
        self.assertIn("总格（15，大吉）", shuli)

    def test_single_surname_double_given(self):
        """单姓双名：姓 7 画，名两字 4 画、14 画。
        天格=7+1=8 人格=7+4=11 地格=4+14=18 外格=14+1=15 总格=7+4+14=25
        """
        code, out, err = run_wuge("--surname", "7", "--given", "4", "14")
        self.assertEqual(code, 0, err)
        self.assertEqual(combo_field(out), "单姓双名")
        self.assertEqual(ge_value(out, "天格"), 8)
        self.assertEqual(ge_value(out, "人格"), 11)
        self.assertEqual(ge_value(out, "地格"), 18)
        self.assertEqual(ge_value(out, "外格"), 15)
        self.assertEqual(ge_value(out, "总格"), 25)

    def test_double_surname_single_given(self):
        """复姓单名：姓两字 6 画、9 画，名 8 画。
        天格=6+9=15 人格=9+8=17 地格=8+1=9 外格=6+1=7 总格=6+9+8=23
        """
        code, out, err = run_wuge("--surname", "6", "9", "--given", "8")
        self.assertEqual(code, 0, err)
        self.assertEqual(combo_field(out), "复姓单名")
        self.assertEqual(ge_value(out, "天格"), 15)
        self.assertEqual(ge_value(out, "人格"), 17)
        self.assertEqual(ge_value(out, "地格"), 9)
        self.assertEqual(ge_value(out, "外格"), 7)
        self.assertEqual(ge_value(out, "总格"), 23)

    def test_double_surname_double_given(self):
        """复姓双名：姓两字 6 画、9 画，名两字 4 画、14 画。
        天格=6+9=15 人格=9+4=13 地格=4+14=18 外格=6+14=20 总格=6+9+4+14=33
        """
        code, out, err = run_wuge("--surname", "6", "9", "--given", "4", "14")
        self.assertEqual(code, 0, err)
        self.assertEqual(combo_field(out), "复姓双名")
        self.assertEqual(ge_value(out, "天格"), 15)
        self.assertEqual(ge_value(out, "人格"), 13)
        self.assertEqual(ge_value(out, "地格"), 18)
        self.assertEqual(ge_value(out, "外格"), 20)
        self.assertEqual(ge_value(out, "总格"), 33)


class WugeWuxingTests(unittest.TestCase):
    def test_wuxing_and_sancai_relation(self):
        """单姓单名 7/8：天格8→金，人格15→土，地格9→水。
        天格→人格：土生金（相生）；人格→地格：土克水（相克）。
        """
        code, out, err = run_wuge("--surname", "7", "--given", "8")
        self.assertEqual(code, 0, err)
        sancai = section(out, "三才五行")
        self.assertIn("金-土-水", sancai)
        self.assertIn("相生（土生金）", sancai)
        self.assertIn("相克（土克水）", sancai)

    def test_bihe_same_wuxing(self):
        """人格 11 → 木（个位1），地格 21 → 木（个位1），应判定比和。"""
        code, out, err = run_wuge("--surname", "10", "--given", "1", "20")
        self.assertEqual(code, 0, err)
        # 单姓双名：人格=10+1=11，地格=1+20=21
        self.assertEqual(ge_value(out, "人格"), 11)
        self.assertEqual(ge_value(out, "地格"), 21)
        sancai = section(out, "三才五行")
        self.assertIn("比和", sancai)


class WugeFoldingTests(unittest.TestCase):
    def test_fold_above_81_via_import(self):
        """折算公式：((n-1) % 81) + 1，直接测函数而非走 CLI 拼大数。"""
        sys.path.insert(0, HERE)
        import wuge

        self.assertEqual(wuge.fold_number(81), 81)
        self.assertEqual(wuge.fold_number(82), 1)
        self.assertEqual(wuge.fold_number(162), 81)
        self.assertEqual(wuge.fold_number(163), 1)
        self.assertEqual(wuge.fold_number(100), 19)

    def test_fold_above_81_via_cli(self):
        """姓 75 画 + 名 7 画（单姓单名）：总格=75+7=82，
        折算为 ((82-1)%81)+1=1，1 号是大吉。
        """
        code, out, err = run_wuge("--surname", "75", "--given", "7")
        self.assertEqual(code, 0, err)
        self.assertEqual(ge_value(out, "总格"), 82)
        shuli = section(out, "数理吉凶")
        self.assertIn("总格（82，大吉）", shuli)  # 折算后为 1 号，1 号是大吉
        wuge_section = section(out, "五格")
        self.assertIn("折算为 1", wuge_section)


class WugeValidationTests(unittest.TestCase):
    def test_too_many_surname_chars_rejected(self):
        code, out, err = run_wuge("--surname", "1", "2", "3", "--given", "4")
        self.assertNotEqual(code, 0)
        self.assertIn("--surname", err)

    def test_too_many_given_chars_rejected(self):
        code, out, err = run_wuge("--surname", "1", "--given", "2", "3", "4")
        self.assertNotEqual(code, 0)
        self.assertIn("--given", err)

    def test_nonpositive_stroke_rejected(self):
        code, out, err = run_wuge("--surname", "0", "--given", "5")
        self.assertNotEqual(code, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

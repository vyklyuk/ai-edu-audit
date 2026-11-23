# -*- coding: utf-8 -*-
"""Регресійний тест: розрахунковий модуль на даних лінії 1 дає рівно еталонний data.json."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from ai_edu_audit.calc.line import build_line_data, link_verdict  # noqa: E402
from ai_edu_audit.io import dumps_data, read_json, read_jsonl  # noqa: E402

REF = os.path.join(ROOT, "data", "reference", "line1")


class Line1Regression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.line = read_json(os.path.join(REF, "line.json"))
        cls.courses = read_jsonl(os.path.join(REF, "courses.jsonl"))
        cls.data = build_line_data(cls.line, cls.courses)
        with open(os.path.join(REF, "expected", "data.json"), encoding="utf-8") as f:
            cls.expected_text = f.read()

    def test_byte_identical(self):
        self.assertEqual(dumps_data(self.data), self.expected_text)

    def test_headline_numbers(self):
        self.assertEqual(self.data["prog_index"], [38.0, 83.5, 93.6])
        self.assertEqual(self.data["b1"], [0.764, 0.768, 0.932])
        self.assertEqual(self.data["b2"], [0.714, 0.714, 1.0])

    def test_hub_objects_consistent(self):
        """R і X еталонного хабу посилаються лише на курси, що є в D."""
        recs = read_json(os.path.join(REF, "recs.json"))
        codes = {p[0] for p in self.data["passport"]}
        self.assertTrue(set(recs["course"]) <= codes, set(recs["course"]) - codes)


class Verdicts(unittest.TestCase):
    def test_link_verdict(self):
        sem = {"A": 3, "B": 5, "C": 5}
        self.assertEqual(link_verdict("A", "B", "prereq", sem), "ok")
        self.assertEqual(link_verdict("B", "C", "prereq", sem), "same")
        self.assertEqual(link_verdict("B", "A", "prereq", sem), "late")
        self.assertEqual(link_verdict("B", "C", "coreq", sem), "ok")
        self.assertEqual(link_verdict("A", None, "next", sem), "absent")


if __name__ == "__main__":
    unittest.main()

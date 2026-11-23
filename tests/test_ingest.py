# -*- coding: utf-8 -*-
"""Нормалізація тексту, пошук цитат, зіставлення назв РП ↔ ОК."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from ai_edu_audit.ingest.convert import find_quote, normalize  # noqa: E402
from ai_edu_audit.ingest.inventory import base_title, is_kp, jaccard, ratio, shingles  # noqa: E402


class Normalize(unittest.TestCase):
    def test_apostrophes_dashes_hyphenation(self):
        self.assertEqual(normalize("Інтер’єр — про-\nєкт"), "інтер'єр - проєкт")

    def test_find_quote(self):
        pages = ["Тема 1. Вступ", "Тема 2. Ергономіка  інтер’єру\nта меблів"]
        self.assertEqual(find_quote(pages, "ергономіка інтер'єру та меблів"), 2)
        self.assertIsNone(find_quote(pages, "чого немає"))


class Titles(unittest.TestCase):
    def test_kp(self):
        self.assertTrue(is_kp("Дизайн інтер'єрів житла (КП)"))
        self.assertTrue(is_kp("Тематичний інтер’єр (KП)"))  # латинська K
        self.assertFalse(is_kp("Дизайн інтер'єрів житла"))

    def test_match_variants(self):
        a = base_title("Технології та матеріали в дизайні інтер_єрів")
        b = base_title("Технології і матеріали у дизайні інтер’єрів")
        self.assertGreater(ratio(a, b), 0.9)
        self.assertGreater(ratio(base_title("Основи проєктної графіки"), base_title("Основи проектної графіки")), 0.99)

    def test_similarity(self):
        t = "один два три чотири п'ять шість сім вісім дев'ять десять"
        self.assertEqual(jaccard(shingles(t), shingles(t)), 1.0)
        self.assertLess(jaccard(shingles(t), shingles("зовсім інший текст без збігів тут нічого")), 0.1)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""Властивості функції балу: межі, монотонність, коридор, вето."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from ai_edu_audit.calc import methodology as M  # noqa: E402
from ai_edu_audit.calc.scoring import problem, score, total  # noqa: E402

BY = {m[0]: m for m in M.MDEF}


class Score(unittest.TestCase):
    def test_range_and_none(self):
        for m in M.MDEF:
            self.assertIsNone(score(m, None))
            for v in (0, 0.1, 0.5, 1, 2, 5, 10, 20):
                s = score(m, v)
                self.assertGreaterEqual(s, 0.0, m[0])
                self.assertLessEqual(s, 100.0, m[0])

    def test_target_gives_100_accept_gives_70(self):
        for m in M.MDEF:
            if m[4] == "band":
                continue
            self.assertEqual(score(m, m[5]), 100.0, m[0])
            self.assertAlmostEqual(score(m, m[6]), 70.0, msg=m[0])

    def test_band(self):
        m = BY["B4"]
        self.assertEqual(score(m, 0.2), 100.0)
        self.assertLess(score(m, 0.5), 100.0)
        self.assertFalse(problem(m, 0.33))
        self.assertTrue(problem(m, 0.4))

    def test_veto_caps_score(self):
        good = {m[0]: (m[5][0] if m[4] == "band" else m[5]) for m in M.MDEF}
        raw, fin, veto, _ = total(good)
        self.assertEqual((raw, fin, veto), (100.0, 100.0, False))
        bad = dict(good, A2=0.0)
        raw, fin, veto, _ = total(bad)
        self.assertTrue(veto)
        self.assertLessEqual(fin, M.VETO_CAP)


if __name__ == "__main__":
    unittest.main()

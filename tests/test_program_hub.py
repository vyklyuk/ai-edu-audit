# -*- coding: utf-8 -*-
"""Фіксація хабу ОП v1 (23.11.2026): структура даних і вигляд, які не мають зламатися при подальших змінах.

Тест збирає хаб прогону runs/interior_b тим самим кодом, що й у роботі, і перевіряє вміст і ключові елементи шаблону.
Якщо зміна навмисна (наприклад, нова вкладка) — оновіть очікування тут і підніміть версію шаблону.
"""
import glob
import json
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(ROOT, "runs", "interior_b")
TPL = os.path.join(ROOT, "src", "ai_edu_audit", "hubs", "templates", "hub.html")
ENV = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))


@unittest.skipUnless(os.path.exists(os.path.join(RUN, "program.json")) and os.path.exists(os.path.join(RUN, "line_L1", "data.json")), "немає даних прогону runs/interior_b (вони не комітяться)")
class ProgramHubV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, "-m", "ai_edu_audit.program", RUN], check=True, env=ENV, capture_output=True)
        subprocess.run([sys.executable, "-m", "ai_edu_audit.hubs.build", RUN], check=True, env=ENV, capture_output=True)
        html = open(os.path.join(RUN, "hubs", "program.html"), encoding="utf-8").read()
        m = re.search(r"const DATA = (\{.*?\});\n", html, re.S)
        cls.html, cls.P = html, json.loads(m.group(1).replace("<\\/", "</"))
        cls.tpl = open(TPL, encoding="utf-8").read()

    # ---------- вміст ----------
    def test_tabs(self):
        self.assertEqual([v[0] for v in self.P["U"]["views"]],
                         ["summary", "passport", "prereq", "topics", "market", "unis", "metrics", "paths", "inputs"])

    def test_all_components_everywhere(self):
        D, U, X = self.P["D"], self.P["U"], self.P["X"]
        n = len(U["prereq_nodes"])
        self.assertEqual(n, 67)
        self.assertEqual(len(D["passport"]), n)          # паспорт
        self.assertEqual(len(X["paths"]), n)             # шляхи вдосконалення
        self.assertEqual(len(U["group"]), n)             # перемикачі циклів
        self.assertEqual(len(D["cscores"]) + len(U["metrics_missing"]), n)   # метрики

    def test_cycles(self):
        self.assertEqual([g["k"] for g in self.P["U"]["groups"]], ["zag", "prof", "vb1", "vb2"])

    def test_topics_and_unis(self):
        D, U = self.P["D"], self.P["U"]
        self.assertGreaterEqual(len(D["topics"]), 59)
        self.assertEqual(len(U["topic_blocks"]), 8)
        with_unis = [t for t in D["topics"] if any(x is not None for x in D["uni_t"][t[0]])]
        self.assertGreaterEqual(len(with_unis), 56)
        self.assertEqual(len(D["unis"]), 7)

    def test_links_and_course_topics(self):
        U = self.P["U"]
        self.assertGreaterEqual(len(U["prereq_links"]), 280)
        self.assertGreaterEqual(sum(len(v) for v in U["ctopics"].values()), 490)

    def test_demand_and_unis2(self):
        U, D = self.P["U"], self.P["D"]
        self.assertGreaterEqual(len(U["skills_joint"]), 22)                     # попит на всю ОП
        self.assertTrue(all(r["line"] and r["w"] is not None for r in U["skills_joint"]))
        self.assertIsNotNone(next(p for p in D["prog"] if p["key"] == "P6")["v"][0])
        self.assertGreaterEqual(len(U["unis2"]["rows"]), 10)                     # лінія ВБ2 проти ландшафту й просторового дизайну
        self.assertEqual(len(U["unis2"]["unis"]), 5)

    def test_paths_have_content(self):
        for c, p in self.P["X"]["paths"].items():
            self.assertTrue(p.get("verdict"), c)
            self.assertTrue(p.get("add") or p.get("keep"), c)

    # ---------- вигляд (шаблон) ----------
    def test_layout_frozen(self):
        t = self.tpl
        for needle, why in [
            (".wrap{max-width:1640px;", "широкий контент"),
            ("nav.tabs{display:flex;flex-wrap:wrap;", "меню без горизонтальної прокрутки"),
            ('id="gfBar"', "перемикачі циклів на всіх вкладках"),
            ("gfwrap{position:sticky", "перемикачі закріплені вгорі"),
            ('class="sgroup"', "зведення розбите за циклами"),
            ("tblwrap noscroll", "таблиця розривів без внутрішньої прокрутки"),
            ('preserveAspectRatio="xMidYMin meet"', "карта пререквізитів на всю ширину, по центру"),
            ('class="tblock"', "блоки тем у матриці"),
            ('data-m="course"', "режим «Теми курсів і повтори»"),
            ('class="tname pk" data-t="${t[0]}" tabindex="0" role="button" title="Показати, як тему вчать', "клікабельні теми у провідних програмах"),
            ("const cl=z=>Math.min(100,Math.max(40,z))", "лінія бала не виходить за шкалу"),
        ]:
            self.assertIn(needle, t, why)
        self.assertNotIn("first.open=true", t, "шляхи вдосконалення мають бути згорнуті")


if __name__ == "__main__":
    unittest.main()

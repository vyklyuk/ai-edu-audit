# -*- coding: utf-8 -*-
"""Схеми коректні, еталонні файли їм відповідають. Пропускається, якщо немає jsonschema."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from ai_edu_audit import schemas  # noqa: E402
from ai_edu_audit.io import read_json, read_jsonl  # noqa: E402

try:
    import jsonschema
    if not hasattr(jsonschema, "Draft202012Validator"):  # потрібна jsonschema >= 4
        jsonschema = None
except ModuleNotFoundError:  # pragma: no cover
    jsonschema = None

REF = os.path.join(ROOT, "data", "reference", "line1")


@unittest.skipIf(jsonschema is None, "pip install 'jsonschema>=4.18'")
class Schemas(unittest.TestCase):
    def test_schemas_valid(self):
        for n in schemas.NAMES:
            jsonschema.Draft202012Validator.check_schema(schemas.load(n))

    def test_reference_files(self):
        self.assertEqual(schemas.errors("line_inputs", read_json(os.path.join(REF, "line.json"))), [])
        self.assertEqual(schemas.errors("data_line", read_json(os.path.join(REF, "expected", "data.json"))), [])
        for r in read_jsonl(os.path.join(REF, "courses.jsonl")):
            self.assertEqual(schemas.errors("course", r), [], r["ok"])

    def test_finding_requires_evidence(self):
        f = dict(id="F1", type="grounding", severity="blocking", where={"course": "ОК45"},
                 problem="тема не знайдена в РП", evidence="", suggestion="прибрати", source="auto")
        self.assertTrue(schemas.errors("finding", f))
        f["evidence"] = "цитата відсутня в нормалізованому тексті, с. 3"
        self.assertEqual(schemas.errors("finding", f), [])


if __name__ == "__main__":
    unittest.main()

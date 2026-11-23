# -*- coding: utf-8 -*-
"""Одноразове перетворення еталонного build_data.py лінії 1 на вхідні дані line.json.

Виконує build_data.py в окремій теці (щоб не перезаписати еталонний data.json), забирає
його константи і розкладає їх на:
  * методику (перевіряється на збіг з ai_edu_audit.calc.methodology);
  * вхідні дані лінії (line.json) — те, що в майбутньому наповнюють агенти.

Запуск:  python tools/extract_reference.py <тека з build_data.py і courses.jsonl> <вихідний line.json>
"""
import json
import os
import runpy
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from ai_edu_audit.calc import methodology as M  # noqa: E402


def run_reference(src_dir):
    tmp = tempfile.mkdtemp()
    for f in ("build_data.py", "courses.jsonl"):
        shutil.copy(os.path.join(src_dir, f), tmp)
    ns = runpy.run_path(os.path.join(tmp, "build_data.py"), run_name="reference")
    return ns


def diff_states(arr_by_metric):
    """{metric: [b, w1, w2]} -> before | None, w1 overrides, w2 overrides (накопичувально)."""
    codes = [c for c in M.METRIC_CODES if c in arr_by_metric]
    before_all_none = all(arr_by_metric[c][0] is None for c in codes)
    before = None if before_all_none else {c: arr_by_metric[c][0] for c in codes}
    base = before or {}
    w1 = {c: arr_by_metric[c][1] for c in codes if before is None or arr_by_metric[c][1] != base.get(c)}
    w1_full = dict(base, **w1)
    w2 = {c: arr_by_metric[c][2] for c in codes if arr_by_metric[c][2] != w1_full.get(c)}
    return before, w1, w2


def main(src_dir, out_path):
    ns = run_reference(src_dir)

    # 1. Методика має збігатися з еталоном
    def norm(x):
        return json.loads(json.dumps(x))
    assert norm(ns["MDEF"]) == norm(M.MDEF), "MDEF розійшлося з еталоном"
    assert ns["WEIGHTS"] == M.WEIGHTS and ns["DIMN"] == M.DIMN
    for p in ns["PM"]:
        assert M.PDEF[p[0]] == (p[5], p[6], p[7]), p[0]

    line = ns["LINE"]
    passport = [dict(code=r[0], title=r[1], role=r[2], sem=r[3],
                     opp=dict(credits=r[4], control=r[5]),
                     rp=dict(status=r[6], year=r[7], credits=r[8], control=r[9], kind=r[10], codes=r[11]),
                     issues=r[12]) for r in ns["PASSPORT"]]
    sem_from_passport = {r[0]: r[3] for r in ns["PASSPORT"]}
    sem_extra = {k: v for k, v in ns["SEM"].items() if k not in sem_from_passport}

    links = [dict(src=l[0], dst=l[1], kind=l[2], as_written=l[3]) for l in ns["LINKS"]]
    topics = [dict(key=t[0], name=t[1], cov=t[2], comment=t[3]) for t in ns["TOPICS"]]

    roles = [dict(key="da", name="Data Analyst", n=2585), dict(key="de", name="Data Engineer", n=6877)]
    skills = [dict(name=s[0], share=dict(da=s[1], de=s[2]), coverage=[s[3], s[4], s[5]],
                   where=dict(before=s[6], after=s[7])) for s in ns["SKILLS"]]

    unis = [dict(name=u[0], courses=u[1], country=u[2]) for u in ns["UNIS"]]

    course_metrics = []
    for c, arr in ns["CM"].items():
        before, w1, w2 = diff_states(arr)
        course_metrics.append(dict(ok=c, before=before, w1=w1, w2=w2))

    # Програмні метрики: значення, які в еталоні обчислюються, замінено на посилання {"calc": ...}
    calc_refs = {
        ("P1", 0): {"calc": "rp_completeness"},
        ("P4", 0): {"calc": "links_valid_share"},
        ("P5", 0): {"calc": "dup_share"}, ("P5", 1): {"calc": "dup_share"},
        ("P6", 0): {"calc": "b1", "state": 0}, ("P6", 1): {"calc": "b1", "state": 1}, ("P6", 2): {"calc": "b1", "state": 2},
        ("P7", 0): {"calc": "consensus_coverage"}, ("P7", 1): {"calc": "consensus_coverage"},
        ("P8", 0): {"calc": "lit_median_age"},
        ("P9", 0): {"calc": "practice_share"}, ("P9", 1): {"calc": "practice_share"},
    }
    note_templates = {
        "P4": "{links_valid} коректних із {links_total} заявлених зв'язків лінії",
        "P7": "консенсус — теми, присутні у ≥5 з 9 програм ({consensus_n} тем)",
    }
    program_metrics = []
    for p in ns["PM"]:
        vals = [calc_refs.get((p[0], i), p[2 + i]) for i in range(3)]
        program_metrics.append(dict(key=p[0], name=p[1], values=vals, note=note_templates.get(p[0], p[8])))

    data = {
        "schema_version": "1.0",
        "meta": {
            "program": "ОПП «Комп'ютерні науки (Системи штучного інтелекту)» 2026, бакалавр",
            "institution": "НУ «Львівська політехніка», кафедра систем штучного інтелекту",
            "line_id": "line1",
            "line_name": "Інтелектуальний аналіз даних",
            "profile": "it",
            "level": "bachelor",
            "sources": {
                "demand": "InterviewStack, травень 2026 (DA n=2585, DE n=6877)",
            },
            "provenance": "перенесено з еталонного build_data.py (tools/extract_reference.py)",
        },
        "year": ns["YEAR"],
        "line": line,
        "passport": passport,
        "sem_extra": sem_extra,
        "links": links,
        "cols": ns["COLS"],
        "topics": topics,
        "owner": ns["OWNER"],
        "demand": {"roles": roles, "skills": skills},
        "universities": {"list": unis, "topic_coverage": ns["UNI_T"]},
        "course_metrics": course_metrics,
        "program_metrics": program_metrics,
        "pilot": ns["data"]["pilot"],
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("записано", out_path)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

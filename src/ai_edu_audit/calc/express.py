# -*- coding: utf-8 -*-
"""Експрес-оцінка ліній з даних етапу I.1 (без ринку й університетів) і пріоритет поглиблення.

Обчислюються лише ті програмні метрики, для яких є дані:
  P1 повнота корпусу РП, P2 готовність РП до ОП (форма контролю, коди компетентностей/ПРН з ОП),
  P3 забезпеченість спеціальних компетентностей лінії (для ліній вибіркових), P4 цілісність пререквізитів,
  P8 медіанний вік літератури, P10 узгодженість оцінювання, P12 політика ШІ.
Експрес-індекс = середній бал обчислених метрик; пріоритет = кредити × (100 − індекс).
"""
import math
import re
import statistics

from ..ingest.inventory import base_title, ratio
from .line import link_verdict
from .scoring import pscore

NAMES = {
    "P1": "Повнота корпусу РП лінії", "P2": "Готовність РП до ОП", "P3": "Забезпеченість компетентностей лінії в РП",
    "P4": "Цілісність пререквізитів", "P8": "Медіанний вік літератури, років", "P10": "Узгодженість оцінювання",
    "P12": "Політика ШІ в РП",
}


def resolve_course(name, courses, min_ratio=0.8):
    """Назва дисципліни як написано в РП -> код ОК (або None)."""
    b = base_title(name)
    best, code = 0, None
    for c in courses:
        r = ratio(b, base_title(c["title"]))
        if r > best:
            best, code = r, c["code"]
    return code if best >= min_ratio else None


def resolve_links(rows, program):
    courses = program["courses"]
    sem = {c["code"]: (c["semesters"][0] if c["semesters"] else None) for c in courses}
    links = []
    for r in rows:
        if r["status"] != "ok":
            continue
        for kind, lst in (("prereq", r.get("prereq", [])), ("next", r.get("next", []))):
            for name in lst:
                other = resolve_course(name, courses)
                src, dst = (other, r["ok"]) if kind == "prereq" else (r["ok"], other)
                if src is None or dst is None:
                    v = "absent"
                    src = src or name
                    dst = dst if dst is not None else None
                elif sem.get(src) is None or sem.get(dst) is None:
                    v = "unknown"
                else:
                    v = link_verdict(src, dst, "prereq", sem)
                links.append(dict(src=src, dst=dst, kind=kind, as_written=name, verdict=v, from_rp=r["ok"]))
    return links, sem


def express_line(line, rows, program, links, year=2026):
    by = {r["ok"]: r for r in rows}
    codes = line["courses"]
    present = [by[c] for c in codes if by.get(c, {}).get("status") == "ok"]
    defined = {c["code"] for c in program["competences"]} | {c["code"] for c in program["outcomes"]}
    opp = {c["code"]: c for c in program["courses"]}
    vals, notes = {}, {}

    vals["P1"] = len(present) / len(codes)
    notes["P1"] = f"{len(present)} із {len(codes)} ОК мають РП/силабус"

    checks = passed = 0
    for r in present:
        checks += 2
        passed += int(r.get("control") == opp[r["ok"]]["control"])
        used = set(r.get("comps", [])) | set(r.get("prn", []))
        passed += int(bool(used) and used <= defined)
    vals["P2"] = passed / checks if checks else None
    notes["P2"] = f"{passed} із {checks} перевірок: форма контролю = ОП; усі коди компетентностей/ПРН є в ОП"

    if line["id"].startswith(("L5", "L6")):
        own = [r for r in present if any(c.startswith(("СКЛ", "ФКС")) for c in r.get("comps", []))
               or any(p.startswith(("ПРНВ", "ПРНЛ")) for p in r.get("prn", []))]
        vals["P3"] = len(own) / len(present) if present else None
        notes["P3"] = f"{len(own)} із {len(present)} РП посилаються на компетентності/ПРН лінії (СКЛ/ФКС, ПРНЛ)"

    le = [l for l in links if (l["src"] in codes or l["dst"] in codes) and l["verdict"] != "unknown"]
    ok = sum(1 for l in le if l["verdict"] == "ok")
    vals["P4"] = ok / len(le) if le else None
    notes["P4"] = f"{ok} коректних із {len(le)} заявлених зв'язків (семестри — з тек)"

    lit = [y for r in present for y in r.get("lit_years", [])]
    vals["P8"] = year - statistics.median(lit) if lit else None
    notes["P8"] = f"медіана по {len(lit)} джерелах {len(present)} РП"

    cons = sum(1 for r in present if r.get("control") == opp[r["ok"]]["control"]
               and (not r.get("assessment") or sum(v for v in r["assessment"].values() if isinstance(v, (int, float))) in (0, 100)))
    vals["P10"] = cons / len(present) if present else None
    notes["P10"] = f"{cons} із {len(present)} РП без розбіжностей оцінювання"

    ai = sum(1 for r in present if r.get("ai_policy"))
    vals["P12"] = ai / len(present) if present else None
    notes["P12"] = f"{ai} із {len(present)} РП мають політику ШІ"

    metrics = []
    for k, v in vals.items():
        if v is None:
            continue
        metrics.append(dict(key=k, name=NAMES[k], v=round(v, 3), s=round(pscore(k, NAMES[k], v), 1), note=notes[k]))
    idx = round(math.fsum(m["s"] for m in metrics) / len(metrics), 1) if metrics else None
    credits = sum(opp[c]["credits"] for c in codes)
    return dict(id=line["id"], name=line["name"], courses=codes, credits=credits, present=len(present),
                metrics=metrics, express_index=idx,
                priority=round(credits * (100 - idx), 1) if idx is not None and not line.get("light") else None,
                light=bool(line.get("light")))


def express_all(lines, rows, program):
    links, sem = resolve_links(rows, program)
    out = [express_line(l, rows, program, links) for l in lines["lines"]]
    ranked = sorted([o for o in out if o["priority"] is not None], key=lambda o: -o["priority"])
    return dict(lines=out, ranking=[o["id"] for o in ranked], links=links, semesters=sem)

# -*- coding: utf-8 -*-
"""Розрахунок даних хабу лінії (об'єкт D) з вхідних даних лінії і корпусу РП.

Вхід:
  line  — вміст line.json (паспорт, зв'язки, теми, попит, університети, значення метрик курсів,
          програмні метрики); у майбутньому його наповнюють агенти витягу й дослідження;
  courses — рядки courses.jsonl (витяг РП).
Вихід: словник data_line (= data.json = об'єкт D хабу).

Код не містить жодних даних конкретної ОП: усе приходить у line.json.
Логіку перенесено з еталонного build_data.py лінії 1; регресійний тест вимагає побайтового збігу.
"""
import math
import statistics

from . import methodology as M
from .scoring import pscore, problem, score, total

STATES = 3  # до, після хвилі 1, після хвилі 2


# ---------- допоміжне ----------

def _passport_rows(line):
    rows = []
    for p in line["passport"]:
        opp, rp = p["opp"], p["rp"]
        rows.append([p["code"], p["title"], p["role"], p["sem"], opp["credits"], opp["control"],
                     rp["status"], rp["year"], rp["credits"], rp["control"], rp["kind"], rp["codes"],
                     p["issues"]])
    return rows


def _sem_map(line):
    sem = {p["code"]: p["sem"] for p in line["passport"]}
    sem.update(line.get("sem_extra", {}))
    return sem


def link_verdict(src, dst, kind, sem):
    """ok | same | late | absent — чи не суперечить зв'язок порядку семестрів."""
    if dst is None:
        return "absent"
    sa, sb = sem.get(src), sem.get(dst)
    if kind == "coreq":
        return "ok" if sa == sb else "late"
    if sa < sb:
        return "ok"
    if sa == sb:
        return "same"
    return "late"


def _skill_rows(demand):
    roles = [r["key"] for r in demand["roles"]]
    rows = []
    for s in demand["skills"]:
        rows.append([s["name"], *[s["share"][r] for r in roles], *s["coverage"],
                     s["where"]["before"], s["where"]["after"]])
    return rows, roles


def demand_b1(demand, state):
    """Зважене покриття одиниць попиту (вага — середня частка за ролями)."""
    roles = [r["key"] for r in demand["roles"]]

    def w(s):
        return sum(s["share"][r] for r in roles) / len(roles)
    num = math.fsum(w(s) * s["coverage"][state] for s in demand["skills"])
    den = math.fsum(w(s) for s in demand["skills"])
    return num / den


def demand_b2(demand, state):
    """Частка ядра попиту (≥ порогу хоча б для однієї ролі), покритого повністю."""
    roles = [r["key"] for r in demand["roles"]]
    core = [s for s in demand["skills"] if max(s["share"][r] for r in roles) >= M.DEMAND_CORE_MIN]
    return sum(1 for s in core if s["coverage"][state] >= 1) / len(core)


def course_metric_states(entry):
    """before | None, w1 = before ∪ w1, w2 = w1 ∪ w2  ->  {metric: [b, w1, w2]} у порядку MDEF."""
    before = entry.get("before")
    w1 = dict(before or {}, **entry.get("w1", {}))
    w2 = dict(w1, **entry.get("w2", {}))
    codes = [c for c in M.METRIC_CODES if c in w2 or (before and c in before)]
    return {c: [None if before is None else before.get(c), w1.get(c), w2.get(c)] for c in codes}


def course_scores(cm_vals):
    out = []
    for i in range(STATES):
        v = {k: vv[i] for k, vv in cm_vals.items()}
        if all(x is None for x in v.values()):
            out.append(None)
            continue
        raw, fin, veto, dsc = total(v)
        out.append(dict(raw=round(raw, 1), final=round(fin, 1), veto=veto,
                        dims={d: round(s, 1) for d, s in dsc.items()},
                        scores={m[0]: (None if v[m[0]] is None else round(score(m, v[m[0]]), 1)) for m in M.MDEF},
                        problems=[m[0] for m in M.MDEF if v.get(m[0]) is not None and problem(m, v[m[0]])]))
    return out


# ---------- головна функція ----------

def build_line_data(line, courses):
    year = line["year"]
    line_codes = line["line"]
    passport = _passport_rows(line)
    sem = _sem_map(line)

    links = []
    for l in line["links"]:
        links.append([l["src"], l["dst"], l["kind"], l["as_written"],
                      link_verdict(l["src"], l["dst"], l["kind"], sem)])

    topics = [[t["key"], t["name"], t["cov"], t["comment"]] for t in line["topics"]]
    demand = line["demand"]
    skills, _roles = _skill_rows(demand)
    unis = [[u["name"], u["courses"], u["country"]] for u in line["universities"]["list"]]
    uni_t = line["universities"]["topic_coverage"]

    cm = {}
    for entry in line["course_metrics"]:
        cm[entry["ok"]] = course_metric_states(entry)
    cscores = {c: course_scores(v) for c, v in cm.items()}

    # ---- обчислювані складові програмних метрик ----
    line_set = set(line_codes)
    rp_ok = [p for p in line["passport"] if p["code"] in line_set and p["rp"]["status"] == "ok"]
    rp_in_line = [p for p in line["passport"] if p["code"] in line_set and p["role"] == "line"]
    rp_ok = [p for p in rp_ok if p["role"] == "line"]

    lit = []
    for r in courses:
        if r["ok"] in line_set:
            lit += r.get("lit_years", [])

    links_eval = [l for l in links if l[1] in line_set or l[0] in line_set]
    links_valid = sum(1 for l in links_eval if l[4] == "ok")

    consensus = [t["key"] for t in line["topics"]
                 if sum(1 for x in uni_t[t["key"]] if x) >= M.CONSENSUS_MIN_PROGRAMS]

    def line_cov(t):
        vals = [v for v in t["cov"].values() if v]
        return max(vals) if vals else 0

    present = {r["ok"]: r for r in courses if r["ok"] in line_set}
    lab_h = [present[c].get("hours", {}).get("lab", 0) for c in line_codes if c in present and present[c].get("hours")]
    aud_h = [sum(present[c]["hours"].get(k, 0) for k in ("lec", "lab", "prac")) for c in line_codes
             if c in present and present[c].get("hours")]

    calc = {
        "rp_completeness": lambda st: len(rp_ok) / len(rp_in_line),
        "links_valid_share": lambda st: links_valid / len(links_eval),
        "dup_share": lambda st: sum(1 for t in line["topics"]
                                    if sum(1 for v in t["cov"].values() if v) >= M.DUP_MIN_COURSES) / len(line["topics"]),
        "b1": lambda st: demand_b1(demand, st),
        "consensus_coverage": lambda st: sum(1 for t in line["topics"]
                                             if t["key"] in consensus and line_cov(t) == 2) / len(consensus),
        "lit_median_age": lambda st: (year - statistics.median(lit)) if lit else None,
        "practice_share": lambda st: (math.fsum(lab_h) / math.fsum(aud_h)) if aud_h and math.fsum(aud_h) else None,
    }
    note_ctx = dict(links_valid=links_valid, links_total=len(links_eval), consensus_n=len(consensus))

    def resolve(v):
        if isinstance(v, dict) and "calc" in v:
            return calc[v["calc"]](v.get("state", 0))
        return v

    prog = []
    for p in line["program_metrics"]:
        vals = [resolve(v) for v in p["values"]]
        t, a, hi = M.PDEF[p["key"]]
        prog.append(dict(key=p["key"], name=p["name"], v=[None if x is None else round(x, 3) for x in vals],
                         target=t, accept=a, hi=hi, note=p["note"].format(**note_ctx),
                         s=[None if x is None else round(pscore(p["key"], p["name"], x), 1) for x in vals]))
    # метрика без даних (None) не входить в індекс; на еталоні лінії 1 таких немає
    prog_index = []
    for i in range(STATES):
        ss = [p["s"][i] for p in prog if p["s"][i] is not None]
        prog_index.append(round(math.fsum(ss) / len(ss), 1) if ss else None)

    return dict(
        passport=passport, links=links, sem=sem, cols=line["cols"], topics=topics, line=line_codes,
        owner=line["owner"], skills=skills,
        b1=[round(demand_b1(demand, i), 3) for i in range(STATES)],
        b2=[round(demand_b2(demand, i), 3) for i in range(STATES)],
        unis=unis, uni_t=uni_t, consensus=consensus,
        mdef=[[m[0], m[1], m[2], m[3], m[4], m[5], m[6]] for m in M.MDEF],
        dimn=M.DIMN, weights=M.WEIGHTS, cm=cm, cscores=cscores, prog=prog, prog_index=prog_index,
        pilot=line["pilot"],
    )

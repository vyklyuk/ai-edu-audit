# -*- coding: utf-8 -*-
"""Хаб усієї ОП (зафіксована версія v1): line.json (усі компоненти), data.json, recs.json, details.json, ui.json.

Запуск: PYTHONPATH=src python3 -m ai_edu_audit.program runs/<прогон>
Загальний код — тут; судження аудитора для конкретної ОП — у <прогон>/program/:
  notes_program.py  — цикли ОП і тексти висновків;   topics_program.py — матриця тем;
  unis_program.py   — покриття тем у провідних програмах;   paths_program.py — шляхи вдосконалення курсів.
Потрібна також поглиблено проаудитована лінія (<прогон>/line_L1/): її теми, докази, попит і рекомендації переносяться як є.
"""
import json, os, re, statistics, sys
from collections import Counter

RUN = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
HERE = os.path.join(RUN, "program")
L1D = os.path.join(RUN, "line_L1")
sys.path.insert(0, HERE)          # модулі з судженнями аудитора для цієї ОП
import notes_program as NP  # noqa: E402
from ai_edu_audit.calc import methodology as M  # noqa: E402
from ai_edu_audit.calc.line import build_line_data  # noqa: E402
from ai_edu_audit.calc.express import express_line  # noqa: E402

J = lambda *p: json.load(open(os.path.join(*p), encoding="utf-8"))
YEAR = 2026
prog = J(RUN, "program.json")
rows = {json.loads(l)["ok"]: json.loads(l) for l in open(os.path.join(RUN, "courses.jsonl"), encoding="utf-8")}
LA = J(RUN, "links_all.json")["links"]
L1 = J(L1D, "line.json"); D1 = J(L1D, "data.json"); U1 = J(L1D, "ui.json"); X1 = J(L1D, "details.json"); R1 = J(L1D, "recs.json")
opp = {c["code"]: c for c in prog["courses"]}
ALL = [c["code"] for c in prog["courses"]]
L1C = L1["line"]
GROUP = {c: next(k for k, n, pref in NP.CYCLES if any(c.startswith(p) for p in pref)) for c in ALL}
GNAME = {k: n for k, n, pref in NP.CYCLES}
sem = {c: (min(opp[c]["semesters"]) if opp[c]["semesters"] else None) for c in ALL}
OKS = [c for c in ALL if rows[c]["status"] == "ok"]
MISS = [c for c in ALL if rows[c]["status"] != "ok"]

prn_text = {o["code"]: o["text"] for o in prog["outcomes"]}
defined = {c["code"] for c in prog["competences"]} | set(prn_text)
HIGH_VERBS = re.compile(r"(?i)^(аналіз|оцін|створ|розроб|проєкт|проект|формув|обґрунт|обгрунт|синтез|інтерпрет|трансформ|відобра|застосов|вирішув|викон)")


def g1_parts(r):
    out = []
    for n in r["notes"]:
        if n.startswith("форма контролю") or n.startswith("сума виділених балів") or n.startswith("згадано спеціальність"):
            out.append(n)
    bad = sorted({p for p in r["prn"] + r["comps"] if p not in defined})
    if bad:
        out.append("коди, яких немає в ОП: " + ", ".join(bad))
    return out


def metric_generic(c):
    r = rows[c]
    m = {k: None for k in M.METRIC_CODES}
    prns = [p for p in r["prn"] if p in prn_text]
    if prns:
        m["A4"] = round(sum(1 for p in prns if HIGH_VERBS.match(prn_text[p])) / len(prns), 2)
    if r["lit_years"]:
        m["C1"] = YEAR - statistics.median(r["lit_years"])
    meth = (r.get("summary", "") + " " + " ".join(e["quote"] for e in r["evidence"] if e["field"] in ("control", "assessment"))
            + " " + " ".join(map(str, (r.get("assessment") or {}).keys()))).lower()
    forms = sum(1 for pat in (r"перегляд", r"тест", r"самостійн", r"контрольн", r"опитув", r"захист", r"практичн\w* завдан|аудиторн\w* робіт|постановк|лаборатор")
                if re.search(pat, meth))
    m["F2"] = forms or None
    m["G1"] = len(g1_parts(r))
    m["D1"] = D1_of(c)
    ts = [t for t, cv in topic_cov.items() if (cv.get(c) or 0) >= 1 and any(x is not None for x in UNI_T[t])]
    if ts:
        m["D2"] = round(sum(1 for t in ts if not any(UNI_T[t])) / len(ts), 2)
        ct = [t for t in ts if t in CONS]
        m["D3"] = round(sum(1 for t in ct if topic_cov[t].get(c) == 2) / len(ct), 2) if ct else None
    return m


# ---------- матриця тем усієї ОП (етап 2) ----------
import topics_program as TP  # noqa: E402
from ai_edu_audit.ingest.convert import find_quote  # noqa: E402
TOPICS = []
for t in L1["topics"]:
    cov = dict(t["cov"]); cov.update(TP.EXTEND.get(t["key"], {}))
    TOPICS.append(dict(key=t["key"], name=t["name"], cov=cov, comment=t["comment"], block="A"))
for k, b, n, cov, cm, kw in TP.NEW:
    TOPICS.append(dict(key=k, name=n, cov=cov, comment=cm, block=b))
KW = {k: kw for k, b, n, cov, cm, kw in TP.NEW}; KW.update(TP.KW_OLD)
import unis_program as UP  # noqa: E402
UNAMES = [u["name"] for u in L1["universities"]["list"]]
UNI_T = dict(L1["universities"]["topic_coverage"])
UNI_MAP_NEW = {}
for t in TOPICS:
    if t["key"] in UNI_T:
        continue
    row = [None] * len(UNAMES)
    for i, (v, crs) in UP.U.get(t["key"], {}).items():
        row[i] = v
        if v and crs:
            UNI_MAP_NEW[f"{UNAMES[i]}|{t['key']}"] = crs
    UNI_T[t["key"]] = row
CONS = [k for k, v in UNI_T.items() if sum(1 for x in v if x) >= M.CONSENSUS_MIN_PROGRAMS]
topic_cov = {t["key"]: t["cov"] for t in TOPICS}
inv = J(RUN, "inventory.json"); TXT = {f["rel"]: f["text_file"] for f in inv["files"] if f.get("text_file")}
EV = {t: dict(v) for t, v in X1["evidence"].items()}
ev_bad = []


def _sents(text):
    return [x.strip() for x in re.split(r"(?<=[.!?;])\s+|\s+\|\s+", text) if len(x.strip()) > 12]


def find_evidence(c, t, v):
    r = rows[c]
    src = [r.get("description", ""), r.get("summary", ""), " | ".join(r.get("lectures") or []), r.get("goal", "")]
    best, sc = None, 0
    for part in src:
        for x in _sents(part):
            k = sum(1 for p in KW.get(t, []) if re.search(p, x, re.I))
            if k > sc:
                best, sc = x, k
    if not best:
        return None
    best = best if len(best) <= 230 else best[:227].rsplit(" ", 1)[0] + "…"
    pages = open(os.path.join(RUN, TXT[r["file"]]), encoding="utf-8").read().split("\f")
    q = best.rstrip("…")[:120]
    if find_quote(pages, q) is None and find_quote(pages, q.replace("-", "")) is None:   # перенос/дефіс, втрачений при конвертації
        ev_bad.append((t, c))
    return ("Завдання" if v == 2 else "Згадка") + f": «{best}»"


for t in TOPICS:
    for c, v in t["cov"].items():
        if t["key"] in EV and c in EV[t["key"]]:
            continue
        if v is None:
            EV.setdefault(t["key"], {})[c] = f"Силабуса немає; тема очікується за назвою компонента в ОП («{opp[c]['title']}»)."
            continue
        if not v:
            continue
        e = find_evidence(c, t["key"], v)
        EV.setdefault(t["key"], {})[c] = e or "Тема — за переліком тем силабуса."


def D1_of(c):
    ts = [t for t, cv in topic_cov.items() if (cv.get(c) or 0) >= 1]
    if not ts:
        return None
    return round(sum(1 for t in ts if sum(1 for k, v in topic_cov[t].items() if k != c and (v or 0) >= 1) >= 2) / len(ts), 2)


cm_L1 = {e["ok"]: e for e in L1["course_metrics"]}
course_metrics = []
for c in OKS:
    if c in cm_L1:
        course_metrics.append(cm_L1[c]); continue
    b = metric_generic(c)
    w1 = {"G1": 0}
    if b["C1"] is not None and b["C1"] > 6:
        w1["C1"] = 6
    if b["F2"] is not None:
        w1["F2"] = min(b["F2"] + 1, 5)
    w2 = {}
    if b["A4"] is not None and b["A4"] < 0.5:
        w2["A4"] = 0.5
    course_metrics.append(dict(ok=c, before=b, w1=w1, w2=w2))


def codes_note(r):
    bad = sorted({p for p in r["prn"] + r["comps"] if p not in defined})
    return "коди з ОП" if not bad else f"є коди, яких немає в ОП: {', '.join(bad)}"


passport = []
for c in ALL:
    r, o = rows[c], opp[c]
    passport.append(dict(code=c, title=o["title"], role="line", sem=sem[c], opp=dict(credits=o["credits"], control=o["control"]),
                         rp=dict(status=r["status"], year=None, credits=None, control=r.get("control"), kind="силабус",
                                 codes=codes_note(r) if r["status"] == "ok" else None),
                         issues=[n for n in r["notes"] if "тематичного плану" not in n]))

links = [dict(src=a, dst=b, kind=("coreq" if k == "coreq" else "prereq"), as_written=f"{t} (у силабусі {me})")
         for a, b, k, t, v, me in LA if v != "unknown"]

# програмні метрики: детерміновані — тим самим кодом, що й експрес-аудит, на всій ОП
ex_links = [dict(src=a, dst=b, kind=k, as_written=t, verdict=("ok" if v == "ok" else v), from_rp=me) for a, b, k, t, v, me in LA]
ex = express_line(dict(id="OP", name="ОП", courses=ALL), list(rows.values()), prog, ex_links, year=YEAR)
EXM = {m["key"]: m for m in ex["metrics"]}
claimed = set()
for c in OKS:
    claimed |= set(rows[c]["comps"]) | set(rows[c]["prn"])
core = [x["code"] for x in prog["competences"] + prog["outcomes"] if re.match(r"^(ЗК|ФК|ПРН)\d", x["code"])]
p3 = round(sum(1 for x in core if x in claimed) / len(core), 3) if core else None
nolit = sum(1 for c in OKS if not rows[c]["lit_years"])
# ---------- зовнішній попит на всю ОП (етап 3) ----------
import demand_program as DP  # noqa: E402
DROLES = ["ri", "rs"]
DN = {r: sum(1 for v in DP.VAC if v[0] == r) for r in DROLES + ["ab"]}
DSH = {c: {r: round(100 * sum(1 for v in DP.VAC if v[0] == r and c in v[3]) / DN[r]) for r in DROLES + ["ab"]} for c, *_ in DP.UNITS}
DEMAND = {"roles": [dict(key="ri", name="Дизайнер інтер'єру (Україна)"), dict(key="rs", name="Дизайнер просторів і ландшафту (Україна)")],
          "skills": [dict(name=n, share={r: DSH[c][r] for r in DROLES}, coverage=[now, now, aft],
                          where=dict(before="; ".join(f"{a} {b}" for a, b in wn) or "—", after="; ".join(f"{a} {b}" for a, b in wa) or "—"),
                          sources=[dict(url=v[2], date="23.11.2026") for v in DP.VAC if c in v[3]][:3])
                     for c, n, now, aft, wn, wa in DP.UNITS]}

program_metrics = [
 dict(key="P1", name="Повнота корпусу РП програми", values=[EXM["P1"]["v"], 1.0, 1.0], note=EXM["P1"]["note"] + "; хвиля 1 — написати 9 відсутніх силабусів"),
 dict(key="P2", name="Готовність РП до ОП", values=[EXM["P2"]["v"], 1.0, 1.0], note=EXM["P2"]["note"]),
 dict(key="P3", name="Забезпеченість компетентностей і ПРН ОП силабусами", values=[p3, 1.0, 1.0],
      note=f"{sum(1 for x in core if x in claimed)} із {len(core)} ЗК/ФК/ПРН ОП заявлено хоча б в одному силабусі"),
 dict(key="P4", name="Цілісність пререквізитів", values=[{"calc": "links_valid_share"}, 0.9, 0.95],
      note="{links_valid} коректних із {links_total} заявлених зв'язків з відомими семестрами (з розділу «попередні та супутні» всіх силабусів)"),
 dict(key="P5", name="Частка тем, що дублюються в ≥3 курсах", values=[{"calc": "dup_share"}, {"calc": "dup_share"}, None],
      note=f"{len(TP.NEW) + 17} тем програми; хвиля 2 (один власник на тему) — після етапу 5"),
 dict(key="P6", name="Покриття зовнішнього попиту (B1 програми)", values=[{"calc": "b1", "state": 0}, {"calc": "b1", "state": 1}, {"calc": "b1", "state": 2}],
      note=f"{len(DP.UNITS)} одиниць попиту всієї ОП; ваги — частки у вибірці українських вакансій (n = {DN['ri']} + {DN['rs']})"),
 dict(key="P7", name="Покриття консенсусного ядра провідних програм", values=[{"calc": "consensus_coverage"}, {"calc": "consensus_coverage"}, None],
      note="консенсус — теми, які є щонайменше в 5 із 7 провідних програм ({consensus_n} тем); тема покрита, якщо хоча б в одному курсі ОП є практичне завдання"),
 dict(key="P8", name="Медіанний вік літератури, років", values=[EXM["P8"]["v"], 6, 5], note=EXM["P8"]["note"]),
 dict(key="P9", name="Частка практики в аудиторних годинах", values=[None, None, None], note="н/д: немає навчального плану й годин (припущення A2)"),
 dict(key="P10", name="Узгодженість оцінювання (бали = 100, форма = ОП)", values=[EXM["P10"]["v"], 1.0, 1.0], note=EXM["P10"]["note"]),
 dict(key="P11", name="Цілісність проєктного ланцюжка", values=[None, None, None], note="оцінюється на етапі 5 (курсові проєкти КП по семестрах)"),
 dict(key="P12", name="Політика ШІ та ШІ-інструменти в РП", values=[EXM["P12"]["v"], 1.0, 1.0], note=EXM["P12"]["note"]),
]

line = {
 "schema_version": "1.0",
 "meta": dict(L1["meta"], line_id="OP", line_name="Освітня програма загалом",
              provenance="етап 1: детерміновані метрики всіх силабусів; змістові — для художньої підготовки, решта на етапах 2–5"),
 "year": YEAR, "line": ALL, "passport": passport, "sem_extra": {}, "links": links, "cols": ALL,
 "topics": [dict(key=t["key"], name=t["name"], cov=t["cov"], comment=t["comment"]) for t in TOPICS], "owner": L1["owner"], "demand": DEMAND,
 "universities": dict(L1["universities"], topic_coverage=UNI_T),
 "course_metrics": course_metrics, "program_metrics": program_metrics, "pilot": L1["pilot"],
}
json.dump(line, open(os.path.join(HERE, "line.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(os.path.join(HERE, "courses.jsonl"), "w", encoding="utf-8") as f:
    for c in ALL:
        f.write(json.dumps(rows[c], ensure_ascii=False) + "\n")
D = build_line_data(line, list(rows.values()))
json.dump(D, open(os.path.join(HERE, "data.json"), "w", encoding="utf-8"), ensure_ascii=False)

# ---------- recs (R) ----------
W1_BASE = "Тематичний план з годинами (перетворити силабус на повну РП)"


def verdict(c):
    r = rows[c]; parts = []
    for n in g1_parts(r):
        parts.append(n[:1].upper() + n[1:])
    if not r.get("ai_policy"):
        parts.append("політики ШІ немає")
    if r["lit_years"]:
        age = YEAR - statistics.median(r["lit_years"])
        if age > 8:
            parts.append(f"медіанний вік літератури {age:g} р.")
    else:
        parts.append("років видання в переліку літератури не знайдено")
    return ("; ".join(parts) + ".") if parts else "Формальних розбіжностей з ОП не знайдено."


def w1_list(c):
    r = rows[c]; out = []
    if any(n.startswith("форма контролю") for n in r["notes"]):
        out.append(f"Форма підсумкового контролю — як в ОП ({opp[c]['control']})")
    if any(n.startswith("сума виділених балів") for n in r["notes"]):
        out.append("Сума балів = 100, розподіл за видами робіт")
    if any(p not in defined for p in r["prn"] + r["comps"]):
        out.append("Коди компетентностей і ПРН — лише з переліку ОП")
    if any(n.startswith("згадано спеціальність") for n in r["notes"]):
        out.append("Прибрати згадку іншої спеціальності / програми")
    if not r.get("ai_policy"):
        out.append("Політика використання ШІ")
    if r["lit_years"] and YEAR - statistics.median(r["lit_years"]) > 6:
        out.append("Оновити базову літературу: щонайменше половина джерел — за останні 10 років")
    out.append(W1_BASE)
    return out


course = {}
for c in OKS:
    course[c] = R1["course"][c] if c in R1["course"] else dict(verdict=verdict(c), w1=w1_list(c),
                                                             w2=["Змістові рекомендації — на етапі 5 аудиту (після матриці тем, попиту й порівняння з провідними програмами)."])
cnt = lambda pred: [c for c in OKS if pred(rows[c])]
ctl = cnt(lambda r: any(n.startswith("форма контролю") for n in r["notes"]))
sums = cnt(lambda r: any(n.startswith("сума виділених балів") for n in r["notes"]))
codes = cnt(lambda r: any(p not in defined for p in r["prn"] + r["comps"]))
spec = cnt(lambda r: any(n.startswith("згадано спеціальність") for n in r["notes"]))
noai = cnt(lambda r: not r.get("ai_policy"))
oldlit = cnt(lambda r: r["lit_years"] and YEAR - statistics.median(r["lit_years"]) > 6)
rng = lambda l: f"{len(l)} курсів"
wave1 = [[f"гарант і викладачі", f"написати силабуси для {len(MISS)} компонентів: " + ", ".join(MISS), "P1"],
         [f"викладачі {rng(ctl)}", "форма контролю як в ОП", "P2, P10, G1"],
         [f"викладачі {rng(sums)}", "сума балів = 100", "P10, G1"],
         [f"викладачі {rng(codes)}", "коди компетентностей і ПРН лише з ОП (ПРН21–23, ФКС тощо)", "P2, G1"],
         [f"викладачі {rng(spec)}", "прибрати згадки іншої спеціальності", "G1"],
         [f"викладачі {rng(noai)}", f"політика використання ШІ (зразок — {NP.AI_SAMPLE})", "P12"],
         [f"викладачі {rng(oldlit)}", "оновити базову літературу", "P8, C1"],
         [f"усі {len(OKS)} курсів", "тематичний план з годинами — повна РП замість силабуса", "13 метрик курсу стають вимірними"]]
R = dict(course=course, wave1=wave1, line=R1["line"],
         opp=R1["opp"] + NP.OPP_EXTRA)
json.dump(R, open(os.path.join(HERE, "recs.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- теми силабусів і їх повтори ----------
from ai_edu_audit.program.course_topics import compare  # noqa: E402
CT = compare(rows, sem, OKS)
ct_cnt = Counter(x[2] for v in CT.values() for x in v)

# ---------- шляхи вдосконалення для всіх компонентів (етап 5) ----------
import paths_program as PP  # noqa: E402
CT_ = compare(rows, sem, OKS) if "CT" not in globals() else CT
PATHS = dict(X1["paths"])
for c in ALL:
    if c in PATHS:
        continue
    cur = PP.P[c]
    tl = CT_.get(c, [])
    now = []
    for t, b, st, h in tl:
        if t not in now:
            now.append(t)
    rm = cur.get("rm")
    whole = False
    if rm is None:
        by = {}
        for t, b, st, h in tl:
            if st == "repeat" and h:
                by.setdefault(h[0][0], []).append(t)
        rm = [[f"{len(ts)} тем(и), що повторюють {d}: " + "; ".join(dict.fromkeys(ts).keys())[:160], f"{d} «{opp[d]['title']}»",
               "розвести зміст: тема лишається в одному курсі, інший посилається на нього"] for d, ts in by.items()]
    if cur.get("rm") is None:
        rm_titles = {t for t, b, st, h in tl if st == "repeat"}
    else:
        whole = "КП" in opp[c]["title"] or "KП" in opp[c]["title"]
        rm_titles = {t for t in now if any(k.lower() in t.lower() for k in cur.get("rmk", []))}
        if whole:
            rm_titles = {t for t, b, st, h in tl if st == "repeat"}
    keep = [t for t in now if t not in rm_titles][:6]
    new = (keep if whole else [t for t in now if t not in rm_titles]) + [a[0] for a in cur["add"]]
    PATHS[c] = dict(group=GROUP[c], verdict=cur["v"], remove=rm, add=cur["add"], keep=keep, labs_now=now, labs_new=new)
    if c in course:
        course[c]["w2"] = [a[0] + " (" + a[1] + ")" for a in cur["add"]] + [f"Прибрати: {x[0]}" for x in rm][:2]
for c in L1C:
    PATHS[c] = dict(PATHS[c], group=GROUP[c])
R["course"] = course
json.dump(R, open(os.path.join(HERE, "recs.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- details (X) ----------
uc = {k: list(v) for k, v in X1["uni_courses"].items()}
for key, crs in UNI_MAP_NEW.items():
    u, t = key.split("|")
    for part in re.split(r";\s*", crs):
        m_ = re.match(r"^([A-Z]{2,5}[- ]?[\dA-Z/]+)\s+«([^»]+)»", part.strip())
        if m_ and not any(x[0] == m_.group(1) for x in uc[u]):
            uc[u].append([m_.group(1), m_.group(2)])
X = dict(X1, paths=PATHS, evidence=EV, uni_map=dict(X1["uni_map"], **UNI_MAP_NEW), uni_url=dict(X1["uni_url"], **UP.URLS), uni_courses=uc,
         uni_short=dict(X1["uni_short"], RISD="BFA Interior Studies"))
json.dump(X, open(os.path.join(HERE, "details.json"), "w", encoding="utf-8"), ensure_ascii=False)


# ---------- ui (U) ----------
GROUPS_ORDER = ["zag", "prof", "vb1", "vb2"]
order = [[GNAME[g], [c for c in ALL if GROUP[c] == g and c in D["cscores"]]] for g in GROUPS_ORDER]
fin = {c: D["cscores"][c][0]["final"] for c in D["cscores"] if D["cscores"][c][0]}
vet = [c for c in D["cscores"] if D["cscores"][c][0] and D["cscores"][c][0]["veto"]]
cred = lambda cs: sum(opp[c]["credits"] for c in cs)
med = statistics.median(fin.values())
pi = D["prog_index"]
f2 = lambda v: f"{v:.1f}".replace(".", ",")
U = dict(U1)
U.update(
 views=[["summary", "Зведення"], ["passport", "Паспорт корпусу"], ["prereq", "Пререквізити"], ["topics", "Матриця тем"],
        ["market", "Зовнішній попит"], ["unis", "Провідні програми"], ["metrics", "Метрики до / після"], ["paths", "Шляхи вдосконалення"],
        ["inputs", "Вхідні дані й припущення"]],
 index_label="Індекс програми", index_note="за метриками, які вже можна виміряти; покриття попиту (P6) додасть етап 3",
 order=order, group=GROUP, groups=[dict(k=g, l=GNAME[g].split(" «")[0], s=GNAME[g]) for g in GROUPS_ORDER],
 summary_title="Зведення по програмі",
 summary_lede=(f"Уся ОП: {len(ALL)} компонентів, {len(OKS)} мають силабус, {len(MISS)} — ні. Бали курсів рахуються з того, що є в силабусах: "
               f"рівень результатів навчання, вік літератури, форми контролю й внутрішні невідповідності; для художньої підготовки — ще й ринок, теми й місце в ОП. "
               f"Перемикачі циклів працюють на всіх вкладках."),
 summary_tiles=[
  dict(l="Компонентів із силабусом", v=f"{len(OKS)} із {len(ALL)}", to=f"{len(ALL)} із {len(ALL)}", z="warn",
       what="Скільки компонентів ОП мають силабус у наданих документах.", how=f"Відсутні: {', '.join(MISS)}. Повних РП з тематичним планом — жодної.",
       goal="Кожен компонент — повна РП з тематичним планом.", so="Без тематичних планів 13 з 24 метрик курсу не вимірні."),
  dict(l="Медіанний бал силабуса", v=f2(med), z="bad" if med < 70 else "warn" if med < 85 else "ok",
       what="Типовий бал робочої програми за методикою AI-Edu.", how=f"Медіана по {len(fin)} силабусах; вето (проблема у вимірах A або B) — у {len(vet)}.",
       goal="85 і більше.", so="Більшість втрат — формальні: форма контролю, коди, політика ШІ, література."),
  dict(l="Форма контролю ≠ ОП", v=f"{len(ctl)} із {len(OKS)}", to="0", z="bad",
       what="Скільки силабусів називають іншу форму підсумкового контролю, ніж ОП.", how="Порівняння поля «форма контролю» з переліком компонентів ОП.",
       goal="0.", so="Найдешевша правка — хвиля 1."),
  dict(l="Політика ШІ", v=f"{len(OKS) - len(noai)} із {len(OKS)}", to=f"{len(OKS)} із {len(OKS)}", z="bad" if len(noai) > len(OKS) / 2 else "warn",
       what="Скільки силабусів мають правила використання ШІ.", how="Пошук розділу про штучний інтелект у тексті силабуса.",
       goal="Усі.", so=f"Зразок уже є в {NP.AI_SAMPLE} — його можна поширити на всі курси.")],
 summary_chart_notes=[f"Бал «зараз» рахується лише з вимірних метрик; курси художньої підготовки мають більше вимірних метрик (теми, ринок), тому їхні бали точніші.",
                      "Хвиля 1 — формальні правки без зміни змісту; хвиля 2 для курсів поза художньою підготовкою з'явиться після етапу 5."],
 wave1_title="Хвиля 1 по всій програмі: формальні правки",
 passport_lede=f"Усі {len(ALL)} компоненти ОП: семестр (з теки силабуса), кредити й форма контролю за ОП проти того, що написано в силабусі.",
 passport_tiles=[dict(l="Силабусів", v=f"{len(OKS)} / {len(ALL)}", s="повних РП з тематичним планом — 0"),
                 dict(l="Форма контролю ≠ ОП", v=str(len(ctl)), s="переважно «залік» замість «диф. заліку»"),
                 dict(l="Коди не з ОП", v=str(len(codes)), s="ПРН21–23, ФКС тощо, яких немає в переліку ОП"),
                 dict(l="Сума балів ≠ 100", v=str(len(sums)), s="за розподілом у силабусі")],
 passport_h_line="", passport_note="Прізвища авторів силабусів на цій сторінці не наводяться.",
 metrics_missing=MISS, default_course="ОК1.13", topic_cols=None, line_label="Курси програми",
 unis_lede=(f"Теми всієї ОП проти повних навчальних планів семи програм дизайну інтер'єру: шість американських (акредитовані CIDA й провідні школи мистецтв) і бакалаврат Politecnico di Milano. "
            f"● — окремий курс, ○ — частина курсу чи студії, порожньо — у повному плані немає, ? — план не розкриває. Консенсус — тема є щонайменше в 5 програмах ({len(CONS)} тем). Клацніть позначку — назва курсу. Останній стовпець — де тема є в нашій ОП."),
 unis_notes=NP.UNIS_NOTES,
 unis_foot=NP.UNIS_FOOT,
 path_groups=[[GNAME[g], [c for c in ALL if GROUP[c] == g], ""] for g in GROUPS_ORDER],
 paths_lede=(f"Усі {len(ALL)} компоненти ОП. Розгорніть курс: що прибрати і з яким курсом воно перекривається, що додати і чим це обґрунтовано "
             "(тема матриці, провідні програми, частка вакансій), що залишити, як зміниться перелік тем, і формальні правки хвилі 1. "
             "Для курсів без силабуса — що має бути в новому документі."),
 labs_now_label="Теми зараз (за силабусом)", labs_new_label="Теми після змін",
 skills_joint=sorted([dict(n=n, ua=round((DSH[c]["ri"] * DN["ri"] + DSH[c]["rs"] * DN["rs"]) / (DN["ri"] + DN["rs"])), fz=DSH[c]["ab"],
                            tot=round(sum(1 for v in DP.VAC if c in v[3]) * 100 / len(DP.VAC)), line=True, now=now, after=aft, w=[wn, wa])
                       for c, n, now, aft, wn, wa in DP.UNITS], key=lambda r: -r["tot"]),
 joint_cols=[f"Україна · n = {DN['ri'] + DN['rs']}", f"За кордоном · n = {DN['ab']}", f"Разом · n = {len(DP.VAC)}"],
 cov_cols=["Програма зараз · де", "Після змін · де"], roles_gives_label="Програма дає",
 roles=[dict(r, now=DP.ROLE_GIVES[r["n"]][0], gap=DP.ROLE_GIVES[r["n"]][1]) if r["n"] in DP.ROLE_GIVES else r for r in U1["roles"]],
 skills_title="Потреби роботодавців і покриття програмою: Україна і за кордоном",
 market_lede=(f"Що вимагають роботодавці від випускника всієї ОП: {len(DP.UNITS)} одиниць попиту з {len(DP.VAC)} вакансій станом на 23.11.2026 — "
              f"дизайнер інтер'єру в Україні ({DN['ri']}), дизайнер просторів і ландшафту в Україні ({DN['rs']}), дизайнер чи архітектор інтер'єру за кордоном ({DN['ab']}: Польща, Велика Британія, США). "
              "Для кожної вимоги — які курси її дають зараз і після правок зі «Шляхів вдосконалення»."),
 market_note=None,
 market_foot=(f"Частка — у скількох відсотках оголошень згадано вимогу. Покриття: «сильне» — є практичне навчання; «часткове» — лише в лекціях, лише в курсовому проєкті без навчання "
              f"або лише в одній вибірковій лінії; «прогалина» — ніде. Метрика покриття попиту (P6) за методикою рахується за українською вибіркою. Вибірка мала — частки орієнтовні; список вакансій — нижче."),
 vacancies_html=None,
 unis2=dict(unis=[list(u) for u in getattr(UP, "UNIS2", [])],
            rows=[[t, [v for v, c in vals], [c for v, c in vals]] for t, vals in getattr(UP, "U2", {}).items()],
            notes=getattr(UP, "NOTES2", []), group="vb2",
            title="Лінія ВБ2 «Просторовий дизайн» проти програм ландшафтного й просторового дизайну",
            lede="Теми лінії 2 зіставлено з двома бакалавратами ландшафтної архітектури (США) і трьома програмами interior and spatial design (Лондон, Мілан): у школах інтер'єру цих тем немає за визначенням."),
 ctopics=CT,
 ctopics_lede=(f"Теми кожного силабуса з розділу «Опис» ({sum(len(v) for v in CT.values())} тем у {len(CT)} силабусах; якщо розділ перелічує «студенти вивчають …, опановують …», кожна частина — окрема тема). "
               "Код шукає таку саму чи схожу тему в усіх інших силабусах за спільними основами слів. "
               "«Повтор» — майже той самий зміст в іншому курсі; «схожа, є раніше» — подібна тема в курсі попереднього семестру (перевірте, чи це розвиток, а не повтор); "
               "«схожа, паралельно чи пізніше» — подібна тема в курсі того самого або наступного семестру. Відсоток — міра схожості."),
 ctopics_total=dict(ct_cnt),
 topic_blocks=[[n, [t["key"] for t in TOPICS if t["block"] == b]] for b, n in TP.BLOCKS],
 topics_lede=("Що вчать курси: ● — практичне чи проєктне завдання, ○ — тема в лекціях або згадка, ? — силабуса немає, а тема очікується за назвою компонента. "
              "Клацніть клітинку — справа з'явиться цитата з силабуса й курси, з якими тема перекривається."),
 topic_dups=NP.TOPIC_DUPS,
 topic_gaps=NP.TOPIC_GAPS,
 metrics_lede=("Програмний рівень — 12 метрик на всю ОП; ті, що залежать від матриці тем, попиту й провідних програм, з'являться на етапах 2–4. "
               "Курсовий рівень — 24 метрики кожного силабуса; оберіть курс."),
 stage_note=NP.STAGE_NOTE,
)
b1, b2 = D["b1"], D["b2"]
low = lambda t: t if len(t) > 1 and t[1].isupper() else t[:1].lower() + t[1:]
f2_ = lambda v: f"{v:.2f}".replace(".", ",")
core = [x for x in DEMAND["skills"] if max(x["share"].values()) >= M.DEMAND_CORE_MIN]
top = U["skills_joint"][:3]
gaps = [r for r in U["skills_joint"] if r["now"] == 0][:4]
U["market_tiles"] = [U1["market_tiles"][0], U1["market_tiles"][1],
  dict(l="Покриття попиту (B1 програми)", v=f2_(b1[0]), to=f2_(b1[2]), z="bad" if b1[0] < .7 else "warn" if b1[0] < .85 else "ok",
       what="Яку частку вимог роботодавців дає програма з практикою (зважено за частотою в оголошеннях).",
       how=f"{len(DP.UNITS)} одиниці попиту; повністю — {sum(1 for r in U['skills_joint'] if r['now'] == 1)}, частково — {sum(1 for r in U['skills_joint'] if r['now'] == .5)}, прогалин — {sum(1 for r in U['skills_joint'] if r['now'] == 0)}.",
       goal="0,85 і більше."),
  dict(l="Ядро попиту (B2)", v=f"{round(b2[0] * len(core))} із {len(core)}", to=f"{round(b2[2] * len(core))} із {len(core)}", z="bad" if b2[0] < .5 else "warn" if b2[0] < 1 else "ok",
       what="Чи дає програма з практикою вимоги, які є щонайменше в 40 % оголошень хоча б однієї ролі.",
       how="Ядро: " + ", ".join(low(x["name"].split(" (")[0]) for x in core) + ".", goal=f"{len(core)} із {len(core)}.")]
U["market_note"] = ("Найчастіше просять " + ", ".join(f"{low(r['n'].split(' (')[0])} ({r['tot']} %)" for r in top) +
                    ". Повністю бракує: " + ", ".join(f"{low(r['n'].split(' (')[0])} ({r['tot']} %)" for r in gaps) +
                    ". Найбільший ефект дадуть силабуси ОК2.2 (креслення), ОК2.23 (обміри) і ОК1.9 (кошторис, авторський нагляд).")
_esc = lambda x: str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
UN = {c: n for c, n, *_ in DP.UNITS}
RLAB = {"ri": "Україна, дизайнер інтер'єру", "rs": "Україна, простори й ландшафт"}
U["vacancies_html"] = (f'<details class="card"><summary><b>Вибірка вакансій · {len(DP.VAC)}</b></summary><ol class="small">' +
    "".join(f'<li>{RLAB.get(v[0], v[1])} — <a href="{_esc(v[2])}" target="_blank" rel="noopener">{_esc(v[2][:80])}</a> · ' +
            ", ".join(UN[x].split(" (")[0] for x in v[3]) + "</li>" for v in DP.VAC) +
    '</ol><p class="small muted">Фрагменти оголошень із текстом вимог і сторінки вакансій студій, станом на 23.11.2026. Мала вибірка — частки орієнтовні.</p></details>')
U["stage_note"] = {}
json.dump(U, open(os.path.join(HERE, "ui.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("тем:", len(TOPICS), "клітинок:", sum(1 for t in TOPICS for v in t["cov"].values() if v is not None), "доказ не знайдено дослівно:", len(ev_bad), ev_bad[:12])
print("курсів з балами:", len(D["cscores"]), "медіана", med, "вето", len(vet), "індекс", pi)
print("P:", [(p["key"], p["v"][0]) for p in D["prog"]])

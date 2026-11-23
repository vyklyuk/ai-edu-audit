# -*- coding: utf-8 -*-
"""Збирає line.json для лінії L1 «Художня підготовка» ОП «Інтер'єр та просторовий дизайн».

Детерміновані частини рахує код (з program.json, courses.jsonl, express.json, sources.py);
судження аудитора (матриця тем, проєктні значення хвиль) записані тут явно, з доказами й правилами,
щоб рецензент міг їх перевірити. Запуск: python build_line_inputs.py  (з цієї теки).
"""
import json
import math
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(RUN, "..", "..", "src"))
import sources as S  # noqa: E402
from ai_edu_audit.calc import methodology as M  # noqa: E402

YEAR = 2026
prog = json.load(open(os.path.join(RUN, "program.json"), encoding="utf-8"))
rows = {json.loads(l)["ok"]: json.loads(l) for l in open(os.path.join(RUN, "courses.jsonl"), encoding="utf-8")}
express = json.load(open(os.path.join(RUN, "express.json"), encoding="utf-8"))
opp = {c["code"]: c for c in prog["courses"]}

LINE = ["ОК1.1", "ОК1.2", "ОК1.3", "ОК1.11", "ОК1.12", "ОК1.13", "ОК1.14", "ОК2.3", "ОК2.4"]
NEIGH = ["ОК2.1", "ОК2.7", "ОК2.21"]          # сусіди з перетином тем
COLS = LINE + NEIGH

# ---------- матриця тем (судження аудитора; 2 = практичне завдання в силабусі, 1 = лише згадка) ----------
TOPICS = [
 ("T01", "Конструктивний рисунок, пропорції предметів і тіл", {"ОК1.1": 2, "ОК1.2": 2, "ОК1.3": 2}, ""),
 ("T02", "Тональний рисунок: світлотінь, матеріальність, фактура", {"ОК1.1": 2, "ОК1.2": 2, "ОК1.3": 2, "ОК1.11": 2, "ОК1.12": 1, "ОК1.14": 1, "ОК2.1": 2}, "сім курсів, без поділу ролей"),
 ("T03", "Перспектива й рисунок простору (інтер'єр, архітектура)", {"ОК1.1": 2, "ОК1.11": 1}, "консенсус провідних програм; у лінії — одне самостійне завдання"),
 ("T04", "Академічний живопис: колорит, гами, етюд", {"ОК1.1": 2, "ОК1.2": 2, "ОК1.3": 2, "ОК1.11": 2, "ОК1.12": 2, "ОК1.13": 2, "ОК1.14": 2}, "сім курсів; у провідних програмах інтер'єру окремого живопису немає"),
 ("T05", "Кольорознавство й колірна гармонія", {"ОК1.1": 1, "ОК1.2": 1, "ОК2.3": 2}, ""),
 ("T06", "Площинна композиція: рівновага, ритм, симетрія, центр", {"ОК1.1": 1, "ОК1.13": 1, "ОК1.14": 2, "ОК2.3": 2, "ОК2.1": 2, "ОК2.7": 1, "ОК2.21": 1}, ""),
 ("T07", "Стилізація, декоративно-площинна трансформація форм", {"ОК1.1": 2, "ОК1.2": 2, "ОК1.3": 2, "ОК1.11": 2, "ОК1.12": 2, "ОК1.13": 2, "ОК2.3": 2}, "сім курсів"),
 ("T08", "Голова й фігура людини, пластична анатомія", {"ОК1.3": 2, "ОК1.11": 2, "ОК1.12": 2, "ОК1.13": 2, "ОК1.14": 1}, "п'ять курсів; провідні програми інтер'єру цього не вимагають"),
 ("T09", "Начерк і швидкий скетч (з натури, по пам'яті, по уяві)", {"ОК1.1": 1, "ОК1.2": 2, "ОК1.3": 2, "ОК1.11": 2, "ОК1.12": 2, "ОК1.13": 2}, "начерки з натури, не скетч простору"),
 ("T10", "Пленер, пейзаж, міське середовище", {"ОК1.2": 2}, ""),
 ("T11", "Об'ємно-просторова композиція, формотворення", {"ОК1.3": 1, "ОК1.11": 1, "ОК2.3": 1, "ОК2.4": 2}, ""),
 ("T12", "Макетування з матеріалів", {"ОК2.4": 2}, ""),
 ("T13", "Скульптура, пластичне моделювання об'єму", {"ОК1.1": 0, "ОК1.2": 0, "ОК1.3": 0}, "у назві трьох курсів «скульптура», у змісті — жодного завдання"),
 ("T14", "Колір і світло в інтер'єрі / середовищі", {"ОК2.3": 2, "ОК2.7": 2}, ""),
 ("T15", "Ручна подача проєкту: скетч інтер'єру, маркери, рендеринг", {"ОК2.4": 1, "ОК2.1": 2}, "консенсус провідних програм; у лінії лише маркери в ОК2.4"),
 ("T16", "Цифровий рисунок і змішані техніки", {}, "прогалина"),
 ("T17", "Копія й інтерпретація творів і стилів", {"ОК1.1": 2, "ОК1.2": 2, "ОК1.13": 2, "ОК1.14": 2}, ""),
]
EVIDENCE = {  # (topic, course) -> цитата з силабуса (перевіряється кодом)
 ("T01", "ОК1.1"): "Лінійно-конструктивний рисунок з геометричних тіл",
 ("T03", "ОК1.1"): "в ізометрії чи лінійній перспективі",
 ("T08", "ОК1.3"): "Рисунок анатомічної голови людини",
 ("T10", "ОК1.2"): "пленерні та ландшафтні студії",
 ("T12", "ОК2.4"): "об’ємних макетів із різних матеріалів",
 ("T14", "ОК2.3"): "використання в конкретному інтер'єрі",
 ("T15", "ОК2.1"): "Комплексне графічне відображення середовища",
 ("T17", "ОК1.14"): "Колористична подача відомого живописного твору",
}
# Хвиля 2: хто вчить тему один раз
OWNER = {"T01": "ОК1.1", "T02": "ОК1.1–ОК1.3", "T03": "ОК1.11 → ОК1.12", "T04": "ОК1.2", "T05": "ОК2.3", "T06": "ОК2.3",
         "T07": "ОК2.3", "T08": "ОК1.3", "T09": "ОК1.13", "T10": "ОК1.2", "T11": "ОК2.4", "T12": "ОК2.4",
         "T13": "ОК1.3 (або перейменувати курс)", "T14": "ОК2.7", "T15": "ОК1.13 → ОК1.14", "T16": "ОК1.14", "T17": "ОК1.14"}

# ---------- зовнішній попит: частки з вибірки ----------
def shares():
    out = {}
    for code, _ in S.SKILLS:
        sh = {}
        for r in S.ROLES:
            vs = [v for v in S.VACANCIES if v[0] == r["key"]]
            sh[r["key"]] = round(100 * sum(1 for v in vs if code in v[2]) / len(vs))
        out[code] = sh
    return out
SH = shares()
N = {r["key"]: sum(1 for v in S.VACANCIES if v[0] == r["key"]) for r in S.ROLES}
SKILL_TOPICS = {"S1": ["T06"], "S2": ["T04", "T05", "T14"], "S3": ["T09", "T15", "T03"], "S4": [], "S5": [],
                "S6": ["T07", "T17"], "S7": ["T11", "T12"], "S11": ["T02", "T12"], "S12": []}
COV = {  # [до, хвиля1, хвиля2]: 1 повністю, 0.5 частково, 0 немає
 "S1": [1, 1, 1], "S2": [1, 1, 1], "S3": [0.5, 0.5, 1], "S4": [0, 0, 1], "S5": [0, 0, 1],
 "S6": [1, 1, 1], "S7": [1, 1, 1], "S11": [0.5, 0.5, 1], "S12": [0, 0.5, 1]}
WHERE = {
 "S1": ("ОК2.3, ОК1.14", "ОК2.3"), "S2": ("ОК2.3, живопис ОК1.1–1.14", "ОК2.3 + ОК2.7 (колір у середовищі)"),
 "S3": ("начерки з натури ОК1.2–1.13; скетчу простору немає", "ОК1.13 — скетч простору, ОК1.14 — ручна подача"),
 "S4": ("—", "ОК1.14 — мудборд і концепт-ескіз"), "S5": ("—", "ОК1.14 — підсумкове портфоліо лінії"),
 "S6": ("ОК1.13–1.14, ОК2.3", "без змін"), "S7": ("ОК2.4", "ОК2.4 + об'ємний блок ОК1.3"),
 "S11": ("фактури в рисунку ОК1.1", "ОК1.1 + матеріали в макетах ОК2.4"),
 "S12": ("—", "політика ШІ (хв. 1), генеративні референси й мудборди в ОК1.14 (хв. 2)")}

# ---------- провідні програми: покриття тем (2 окремий курс, 1 частина курсу, 0 немає, None — немає даних) ----------
#            Pratt RISD SCAD SVA RIT MIAD Polimi
UNI_T = {
 "T01": [2, 2, 2, 1, 2, 2, 2], "T02": [1, None, 1, 1, None, None, None], "T03": [2, 1, 2, 2, 1, 1, 2],
 "T04": [0, 0, 0, 0, 0, None, 0], "T05": [2, 2, 2, 1, 2, 2, 1], "T06": [1, 2, 2, None, None, 2, None],
 "T07": [0, 0, 0, 0, 0, None, 0], "T08": [None, None, 0, 0, 0, None, None], "T09": [1, 1, 1, 2, None, None, None],
 "T10": [0, 0, 0, 2, 0, None, 0], "T11": [2, 2, 2, None, None, None, None], "T12": [1, 2, 1, None, None, None, None],
 "T13": [0, 0, 0, 0, 0, None, 0], "T14": [2, 2, 1, None, 2, None, 1], "T15": [2, 1, 1, 2, 1, None, 1],
 "T16": [None, None, 1, None, None, 1, None], "T17": [0, 0, 0, 0, 0, None, 0],
}

# ---------- метрики курсів ----------
INCONS = {  # внутрішні суперечності в правилах оцінювання (цитати перевіряються)
 "ОК1.12": "Розрахунок балів: А.р.№1+А.р.№2+А.р.№3+А.р.№4+С.р.№1+С.р.№2+С.р.№3+С.р.№4) : 8= 60+40= 100 балів",
 "ОК1.14": "Протягом семестру студент може набрати 100 балів за виконання двох завдань",
}
EXTRA = {}   # хвиля 2: одиниці попиту без теми в матриці (мудборд, портфоліо, ШІ) — додаються курсу явно
HIGH_VERBS = re.compile(r"(?i)^(аналіз|оцін|створ|розроб|проєкт|проект|формув|обґрунт|обгрунт|синтез|інтерпрет|трансформ|відобра|застосов|вирішув|викон)")
prn_text = {o["code"]: o["text"] for o in prog["outcomes"]}
defined = {c["code"] for c in prog["competences"]} | set(prn_text)
consensus = [t for t, v in UNI_T.items() if sum(1 for x in v if x) >= M.CONSENSUS_MIN_PROGRAMS]
topic_cov = {t[0]: t[2] for t in TOPICS}


def course_topics(c, min_v=1):
    return [t for t, cov in topic_cov.items() if (cov.get(c) or 0) >= min_v]


def metric_before(c):
    r = rows[c]
    m = {k: None for k in M.METRIC_CODES}
    prns = [p for p in r["prn"] if p in prn_text]
    if prns:   # A4 — частка ПРН рівня «застосування й вище» за дієсловом формулювання в ОП
        m["A4"] = round(sum(1 for p in prns if HIGH_VERBS.match(prn_text[p])) / len(prns), 2)
    ts = course_topics(c)
    w = lambda s: sum(SH[s].values()) / len(SH[s])
    # B1/B2 курсу — лише по одиницях попиту, до яких курс має стосунок (через теми або план хвилі 2)
    cov_s = {}
    for s, tl in SKILL_TOPICS.items():
        v = max([topic_cov[t].get(c) or 0 for t in tl] + [0])
        has = lambda txt: re.search(re.escape(c) + r"(?![\d.]\d)(?!\d)", txt) is not None
        assigned = has(WHERE[s][1]) and not has(WHERE[s][0])
        if v or assigned or s in EXTRA.get(c, ()):
            cov_s[s] = 1 if (v == 2 or s in EXTRA.get(c, ())) else 0.5 if v == 1 else 0
    if cov_s:
        den = sum(w(s) for s in cov_s) or 1
        m["B1"] = round(sum(w(s) * cov_s[s] for s in cov_s) / den, 2)
        core = [s for s in cov_s if max(SH[s].values()) >= M.DEMAND_CORE_MIN]
        m["B2"] = round(sum(1 for s in core if cov_s[s] >= 1) / len(core), 2) if core else None
    if ts:     # B3 — частка тем курсу з зовнішнім обґрунтуванням (одиниця попиту або консенсус)
        backed = {t for tl in SKILL_TOPICS.values() for t in tl} | set(consensus)
        m["B3"] = round(sum(1 for t in ts if t in backed) / len(ts), 2)
    if r["lit_years"]:
        m["C1"] = YEAR - statistics.median(r["lit_years"])
    if ts:     # D1 — частка тем курсу, що є ще у ≥2 інших курсах лінії
        m["D1"] = round(sum(1 for t in ts if sum(1 for k in LINE if k != c and (topic_cov[t].get(k) or 0) >= 1) >= 2) / len(ts), 2)
        # D2 — частка тем, яких немає в жодній провідній програмі (власний профіль курсу)
        m["D2"] = round(sum(1 for t in ts if not any(UNI_T[t])) / len(ts), 2)
        cons_touch = [t for t in ts if t in consensus]
        m["D3"] = round(sum(1 for t in cons_touch if topic_cov[t].get(c) == 2) / len(cons_touch), 2) if cons_touch else None
    meth = (r.get("summary", "") + " " + " ".join(e["quote"] for e in r["evidence"] if e["field"] in ("control", "assessment"))).lower()
    forms = sum(1 for pat in (r"перегляд", r"тест", r"самостійн", r"контрольн", r"опитув", r"захист", r"практичн\w* завдан|аудиторн\w* робіт|постановк")
                if re.search(pat, meth))
    m["F2"] = forms or None
    g1 = 0
    g1 += any("форма контролю" in n for n in r["notes"])
    g1 += any("сума виділених балів" in n for n in r["notes"])
    g1 += any(p not in defined for p in r["prn"] + r["comps"])
    g1 += c in ("ОК1.1", "ОК1.2", "ОК1.3")          # «скульптура» в назві без змісту
    g1 += c in ("ОК1.1", "ОК1.2")                   # однаковий перелік літератури (22 джерела)
    g1 += c in INCONS
    m["G1"] = g1
    if c in ("ОК1.1", "ОК1.2", "ОК1.3"):
        m["G2"] = round(2 / 3, 2)                    # 2 з 3 названих складників (рисунок, живопис) є в змісті
    return m


W1_RULES = "хвиля 1 — формальні правки без зміни змісту: G1 → 0 (форма контролю як в ОП, бали = 100, коди з ОП, " \
           "окремий перелік літератури), C1 → 6 (оновлення базової літератури), F2 +1 (перегляд-захист у ВНС)"
W2_PLAN = {   # хвиля 2 — зміни змісту (прогноз; кожна зміна — у R.course[c].w2)
 "ОК1.1": dict(G2=1.0, D1=0.4), "ОК1.2": dict(G2=1.0, D1=0.4),
 "ОК1.3": dict(G2=1.0, D1=0.4),
 "ОК1.11": dict(D1=0.4), "ОК1.12": dict(D1=0.4), "ОК1.13": dict(D1=0.35), "ОК1.14": dict(D1=0.3),
 "ОК2.3": dict(D1=0.4), "ОК2.4": dict(),
}
W2_TOPICS = {  # нові/посилені теми хвилі 2 за курсами (для B1, B3, D3)
 "ОК1.1": {"T06": 2}, "ОК1.3": {"T13": 2}, "ОК1.11": {"T03": 2}, "ОК1.12": {"T03": 2}, "ОК1.13": {"T09": 2, "T03": 2, "T06": 2},
 "ОК1.14": {"T15": 2, "T16": 2}, "ОК2.3": {}, "ОК2.4": {"T15": 2},
}

course_metrics = []
for c in LINE:
    if rows[c]["status"] != "ok":
        continue
    b = metric_before(c)
    w1 = {"G1": 0}
    if b["C1"] is not None and b["C1"] > 6:
        w1["C1"] = 6
    if b["F2"] is not None:
        w1["F2"] = min(b["F2"] + 1, 5)
    # хвиля 2: перерахунок B1/B2/B3/D3 з новими темами — тим самим правилом, що й «до»
    saved = {t: dict(v) for t, v in topic_cov.items()}
    for t, v in W2_TOPICS.get(c, {}).items():
        topic_cov[t][c] = v
    for s in ("S4", "S5", "S12"):
        pass
    after = metric_before(c)
    topic_cov.clear(); topic_cov.update(saved)
    w2 = {k: after[k] for k in ("B1", "B2", "B3", "D3") if after[k] is not None and after[k] != b[k]}
    if c == "ОК1.14":   # мудборд, портфоліо і ШІ-референси додають S4, S5, S12
        EXTRA[c] = ("S4", "S5", "S12")
        for t, v in W2_TOPICS.get(c, {}).items():
            topic_cov[t][c] = v
        a2 = metric_before(c)
        topic_cov.clear(); topic_cov.update({t: dict(v) for t, v in saved.items()})
        EXTRA.pop(c)
        for k in ("B1", "B2", "B3"):
            if a2[k] is not None:
                w2[k] = a2[k]
    w2.update(W2_PLAN.get(c, {}))
    if b["A4"] is not None and b["A4"] < 0.5:
        w2["A4"] = 0.5      # формулювання РН курсу на рівні «аналізувати / створювати»
    course_metrics.append(dict(ok=c, before=b, w1=w1, w2=w2))

# ---------- паспорт ----------
def codes_note(r):
    bad = sorted({p for p in r["prn"] + r["comps"] if p not in defined})
    return ("коди з ОП" if not bad else f"є коди, яких немає в ОП: {', '.join(bad)}")


passport = []
for c in COLS:
    r, o = rows[c], opp[c]
    passport.append(dict(code=c, title=o["title"], role="line" if c in LINE else "pre",
                         sem=(o["semesters"] or [None])[0], opp=dict(credits=o["credits"], control=o["control"]),
                         rp=dict(status=r["status"], year=None, credits=None, control=r.get("control"),
                                 kind="силабус", codes=codes_note(r) if r["status"] == "ok" else None),
                         issues=[n for n in r["notes"] if "тематичного плану" not in n]))

sem = {c: (opp[c]["semesters"] or [None])[0] for c in opp}
links, seen = [], set()
for l in express["links"]:
    if not (l["src"] in COLS or l["dst"] in COLS):
        continue
    if l["verdict"] == "unknown":
        continue
    src = l["src"] if l["src"] in opp else None
    if src is None:
        continue
    dst = l["dst"] if l["dst"] in opp else None
    key = (src, dst, l["as_written"])
    if key in seen:
        continue
    seen.add(key)
    links.append(dict(src=src, dst=dst, kind="prereq", as_written=l["as_written"] + f" (у силабусі {l['from_rp']})"))
# усі ОК із семестром (з тек силабусів) — щоб карта пререквізитів показувала повний розклад, а не лише зв'язки лінії
sem_extra = {k: v for k, v in sem.items() if k not in COLS and v is not None}

line = {
 "schema_version": "1.0",
 "meta": {"program": "ОПП «Інтер'єр та просторовий дизайн» 2026, бакалавр, В2 «Дизайн»",
          "institution": "НУ «Львівська політехніка», кафедра дизайну та основ архітектури",
          "line_id": "L1", "line_name": "Художня підготовка", "profile": "creative", "level": "bachelor",
          "sources": {"demand": f"фрагменти вакансій work.ua / djinni (n = {N['ri']} + {N['rs']}) і ESCO, станом на {S.AS_OF}",
                      "universities": f"публічні навчальні плани 7 програм, станом на {S.AS_OF}"},
          "topic_scale": "2 — практичне завдання в силабусі; 1 — лише згадка в змісті; 0 — немає (тематичних планів з годинами немає)",
          "w1_rules": W1_RULES,
          "provenance": "прототип: судження аудитора записані в build_line_inputs.py; детерміновані частини — код"},
 "year": YEAR,
 "line": LINE,
 "passport": passport,
 "sem_extra": sem_extra,
 "links": links,
 "cols": COLS,
 "topics": [dict(key=t, name=n, cov={k: v for k, v in cov.items()}, comment=cm) for t, n, cov, cm in TOPICS],
 "owner": OWNER,
 "demand": {"roles": S.ROLES, "skills": [dict(name=n, share=SH[s], coverage=COV[s],
                                                where=dict(before=WHERE[s][0], after=WHERE[s][1]),
                                                sources=[dict(url=v[1], date=S.AS_OF) for v in S.VACANCIES if s in v[2]][:3])
                                           for s, n in S.SKILLS]},
 "universities": {"list": [dict(name=u[0], courses=u[1], country=u[2]) for u in S.UNIS], "topic_coverage": UNI_T},
 "course_metrics": course_metrics,
 "program_metrics": [
  dict(key="P1", name="Повнота корпусу РП лінії", values=[{"calc": "rp_completeness"}, 1.0, 1.0],
       note="9 із 9 ОК лінії мають силабус; повних РП з тематичним планом немає"),
  dict(key="P2", name="Готовність РП лінії до ОП", values=[round(next(m["v"] for m in next(l for l in express["lines"] if l["id"] == "L1")["metrics"] if m["key"] == "P2"), 3), 1.0, 1.0],
       note="форма контролю = ОП і всі коди компетентностей/ПРН визначені в ОП: 1 із 18 перевірок; частина кодів (ПРН21–23) не визначена в самій ОП"),
  dict(key="P3", name="Забезпеченість компетентностей лінії", values=[None, None, None],
       note="н/д: лінія обов'язкова, власних СКЛ/ПРНЛ не має"),
  dict(key="P4", name="Цілісність пререквізитів", values=[{"calc": "links_valid_share"}, 0.9, 0.95],
       note="{links_valid} коректних із {links_total} заявлених зв'язків (семестри — з тек силабусів)"),
  dict(key="P5", name="Частка тем, що дублюються в ≥3 курсах", values=[{"calc": "dup_share"}, {"calc": "dup_share"}, 0.18],
       note="після хвилі 2 кожна тема має одного власника; живопис і рисунок лишаються наскрізними"),
  dict(key="P6", name="Покриття зовнішнього попиту (зважене, B1 лінії)", values=[{"calc": "b1", "state": 0}, {"calc": "b1", "state": 1}, {"calc": "b1", "state": 2}],
       note=f"9 одиниць попиту художньої підготовки; ваги — частки у вибірці вакансій (n = {N['ri']} + {N['rs']})"),
  dict(key="P7", name="Покриття консенсусного ядра провідних програм", values=[{"calc": "consensus_coverage"}, {"calc": "consensus_coverage"}, 1.0],
       note="консенсус — теми у ≥5 з 7 програм ({consensus_n} тем); тема покрита, якщо є хоча б одне практичне завдання в лінії чи в сусіда: T03 — лише самостійне завдання ОК1.1, T15 — лише сусідній ОК2.1"),
  dict(key="P8", name="Медіанний вік літератури лінії, років", values=[{"calc": "lit_median_age"}, 6, 5],
       note="медіана по 9 силабусах"),
  dict(key="P9", name="Частка практики в аудиторних годинах", values=[None, None, None],
       note="н/д: немає навчального плану й годин (припущення A2)"),
  dict(key="P10", name="Узгодженість оцінювання (бали = 100, форма = ОП)", values=[0.0, 1.0, 1.0],
       note="0 із 9: у 8 форма контролю «залік» замість «диф. заліку»; в ОК2.3 сума балів 95; в ОК1.12 і ОК1.14 суперечливі правила підрахунку"),
  dict(key="P11", name="Цілісність проєктного ланцюжка", values=[None, None, None], note="н/д для лінії художньої підготовки"),
  dict(key="P12", name="Політика ШІ та ШІ-інструменти в РП лінії", values=[0.0, 1.0, 1.0],
       note="0 із 9 силабусів; хвиля 1 — шаблон політики з ВБ1.3"),
 ],
 "pilot": {"before": None, "raw_after": None, "final_after": None, "note": "пілотного курсу з виміряним «до/після» немає; K не застосовується"},
}
out = os.path.join(HERE, "line.json")
json.dump(line, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# курси лінії для розрахунку (вік літератури) — підмножина courses.jsonl
with open(os.path.join(HERE, "courses.jsonl"), "w", encoding="utf-8") as f:
    for c in COLS:
        f.write(json.dumps(rows[c], ensure_ascii=False) + "\n")

# перевірка доказів матриці тем
from ai_edu_audit.ingest.convert import find_quote  # noqa: E402
inv = json.load(open(os.path.join(RUN, "inventory.json"), encoding="utf-8"))
txt = {f["rel"]: f["text_file"] for f in inv["files"] if f.get("text_file")}
bad = []
for (t, c), q in list(EVIDENCE.items()) + [(("G1", c), q) for c, q in INCONS.items()]:
    pages = open(os.path.join(RUN, txt[rows[c]["file"]]), encoding="utf-8").read().split("\f")
    if find_quote(pages, q) is None:
        bad.append((t, c, q))
print("line.json записано; консенсус:", consensus, "; докази матриці не знайдено:", bad)
print("частки попиту:", SH, N)

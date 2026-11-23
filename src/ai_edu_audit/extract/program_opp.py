# -*- coding: utf-8 -*-
"""Детермінований витяг паспорта ОП з ОПП у форматі НУ «Львівська політехніка».

Що береться: загальні відомості, компетентності й ПРН з текстами (з доказом: сторінка + цитата),
перелік ОК (з інвентаризації), семестри (з тек силабусів — навчального плану немає),
матриці «ОК × компетентність» і «ОК × ПРН». Розбіжності в самій ОПП (коди в матрицях,
яких немає в переліку, тощо) повертаються як issues — це знахідки аудиту, а не помилки витягу.
"""
import re
from collections import defaultdict

from ..ingest.convert import find_quote

CODE_RE = re.compile(r"(?<![А-ЯІЇЄA-Za-z])((?:ПРНОП|ПРНВ|ПРНЛ|ПРН|СКЛ|СКОП|СК|ЗК|ФКС|КОМ|АіВ|ВіВ|ІНТ)\s?\d+(?:\.\d+)?)\.?\s*")


def _cells(row):
    out = []
    for c in row.cells:
        x = " ".join(c.text.split())
        if not out or out[-1] != x:
            out.append(x)
    return out


def norm_code(c):
    c = re.sub(r"\s+", "", c).replace("ВіВ", "АіВ")
    return c


def norm_ok(c):
    return re.sub(r"\s+", "", c).rstrip(".")


def split_items(text):
    """«ЗК1. Текст. ЗК2. Текст» -> [(ЗК1, Текст), …]"""
    parts = CODE_RE.split(text)
    items = []
    for i in range(1, len(parts) - 1, 2):
        code, body = norm_code(parts[i]), parts[i + 1].strip().rstrip(";").strip()
        if body:
            items.append((code, body))
    return items


def _kv_table(d):
    t = next((t for t in d.tables if t.rows and "загальні відомості" in " ".join(_cells(t.rows[0])).lower()), None)
    kv = {}
    if t is None:
        return kv
    for r in t.rows:
        c = _cells(r)
        if len(c) >= 2:
            kv[c[0]] = c[1]
    return kv


GROUPS = [  # мітка рядка таблиці -> (група, тип)
    ("Інтегральна компетентність", "ІНТ", "competence"),
    ("Загальні компетентності", "ЗК", "competence"),
    ("Спеціальні компетентності освітньої програми", "СКОП", "competence"),
    ("Спеціальні компетентності лінії", "СКЛ", "competence"),
    ("Спеціальні компетентності", "СК", "competence"),
    ("Програмні результати навчання освітньої програми", "ПРНОП", "outcome"),
    ("Програмні результати навчання ліній", "ПРНЛ", "outcome"),
    ("Програмні результати навчання", "ПРН", "outcome"),
    ("Комунікація", "КОМ", "outcome"),
    ("Автономія і відповідальність", "АіВ", "outcome"),
]


def parse_matrix(t):
    hdr = [norm_code(" ".join(c.text.split())) for c in t.rows[0].cells]
    rows, unlabeled = {}, defaultdict(int)
    for r in t.rows[1:]:
        cells = [" ".join(c.text.split()) for c in r.cells]
        ok = norm_ok(cells[0])
        if not ok:
            continue
        marks = []
        for j in range(1, len(cells)):
            if cells[j] in ("•", "+", "●", "х", "x", "Х", "X", "∙", "·"):
                if j < len(hdr) and hdr[j]:
                    marks.append(hdr[j])
                else:
                    unlabeled[ok] += 1
        rows[ok] = sorted(set(marks), key=marks.index)
    return [h for h in hdr[1:] if h], rows, dict(unlabeled)


def extract_program(opp_docx, opp_pages, inventory, std_info=None):
    import docx
    d = docx.Document(opp_docx)
    kv = _kv_table(d)
    issues = []

    def ev(field, quote):
        page = find_quote(opp_pages, quote[:160])
        return dict(field=field, quote=quote[:160], file=inventory["program_file"], page=page)

    evidence = []
    competences, outcomes = [], []
    for label, val in kv.items():
        grp = next(((g, k) for (lab, g, k) in GROUPS if label.startswith(lab)), None)
        if not grp:
            continue
        g, kind = grp
        if g == "ІНТ":
            items = [("ІНТ", val)]
        else:
            items = split_items(val)
        for code, body in items:
            rec = dict(code=code, text=body, group=g)
            (competences if kind == "competence" else outcomes).append(rec)
            evidence.append(ev(f"{'competences' if kind == 'competence' else 'outcomes'}.{code}", body))

    # дублікати кодів у переліку
    for coll, name in ((competences, "компетентностей"), (outcomes, "результатів навчання")):
        seen = defaultdict(list)
        for r in coll:
            seen[r["code"]].append(r["group"])
        for c, g in seen.items():
            if len(g) > 1:
                issues.append(dict(type="codes", severity="warning",
                                   text=f"Код {c} використано двічі в переліку {name} ({', '.join(g)})"))

    # матриці
    comp_matrix, prn_matrix, other_matrix = defaultdict(list), defaultdict(list), defaultdict(list)
    defined = {r["code"] for r in competences} | {r["code"] for r in outcomes}
    matrix_codes = set()
    for t in d.tables:
        if not t.rows or len(t.rows[0].cells) < 5:
            continue
        hdr0 = [norm_code(" ".join(c.text.split())) for c in t.rows[0].cells]
        first = norm_ok(" ".join(t.rows[1].cells[0].text.split())) if len(t.rows) > 1 else ""
        if not re.match(r"^(ОК|ВБ)\d", first):
            continue
        codes, rows, unl = parse_matrix(t)
        matrix_codes |= set(codes)
        kind = ("prn" if any(c.startswith(("ПРН", "ПРОН")) for c in codes) else
                "other" if any(c.startswith("РНПС") for c in codes) else "comp")
        target = dict(prn=prn_matrix, other=other_matrix, comp=comp_matrix)[kind]
        for ok, marks in rows.items():
            target[ok] = list(dict.fromkeys(target[ok] + marks))
        for ok, n in unl.items():
            issues.append(dict(type="matrix", severity="warning",
                               text=f"Матриця ({kind}): у рядку {ok} {n} позначок у стовпцях без назви"))
        dup = [c for c in set(codes) if codes.count(c) > 1]
        if dup:
            issues.append(dict(type="matrix", severity="warning",
                               text=f"Матриця ({kind}): стовпці з однаковою назвою {sorted(dup)} — "
                                    "неможливо визначити, який результат мається на увазі"))
    undefined = sorted(c for c in matrix_codes if c not in defined and c != "ІНТ")
    if undefined:
        groups = defaultdict(list)
        for c in undefined:
            groups[re.sub(r"\d.*", "", c)].append(c)
        for g, cs in groups.items():
            issues.append(dict(type="codes", severity="warning",
                               text=f"У матрицях є коди {g} ({len(cs)}: {', '.join(cs[:6])}{'…' if len(cs) > 6 else ''}), "
                                    "яких немає в переліку компетентностей/ПРН ОП"))
    never = sorted(c for c in defined if c not in matrix_codes and not c.startswith(("КОМ", "АіВ", "ІНТ")))
    if never:
        issues.append(dict(type="codes", severity="info",
                           text=f"Коди з переліку, яких немає в жодній матриці ({len(never)}): "
                                f"{', '.join(never[:10])}{'…' if len(never) > 10 else ''}"))

    # ОК із семестрами з тек силабусів
    sem_by_ok = defaultdict(set)
    for f in inventory["files"]:
        m = f.get("match") or {}
        if m.get("ok") and f.get("semester_folder"):
            sem_by_ok[m["ok"]].add(f["semester_folder"])
    courses = []
    for c in inventory["opp_components"]:
        if c["free_choice"]:
            continue
        sems = sorted(sem_by_ok.get(c["code"], []))
        courses.append(dict(code=c["code"], title=c["title"], type=c["type"], block=c["block"],
                            semesters=sems, semester_source="тека силабуса" if sems else None,
                            credits=c["credits"], control=c["control"]))
        if len(sems) > 1:
            issues.append(dict(type="semesters", severity="info",
                               text=f"{c['code']}: силабуси лежать у кількох семестрах {sems}"))

    level_txt = kv.get("Рівень вищої освіти", "")
    program = dict(
        name=kv.get("Назва освітньої програми українською мовою", ""),
        name_en=kv.get("Назва освітньої програми англійською мовою", ""),
        level="bachelor" if "бакалавр" in level_txt.lower() else "master_opp",
        specialty=dict(code="В2", name=kv.get("Назва спеціальності", ""), list="2024",
                       specialization=kv.get("Назва спеціалізації (предметної спеціальності)", "")),
        institution=kv.get("Повна назва закладу вищої освіти", ""),
        unit=kv.get("Назва навчально-наукового(их) інституту(ів), відповідального(их) за реалізацію освітньої програми", ""),
        year=2026, form=kv.get("Форми здобуття освіти", ""), profile="creative",
        credits_total=float(kv.get("Обсяг освітньої програми (у кредитах ЄКТС)", "0") or 0),
        duration=kv.get("Термін навчання", ""),
        goal=kv.get("Мета освітньої програми", ""),
        employment=kv.get("Працевлаштування випускників", ""),
        practice_orientation=kv.get("Практикоорієнтованість освітньої програми", ""),
        courses=courses, competences=competences, outcomes=outcomes,
        comp_matrix=dict(comp_matrix), prn_matrix=dict(prn_matrix), other_matrix=dict(other_matrix),
        standard=std_info or {}, evidence=evidence, issues=issues,
    )
    return program

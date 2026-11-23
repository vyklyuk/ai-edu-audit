# -*- coding: utf-8 -*-
"""Детермінований витяг рядка courses.jsonl із силабуса НУ «Львівська політехніка».

Код бере лише те, що має явну форму: коди компетентностей і ПРН, пре- і постреквізити,
форму контролю, бали, тип практики, роки літератури, політику ШІ. Кожне поле супроводжується
доказом (точна цитата + сторінка). Теми (lectures/practice) з «Короткого змісту» і «Опису»
виділяє агентний крок витягу (extract_topics), бо це потребує судження.
"""
import re

from ..ingest.convert import find_quote, normalize
from ..ingest.inventory import parse_syllabus

PRE_RE = re.compile(r"(?:Попередні навчальні дисципліни|пререквізити)\)?\s*[:\-–]?\s*(.+?)(?=(?:Супутні|Наступні|Постреквізити|кореквізити|$))", re.I | re.S)
NEXT_RE = re.compile(r"(?:Наступні навчальні дисципліни|Постреквізити)[^:]*:\s*(.+?)$", re.I | re.S)


def _split_list(s):
    s = re.sub(r"\(.*?\)", "", s or "")
    s = re.split(r"(?i)наступні навчальні дисципліни|постреквізити|супутні навчальні дисципліни", s)[0]
    s = re.sub(r"(?<![\w.])\d{1,2}\.\s*", "; ", s)          # «1. А 2. Б» -> «; А ; Б»
    items = re.split(r"\s*[;•]\s*|\s+-\s+|\s*\n\s*|,\s*(?=[А-ЯІЇЄҐ«])|»\s*,?\s*«|\.\s+(?=[А-ЯІЇЄҐ«])", s)
    out = []
    for i in items:
        i = i.strip(" .-–—:«»\"").strip()
        if 3 <= len(i) <= 120 and not re.match(r"(?i)^(немає|відсутні|не передбачено|[ivxlcді]+)$", i):
            out.append(i)
    return out


def _sentence_with(text, pattern):
    m = re.search(r"[^.]*" + pattern + r"[^.]*\.?", text, re.I)
    return m.group(0).strip() if m else None


def extract_course(file_rel, docx_path, pages, opp_course, block=None):
    meta = parse_syllabus(docx_path)
    text = meta["text"]
    secs = {}
    for p in text.split("\n")[1:]:
        m = re.match(r"^([А-ЯІЇЄҐ][^:]{2,70}):\s*(.*)$", p, re.S)
        if m:
            secs[m.group(1).strip()] = m.group(2).strip()
    evidence = []

    def ev(field, quote):
        if quote:
            q = quote.strip()[:200]
            evidence.append(dict(field=field, quote=q, file=file_rel, page=find_quote(pages, q)))

    prereq_sec = next((v for k, v in secs.items() if k.lower().startswith("необхідні обов")), "")
    pm = PRE_RE.search(prereq_sec)
    nm = NEXT_RE.search(prereq_sec)
    prereq = _split_list(pm.group(1)) if pm else []
    nxt = _split_list(nm.group(1)) if nm else []
    if prereq_sec:
        ev("prereq", prereq_sec)

    meth = secs.get("Методи та критерії оцінювання", "") + " " + secs.get("Критерії оцінювання результатів навчання", "")
    mq = re.search(r"Підсумковий контроль[^.]*", meth, re.I)
    ev("control", mq.group(0) if mq else _sentence_with(meth, r"екзамен|залік"))
    points = {}
    for m in re.finditer(r"(\d{1,3})\s*бал\w*\s*(?:за|на)\s*([^.,;()]{3,60})", meth):
        points[m.group(2).strip()] = int(m.group(1))
    for m in re.finditer(r"([А-ЯІЇЄҐа-яіїєґ’' ]{4,50})\s*\((?:максимум\s*)?(\d{1,3})\s*бал", meth):
        points.setdefault(m.group(1).strip(" —-"), int(m.group(2)))
    if points:
        ev("assessment", _sentence_with(meth, r"\d{1,3}\s*бал"))
    low = normalize(text)
    kinds = [k for k, pat in (("lab", r"лабораторн"), ("prac", r"практичн\w* занят"), ("studio", r"студійн|студі[яї]"),
                              ("project", r"курсов\w* проєкт|курсов\w* проект|кп\b"), ("field", r"пленер|практик\w* на об"))
             if re.search(pat, low)]
    practice_type = kinds[0] if kinds else None

    comps_sec = secs.get("Завдання", "")
    prn_sec = secs.get("Результати навчання", "")
    if comps_sec:
        ev("comps", comps_sec[:200])
    if prn_sec:
        ev("prn", prn_sec[:200])
    lit = secs.get("Рекомендована література", "")
    if lit:
        ev("lit_years", lit[:200])
    ai_sec = next((v for k, v in secs.items() if "штучного інтелекту" in k.lower()), None)
    if ai_sec:
        ev("ai_policy", ai_sec[:200])

    notes = []
    if meta.get("control") and opp_course.get("control") and meta["control"] != opp_course["control"]:
        notes.append(f"форма контролю в силабусі «{meta['control']}», в ОП «{opp_course['control']}»")
    for h in meta.get("hours_total", []):
        if abs(h - opp_course["credits"] * 30) > 1:
            notes.append(f"у силабусі {h} год, а {opp_course['credits']:g} кр. = {opp_course['credits'] * 30:g} год")
    for s in meta.get("specialty_mentions", []):
        notes.append(f"згадано спеціальність «{s}»")
    if not meta.get("has_topic_plan"):
        notes.append("немає тематичного плану з годинами (силабус)")
    parts = [v for v in points.values() if v < 100]     # розбивка за видами робіт (не підсумкові «100 балів за …»)
    pts_sum = sum(parts)
    if len(parts) >= 3 and pts_sum != 100:
        notes.append(f"сума виділених балів {pts_sum} ≠ 100 (перевірити)")

    return dict(
        ok=opp_course["code"], title=opp_course["title"], status="ok", file=file_rel,
        year=None, kind=opp_course["type"] if opp_course["type"] != "вибіркова" else f"вибіркова ({block or opp_course.get('block')})",
        credits=opp_course["credits"], practice_type=practice_type, control=meta.get("control"),
        comps=meta.get("comps", []), prn=meta.get("prn", []), prereq=prereq, next=nxt,
        lectures=[], practice=[], assessment=points, lit_years=meta.get("lit_years", []),
        ai_policy=meta.get("ai_policy", False), notes=notes, evidence=evidence,
        summary=secs.get("Короткий зміст навчальної програми", ""), description=secs.get("Опис", ""),
        goal=secs.get("Мета вивчення дисципліни", ""),
    )


def missing_course(opp_course, reason="РП/силабус відсутній у наданих документах"):
    return dict(ok=opp_course["code"], title=opp_course["title"], status="missing", credits=opp_course["credits"],
                kind=opp_course["type"], control=None, comps=[], prn=[], prereq=[], next=[], lectures=[],
                practice=[], lit_years=[], notes=[reason], evidence=[])

# -*- coding: utf-8 -*-
"""Кандидати тем курсу з «Опису» / «Короткого змісту» силабуса (без моделі).

Силабуси не мають тематичного плану, тож теми виділяються з тексту за формою:
  1) явні маркери «Тема N.», «Лекція N.», «1. …»;
  2) шаблон «Назва теми. Студенти …» — тема = речення перед реченням про студентів;
  3) інакше — короткі речення-переліки.
Кожна тема — точна цитата з силабуса (доказ). Зведення тем різних курсів до спільного переліку
й рішення «чи справді тема належить курсу» — агентний крок (рецензент «матриця тем»).
"""
import re

STUD = re.compile(r"^(Студент|Здобувач|Слухач|Учасник)", re.I)
MARK = re.compile(r"(?:(?:ТЕМА|Тема|Лекція|Розділ|Блок)\s*\d+\s*[.:)]|(?<![\d.])\d{1,2}\.\s+(?=[А-ЯІЇЄҐ«]))")
SKIP = re.compile(r"(?i)^(мета|курс|програма складається|практичні заняття\s*[–-]|завдання аудиторних|дисципліна|в дисципліні|у дисципліні)")


def _clean(s):
    s = re.sub(r"\s+", " ", s).strip(" .;:-–—")
    return s


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[А-ЯІЇЄҐ«\d])", text) if s.strip()]


def candidate_topics(description, summary, max_topics=20):
    for src_name, text in (("Опис", description), ("Короткий зміст", summary)):
        if not text or len(text) < 80:
            continue
        # 1. явні маркери
        parts = MARK.split(text)
        if len(parts) >= 4:
            out = []
            for p in parts[1:]:
                first = re.split(r"(?<=[.!?])\s+", p.strip(), maxsplit=1)[0]
                t = _clean(first)
                if 6 <= len(t) <= 220 and not SKIP.match(t):
                    out.append(t)
            if len(out) >= 3:
                return out[:max_topics], src_name, "маркери тем"
        sents = _sentences(text)
        # 2. «Тема. Студенти …»
        heads = [_clean(sents[i - 1]) for i in range(1, len(sents)) if STUD.match(sents[i]) and not STUD.match(sents[i - 1])]
        heads = [h for h in heads if 6 <= len(h) <= 220 and not SKIP.match(h)]
        if len(heads) >= 2:
            return heads[:max_topics], src_name, "речення перед «Студенти …»"
        # 3. короткі речення-переліки
        short = [_clean(s) for s in sents if 8 <= len(s) <= 160 and not STUD.match(s) and not SKIP.match(s)]
        if len(short) >= 3:
            return short[:max_topics], src_name, "короткі речення"
    return [], None, None

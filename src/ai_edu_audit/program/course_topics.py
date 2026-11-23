# -*- coding: utf-8 -*-
"""Теми кожного силабуса і їх повтори в інших курсах (код; сумнівні пари переглядає аудитор).

Одиниця — тема з розділу «Опис» силабуса. Якщо розділ має речення «Студенти вивчають …, опановують …»,
кожна дієслівна частина стає окремою підтемою. Схожість — частка спільних основ слів (без службових).
"""
import re

STOP = set("""студенти студент вивчають вивчає опановують опановує знайомляться розглядають досліджують аналізують
набувають отримують засвоюють виконують створюють розробляють формують навчаються ознайомлюються вчаться освоюють
та і й а в у з із зі на до для від по при про як що це їх його її також а також основи основні основ поняття
особливості принципи методи засоби роль вступ загальні сучасні сучасних різних різні види типи процес процеси
етапи етап курс курсу дизайн дизайну дизайні середовища середовище середовищі середовищ програми програма дисципліни дисципліна теми тема робота роботи практичн аналіз застосування використання""".split())
VERB = r"[а-яіїєґʼ']+(?:ють|ять|ують|юють|ються|яться)"


def stem(w):
    return w[:6] if len(w) > 6 else w


def toks(s):
    s = s.lower().replace("’", "'").replace("ʼ", "'")
    ws = re.findall(r"[a-zа-яіїєґ0-9']{3,}", s)
    return {stem(w) for w in ws if w not in STOP and not any(w.startswith(x) for x in ("практичн",))}


def units(row):
    """[(назва, зміст)] — теми силабуса."""
    desc = row.get("description") or ""
    lect = [x.strip() for x in (row.get("lectures") or []) if len(x.strip()) > 6]
    out = []
    if "Студенти" in desc and lect:
        # розділ = назва теми + речення «Студенти …»
        parts = re.split(r"(?<=[.!?])\s+(?=Студенти\b)", desc)
        # назви тем — з lectures; зміст — речення, що йде після назви
        for i, t in enumerate(lect):
            j = desc.find(t)
            if j < 0:
                out.append((t, "")); continue
            rest = desc[j + len(t):]
            m = re.match(r"\.?\s*(Студенти[^.]*\.)", rest)
            body = m.group(1) if m else ""
            clauses = re.split(r",\s+(?=" + VERB + r"\b)|\s+(?:та|і|й)\s+(?=" + VERB + r"\b)", body) if body else []
            clauses = [c.strip(" .") for c in clauses if len(c.strip()) > 15]
            if len(clauses) >= 2:
                for c in clauses:
                    c2 = re.sub(r"^Студенти\s+", "", c)
                    out.append((t, c2[:1].upper() + c2[1:]))
            else:
                out.append((t, re.sub(r"^Студенти\s+", "", body).strip(" .")))
    else:
        out = [(t, "") for t in lect]
    # прибрати технічні рядки
    out = [(t, b) for t, b in out if not re.match(r"(?i)^(лабораторна|контрольна робота|самостійна робота:?$|блок «|\d\.\s*(рисунок|живопис)\s*$|формат|теми та|тематики викладені|варіанти\s*$)", t)]
    out = [(t, (b[:1].upper() + b[1:]) if b else b) for t, b in out]
    return out


def compare(rows, sem, codes):
    U = {c: units(rows[c]) for c in codes}
    T = {c: [toks(t + " " + b) for t, b in U[c]] for c in codes}
    res = {}
    for c in codes:
        lst = []
        for i, (t, b) in enumerate(U[c]):
            a = T[c][i]
            hits = []
            if len(a) >= 2:
                for d in codes:
                    if d == c:
                        continue
                    best = (0, None)
                    for k, bb in enumerate(T[d]):
                        if len(bb) < 2:
                            continue
                        inter = len(a & bb)
                        if a == bb:
                            sc = 1.0
                            if sc > best[0]:
                                best = (sc, k)
                            continue
                        if inter < 3:
                            continue
                        cont = inter / min(len(a), len(bb)); jac = inter / len(a | bb)
                        sc = round(0.6 * cont + 0.4 * jac, 2)
                        if sc > best[0]:
                            best = (sc, k)
                    if best[0] >= 0.55:
                        k = best[1]; ot, ob = U[d][k]
                        hits.append([d, ot + (f" — {ob}" if ob else ""), best[0]])
            hits.sort(key=lambda h: -h[2])
            top = hits[0][2] if hits else 0
            if top >= 0.8:
                st = "repeat"
            elif top >= 0.55:
                sd = sem.get(hits[0][0]); sc_ = sem.get(c)
                st = "dev" if (sd and sc_ and sd < sc_) else "near"
            else:
                st = "unique"
            lst.append([t, b, st, hits[:4]])
        res[c] = lst
    return res

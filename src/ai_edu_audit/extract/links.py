"""Зв'язки між курсами з розділу «Необхідні обов'язкові попередні та супутні навчальні дисципліни».

Шукає в розділі назви компонентів ОП (найдовші першими), розбирає мітки «Попередні / Супутні / Наступні»
і порівнює із семестрами. Формат зв'язку: [раніший, пізніший, вид, як написано, вердикт] — як у line.json.
"""
import re

SEC_RE = re.compile(r"(?:Необхідні\s+обов.язкові\s+попередні\s+та\s+супутні\s+навчальні\s+дисципліни|Пререквізити(?:\s+та\s+постреквізити)?|Міждисциплінарні\s+зв.язки)\s*:?(.{0,1600}?)(?=Короткий\s+зміст|Мета\s|Мета:|Завдання:|Результати\s+навчання|Опис:|\Z)", re.I | re.S)
LAB_RE = re.compile(r"(Попередні\s+та\s+супутні(?:\s+навчальні\s+дисципліни)?|Супутні\s+та\s+наступні(?:\s+навчальні\s+дисципліни)?|Попередні(?:\s+навчальні\s+дисципліни)?|Пререквізити|Супутні(?:\s+навчальні\s+дисципліни)?|Кореквізити|Наступні(?:\s+навчальні\s+дисципліни)?|Постреквізити)\s*[:\-–]?", re.I)
LAB_KIND = [("попередні та супутні", "mixed"), ("супутні та наступні", "conext"), ("попередні", "pre"), ("пререквізити", "pre"),
            ("супутні", "co"), ("кореквізити", "co"), ("наступні", "next"), ("постреквізити", "next")]


def norm(s):
    s = s.lower().replace("­", "")
    s = re.sub(r"-\s*\n\s*", "", s)
    s = re.sub(r"[’ʼ`´‘]", "'", s)
    s = s.replace("проєкт", "проект").replace("kп", "кп").replace("3d-", "3d ")
    s = re.sub(r"\bч\.\s*", "частина ", s)
    s = re.sub(r"\bв\b", "у", s)
    s = re.sub(r"[«»\"“”]", "", s)
    s = re.sub(r"\s+", " ", s)
    s = s.replace(" та ", " і ")
    return s


ALIASES = {"основи дизайну предметного середовища": "ОК2.5", "основи дизайну предметного середовища (кп)": "ОК2.20"}


def _variants(courses):
    """[(шаблон, [коди])] — довші першими. Частини курсу розгортаються: «…, частина 1, 2» / «ч.1, ч.2»."""
    out, parts = [], {}
    for c in courses:
        for t in c["title"].replace("**", "").split("/"):
            t = norm(t).strip(" ,.")
            if len(t) < 5:
                continue
            m = re.match(r"^(.*?),? частина (\d)$", t)
            if m:
                parts.setdefault(m.group(1).strip(" ,"), {})[m.group(2)] = c["code"]
            else:
                out.append((t, [c["code"]]))
    for t, c in ALIASES.items():
        out.append((t, [c]))
    for base, d in parts.items():
        out.append((base, d))  # dict → розбір номерів частин
    out.sort(key=lambda x: -len(x[0]))
    return out


def _find(seg, variants):
    """Знайдені коди з фрагментами тексту, без перекриття збігів."""
    s = norm(seg)
    used = [False] * len(s)
    found = []
    for pat, codes in variants:
        for m in re.finditer(re.escape(pat), s):
            a, b = m.span()
            if any(used[a:b]):
                continue
            if isinstance(codes, dict):
                tail = s[b:b + 60]
                nums = re.match(r"\s*\(?\s*(?:[іi] курс,?\s*)?((?:\s*(?:,|;|і|й)?\s*(?:частина\s*)?\d\b)+)", tail)
                ks = [k for k in re.findall(r"\d", nums.group(1)) if k in codes] if nums else []
                if ks:
                    b += nums.end()
                    sel = [codes[k] for k in ks]
                else:
                    sel = ["*" + "|".join(codes[k] for k in sorted(codes))]  # частини не названо
            else:
                sel = codes
            for i in range(a, b):
                used[i] = True
            found += [(c, s[a:b].strip(" ,;.")) for c in sel]
    return found


def extract_links(text, me, courses, sem):
    """Зв'язки курсу `me` з тексту його силабуса."""
    m = SEC_RE.search(text)
    if not m:
        return [], None
    sec = m.group(1)
    variants = _variants(courses)
    # поділ за мітками
    pieces, kind, pos = [], "mixed", 0
    for lm in LAB_RE.finditer(sec):
        pieces.append((kind, sec[pos:lm.start()]))
        lab = re.sub(r"\s+", " ", lm.group(1).lower())
        kind = next(k for p, k in LAB_KIND if lab.startswith(p))
        pos = lm.end()
    pieces.append((kind, sec[pos:]))
    links, seen = [], set()
    sm = sem.get(me)
    for kind, seg in pieces:
        found = []
        for other, frag in _find(seg, variants):
            if other.startswith("*"):  # частини не названо: беремо ті, що узгоджуються з видом зв'язку
                ps = [p for p in other[1:].split("|") if p != me]
                if kind == "next":
                    ok = [p for p in ps if sem.get(p) and sm and sem[p] > sm]
                else:
                    ok = [p for p in ps if sem.get(p) and sm and sem[p] <= sm]
                found += [(p, frag) for p in (ok or ps[:1])]
            else:
                found.append((other, frag))
        for other, frag in found:
            if other == me or (other, kind) in seen:
                continue
            seen.add((other, kind))
            so = sem.get(other)
            if sm is None or so is None:
                v = "unknown"
            k = {"pre": "prereq", "next": "next", "co": "coreq"}.get(kind)
            if kind == "mixed":
                k = "coreq" if so is not None and so == sm else "prereq"
            if kind == "conext":
                k = "coreq" if so is not None and so == sm else "next"
            if k == "next":
                a, b = me, other
            elif k == "prereq":
                a, b = other, me
            else:
                a, b = other, me
            if sm is None or so is None:
                v = "unknown"
            elif k == "coreq":
                v = "ok" if so == sm else "cosem"
            else:
                v = "ok" if sem[a] < sem[b] else "same" if sem[a] == sem[b] else "late"
            links.append([a, b, k, frag[:1].upper() + frag[1:], v, me])
    return links, re.sub(r"\s+", " ", sec).strip()

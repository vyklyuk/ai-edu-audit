# -*- coding: utf-8 -*-
"""Інвентаризація вхідних документів ОП: що є, чого бракує, що викликає сумнів.

Дешевий крок до витягу: класифікація файлів і перевірки робляться кодом, без моделі.
Результат — inventory.json (структуровано) і звіт для гаранта (report.py).

Перевірки (ТЗ, «Звіт про вхідні дані»): базові документи, повнота РП, дублікати, актуальність,
читабельність, сторонні файли, сліди копіювання, вердикт.
"""
import datetime as dt
import difflib
import os
import re
from collections import defaultdict

from .convert import convert_all, normalize, scan_pages, sha256

SKIP_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
MIN_TEXT_CHARS = 1500       # менше — порожній шаблон
SIM_COPY = 0.80             # схожість текстів двох РП (Жаккар 5-грам), вище — ймовірна копія
TITLE_MATCH = 0.82          # поріг схожості назв РП ↔ ОК


# ---------- допоміжне ----------

def norm_title(t):
    t = normalize(t)
    t = t.replace("проєкт", "проект").replace("3d-", "3d ").replace("ё", "е")
    t = re.sub(r"\((к[пp]|kп|kp)\)", " (кп) ", t)
    t = re.sub(r"[^\w() ]+", " ", t)
    t = re.sub(r"\b(і|та|й|и)\b", " ", t)
    t = re.sub(r"\b(у|в)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def is_kp(t):
    return "(кп)" in norm_title(t)


def base_title(t):
    return norm_title(t).replace("(кп)", "").strip()


def shingles(text, k=5):
    w = normalize(text).split()
    return {" ".join(w[i:i + k]) for i in range(max(0, len(w) - k + 1))}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


# ---------- розбір ОПП ----------

def office_doc_to_docx(path, cache_dir):
    """Для таблиць ОПП потрібен docx; .doc перетворюємо LibreOffice-ом."""
    if path.lower().endswith(".docx"):
        return path
    import shutil
    import subprocess
    import tempfile
    out = os.path.join(os.path.abspath(cache_dir), sha256(path)[:12] + ".docx")
    if os.path.exists(out):
        return out
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "opp" + os.path.splitext(path)[1])
        shutil.copy(path, src)
        subprocess.run([shutil.which("soffice"), f"-env:UserInstallation=file://{tmp}/prof", "--headless",
                        "--convert-to", "docx", "--outdir", tmp, src],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=170)
        shutil.copyfile(os.path.join(tmp, "opp.docx"), out)
    return out


def _cells(row):
    out = []
    for c in row.cells:
        x = " ".join(c.text.split())
        if not out or out[-1] != x:
            out.append(x)
    return out


def parse_opp_components(docx_path):
    """Перелік ОК з таблиці «Шифр ОК | Назва | Кредити | Форма контролю»."""
    import docx
    d = docx.Document(docx_path)
    table = next((t for t in d.tables if t.rows and "шифр ок" in " ".join(_cells(t.rows[0])).lower()), None)
    if table is None:
        return [], {}
    comps, section, block, block_name = [], "обов'язкова", None, None
    totals = {}
    for r in table.rows[1:]:
        cells = _cells(r)
        line = " ".join(cells)
        low = line.lower()
        if low.startswith("вибіркові освітні компоненти"):
            section = "вибіркова"
            continue
        if low.startswith("практика та підсумкова атестація"):
            section = "практика/атестація"
            continue
        m = re.match(r"лінія\s*(\d+)\.?\s*(.*)", low)
        if m:
            block, block_name = f"ВБ{m.group(1)}", line.split(".", 1)[-1].strip()
            continue
        if low.startswith("разом"):
            nums = [c for c in cells[1:] if re.fullmatch(r"[\d,]+", c)]
            if nums:
                totals[cells[0].rstrip(":")] = float(nums[0].replace(",", "."))
            continue
        if len(cells) < 3:
            continue
        code = re.sub(r"\.$", "", cells[0].split("(")[0].strip())
        title = cells[1]
        cr = re.sub(r"[^\d,\.]", "", cells[2]).replace(",", ".")
        if not title or not cr or re.fullmatch(r"\d+", title):
            continue
        kind = section
        if section == "практика/атестація":
            kind = "атестація" if "кваліфікаційн" in title.lower() and "практика" not in title.lower() else "практика"
        comps.append(dict(code=code or None, title=title, credits=float(cr),
                          control=cells[3] if len(cells) > 3 else "",
                          type=kind, block=block if section == "вибіркова" else None,
                          block_name=block_name if section == "вибіркова" else None,
                          free_choice=not code))
    return comps, totals


# ---------- розбір силабуса / РП ----------

SECTION_RE = re.compile(r"^([А-ЯІЇЄҐ][^:]{2,70}):\s*(.*)$", re.S)


def parse_syllabus(docx_path):
    import docx
    d = docx.Document(docx_path)
    paras = [p.text.strip() for p in d.paragraphs if p.text.strip()]
    text = "\n".join(paras)
    sections = {}
    for p in paras[1:]:
        m = SECTION_RE.match(p)
        if m:
            sections[m.group(1).strip()] = m.group(2).strip()
    lit = sections.get("Рекомендована література", "")
    years = [int(y) for y in re.findall(r"(?<!\d)(19[5-9]\d|20[0-3]\d)(?!\d)", lit)]
    meth = (sections.get("Методи та критерії оцінювання", "") + " " +
            sections.get("Критерії оцінювання результатів навчання", "")).lower()
    m_final = re.search(r"підсумковий контроль\s*[:\-–]\s*([^.;]{0,120})", meth)
    probe = m_final.group(1) if m_final else meth
    control = ("диф. залік" if re.search(r"диференційован\w* залік|диф\. ?залік", probe) else
               "екзамен" if re.search(r"екзамен|іспит", probe) else "залік" if "залік" in probe else None)
    spec = re.findall(r"спеціальност\w*\s*[«\"“]([^»\"”]{3,80})[»\"”]", text)
    hours_total = [int(h) for h in re.findall(r"охоплює\s*(\d+)\s*год", text)]
    return dict(
        title=paras[0] if paras else "",
        chars=len(text),
        sections=sorted(sections),
        has_topic_plan=len(re.findall(r"(?i)\bтема\s*\d", text)) >= 3,
        has_hours=bool(re.search(r"\d+\s*год", text)),
        hours_total=hours_total,
        comps=sorted(set(re.sub(r"\s+", "", c) for c in re.findall(r"\b(?:ЗК|СК|КС|ФК|ФКС)\s?\d+(?:\.\d+)?", text))),
        prn=sorted(set(re.sub(r"\s+", "", c) for c in re.findall(r"\b(?:ПРН|РН)\s?\d+(?:\.\d+)?", text))),
        prereq=sections.get("Необхідні обов'язкові попередні та супутні навчальні дисципліни",
                            sections.get("Необхідні обов’язкові попередні та супутні навчальні дисципліни", "")),
        lit_years=years,
        control=control,
        ai_policy=any("штучного інтелекту" in s.lower() for s in sections),
        specialty_mentions=sorted(set(s.strip() for s in spec)),
        text=text,
    )


# ---------- головна функція ----------

def classify(path, text):
    name = os.path.basename(path)
    low = normalize(text[:6000])
    if name.startswith("~$"):
        return "temp"
    if name in SKIP_NAMES:
        return "system"
    if "стандарт вищої освіти" in low:
        return "standard"
    if "освітньо-професійна програма" in low or "освітньо-наукова програма" in low:
        if "шифр ок" in normalize(text) or "перелік компонент" in normalize(text):
            return "program"
    if "навчальний план" in low[:600]:
        return "curriculum"
    if "мета вивчення дисципліни" in low or "робоча програма" in low[:800] or "силабус" in low[:800]:
        return "syllabus"
    if "програма практики" in low[:800] or "програма атестації" in low[:800]:
        return "practice"
    if "профес" in low[:300] and "стандарт" in low[:300]:
        return "prof_standard"
    return "other"


def semester_hint(rel):
    m = re.search(r"(\d)\s*семестр|семестр\s*(\d)", rel, re.I)
    return int(m.group(1) or m.group(2)) if m else None


def block_hint(rel):
    m = re.search(r"ВБ\s*(\d)", rel)
    return f"ВБ{m.group(1)}" if m else None


def run_inventory(root, work_dir, level="bachelor", program_year=None):
    root = os.path.abspath(root)
    text_dir = os.path.join(work_dir, "text")
    files = []
    for dp, _dn, fn in os.walk(root):
        for f in sorted(fn):
            files.append(os.path.join(dp, f))
    files.sort()
    convertible = [p for p in files if not os.path.basename(p).startswith("~$")
                   and os.path.basename(p) not in SKIP_NAMES
                   and os.path.splitext(p)[1].lower() in {".doc", ".docx", ".odt", ".rtf", ".pdf"}]
    conv = convert_all(convertible, text_dir)

    recs = []
    for p in files:
        rel = os.path.relpath(p, root)
        c = conv.get(p, {})
        pages = c.get("pages") or []
        text = "\n".join(pages)
        kind = classify(p, text) if c and not c.get("error") else (
            "temp" if os.path.basename(p).startswith("~$") else
            "system" if os.path.basename(p) in SKIP_NAMES else "unreadable")
        recs.append(dict(rel=rel, path=p, kind=kind, sha=c.get("sha"), pages=len(pages),
                         chars=len(text.strip()), scan_pages=scan_pages(pages) if pages else [],
                         ocr_pages=c.get("ocr_pages", []), error=c.get("error"),
                         text_file=os.path.relpath(c["text_path"], work_dir) if c.get("text_path") else None,
                         semester_folder=semester_hint(rel), block_folder=block_hint(rel),
                         size=os.path.getsize(p), mtime=dt.datetime.fromtimestamp(os.path.getmtime(p)).date().isoformat()))

    by_kind = defaultdict(list)
    for r in recs:
        by_kind[r["kind"]].append(r)

    # ---- ОПП ----
    program = None
    comps, totals = [], {}
    if by_kind["program"]:
        program = by_kind["program"][0]
        docx_path = office_doc_to_docx(program["path"], text_dir)
        comps, totals = parse_opp_components(docx_path)
    real_comps = [c for c in comps if not c["free_choice"]]

    # ---- силабуси ----
    syl = []
    for r in by_kind["syllabus"]:
        meta = {}
        if r["path"].lower().endswith(".docx"):
            meta = parse_syllabus(r["path"])
        else:
            meta = dict(title=os.path.splitext(os.path.basename(r["path"]))[0], text="", chars=r["chars"])
        r["syllabus"] = {k: v for k, v in meta.items() if k != "text"}
        syl.append((r, meta))

    # зіставлення РП ↔ ОК
    for r, meta in syl:
        cands = []
        for t in (meta.get("title", ""), os.path.splitext(os.path.basename(r["path"]))[0]):
            for c in real_comps:
                # складений ОК («А/Б, В») — порівнюємо з кожною альтернативою
                alts = [c["title"]] + [a for a in re.split(r"[/]", c["title"]) if a.strip()]
                s = max(ratio(base_title(t), base_title(a)) for a in alts)
                if len(alts) > 2 and any(base_title(t) and base_title(t) in base_title(a) for a in alts):
                    s = max(s, 0.9)
                kp_ok = is_kp(t) == is_kp(c["title"])
                cands.append((s + (0.05 if kp_ok else 0), s, kp_ok, c["code"], t))
        cands.sort(reverse=True)
        best = cands[0] if cands else None
        if best and best[1] >= TITLE_MATCH:
            r["match"] = dict(ok=best[3], score=round(best[1], 3), kp_consistent=best[2], by=best[4])
        else:
            r["match"] = dict(ok=None, score=round(best[1], 3) if best else 0, kp_consistent=None,
                              by=best[4] if best else None, nearest=best[3] if best else None)

    # одна РП на ОК: якщо є варіант з (КП) і без — віддати кожному свій
    by_ok = defaultdict(list)
    for r, _ in syl:
        if r["match"]["ok"]:
            by_ok[r["match"]["ok"]].append(r)

    # схожість текстів (сліди копіювання, дублікати)
    sh = {r["rel"]: shingles(m.get("text", "")) for r, m in syl}
    pairs = []
    rels = list(sh)
    for i in range(len(rels)):
        for j in range(i + 1, len(rels)):
            s = jaccard(sh[rels[i]], sh[rels[j]])
            if s >= SIM_COPY:
                pairs.append(dict(a=rels[i], b=rels[j], similarity=round(s, 3)))
    identical = defaultdict(list)
    for r in recs:
        if r["sha"]:
            identical[r["sha"]].append(r["rel"])

    # ---- перевірки ----
    issues = []

    def issue(check, severity, text, files=(), ok=None):
        issues.append(dict(check=check, severity=severity, text=text, files=list(files), ok=ok))

    opp_by_code_all = {c["code"]: c for c in real_comps}

    # 1. Базові документи
    base = dict(
        program=bool(by_kind["program"]), curriculum=bool(by_kind["curriculum"]),
        standard=bool(by_kind["standard"]), prof_standard=bool(by_kind["prof_standard"]),
        practice=bool(by_kind["practice"]))
    if not base["program"]:
        issue("base", "blocking", "Не знайдено ОП — без неї аудит неможливий")
    if not base["curriculum"]:
        issue("base", "blocking", "Не знайдено навчального плану (семестри, години, розподіл аудиторних занять)")
    if not base["standard"]:
        issue("base", "warning", "Не знайдено стандарту вищої освіти — доведеться спиратися на дескриптори НРК")
    if not base["prof_standard"]:
        issue("base", "info", "Профстандарту немає (для творчого профілю — не обов'язковий, замінюється ESCO і вимогами роботодавців)")
    std_info = None
    for r in by_kind["standard"]:
        t = normalize(open(os.path.join(work_dir, r["text_file"]), encoding="utf-8").read())
        m = re.search(r"спеціальність\s*(\d{3}|[а-яіїє]\d+)\s+([а-яіїє' ]+)", t)
        y = re.search(r"наказ[^\d]{0,80}(\d{2}\.\d{2}\.(\d{4}))", t)
        std_info = dict(code=m.group(1).upper() if m else None, name=m.group(2).strip() if m else None,
                        approved=y.group(1) if y else None, file=r["rel"])
    if std_info and std_info["code"] and std_info["code"].isdigit():
        issue("base", "warning",
              f"Стандарт — для спеціальності {std_info['code']} за переліком 2015 (наказ {std_info['approved']}); "
              "ОП — за новим кодом. Чи є затверджений стандарт для нового коду?", [std_info["file"]])
    for r in by_kind["standard"] + by_kind["program"]:
        if r["scan_pages"]:
            issue("readability", "info", f"Сторінки без текстового шару (скан): {r['scan_pages']} — "
                  "OCR недоступний; якщо там зміст, а не підписи, потрібен текстовий варіант", [r["rel"]])

    # 2. Повнота РП
    covered = set(by_ok)
    missing = [c for c in real_comps if c["code"] not in covered]
    for c in missing:
        sev = "warning"
        what = "РП"
        if c["type"] == "практика":
            what = "Програма практики"
        issue("completeness", sev, f"{what} відсутня: {c['code']} «{c['title']}» ({c['credits']:g} кр.)", ok=c["code"])
    for r, _ in syl:
        if not r["match"]["ok"]:
            issue("foreign", "warning",
                  f"РП не зіставлена з жодним ОК ОП (найближчий: {r['match'].get('nearest')}, "
                  f"схожість назв {r['match']['score']})", [r["rel"]])

    # 3. Дублікати
    missing_codes = {c["code"] for c in real_comps} - set(by_ok)
    for ok, rs in by_ok.items():
        if len(rs) > 1:
            sems = sorted({r["semester_folder"] for r in rs if r["semester_folder"]})
            hint = ""
            t = opp_by_code_all.get(ok, {}).get("title", "")
            m = re.search(r"частина\s*(\d+)", t)
            if m:
                nxt = re.sub(r"частина\s*\d+", f"частина {int(m.group(1)) + 1}", t)
                cand = [c["code"] for c in real_comps if c["title"] == nxt and c["code"] in missing_codes]
                if cand and len(sems) > 1:
                    hint = (f" Файли лежать у семестрах {sems}; частина {int(m.group(1)) + 1} ({cand[0]}) не має РП — "
                            "можливо, один із файлів мав бути нею.")
            issue("duplicates", "question", f"{ok}: {len(rs)} файли на один ОК — яку версію брати?{hint}",
                  [r["rel"] for r in rs], ok=ok)
    for sha, rels_ in identical.items():
        if len(rels_) > 1:
            issue("duplicates", "warning", "Побайтово однакові файли", rels_)

    # 4. Актуальність
    no_year = [r["rel"] for r, m in syl if not re.search(r"20\d\d\s*[/–-]\s*20\d\d\s*н", m.get("text", "").lower())]
    if no_year:
        issue("actuality", "info", f"Навчальний рік не вказано в {len(no_year)} з {len(syl)} РП — "
              "актуальність визначаємо лише за датою файлу і відповідністю ОП", no_year[:3] + (["…"] if len(no_year) > 3 else []))
    comp_codes = defaultdict(int)
    for r, m in syl:
        for c in m.get("comps", []):
            comp_codes[re.sub(r"\d.*", "", c)] += 1
    if comp_codes:
        issue("actuality", "info", "Префікси кодів компетентностей у РП: " +
              ", ".join(f"{k} — {v}" for k, v in sorted(comp_codes.items())) +
              " (звірити з кодами ОП на етапі витягу)")

    # 5. Читабельність і повнота змісту
    for r in by_kind["unreadable"]:
        issue("readability", "warning", f"Файл не читається: {r.get('error')}", [r["rel"]])
    for r, m in syl:
        if m.get("chars", 0) < MIN_TEXT_CHARS:
            issue("readability", "warning", "Майже порожній документ (шаблон?)", [r["rel"]])
    no_plan = [r["rel"] for r, m in syl if not m.get("has_topic_plan")]
    if syl and len(no_plan) >= len(syl) * 0.5:
        issue("content", "blocking",
              f"{len(no_plan)} з {len(syl)} документів — силабуси без тематичного плану: немає переліку тем "
              "лекцій і практичних занять з годинами. Метод вимагає повних РП (матриця тем, покриття практикою, "
              "трудомісткість). Чи є повні робочі програми?")

    # 6. Сторонні / службові файли
    for r in by_kind["temp"]:
        issue("foreign", "info", "Тимчасовий файл Word (~$…) — не документ, ігнорується", [r["rel"]])
    for r in by_kind["other"]:
        issue("foreign", "question", "Документ не схожий на ОП, план, стандарт чи РП — чи стосується аудиту?", [r["rel"]])

    # 7. Сліди копіювання
    for r, m in syl:
        t, fn = m.get("title", ""), os.path.splitext(os.path.basename(r["path"]))[0]
        if t and ratio(norm_title(t), norm_title(fn)) < 0.75:
            issue("copy_traces", "warning", f"Назва всередині «{t}» не відповідає назві файлу", [r["rel"]])
        if r["match"]["ok"] and r["match"]["kp_consistent"] is False:
            issue("copy_traces", "warning", "Позначка (КП) у назві РП не збігається з ОК", [r["rel"]], ok=r["match"]["ok"])
        for sname in m.get("specialty_mentions", []):
            if "інтер" not in normalize(sname) and "дизайн" not in normalize(sname):
                issue("copy_traces", "warning", f"Згадано іншу спеціальність: «{sname}»", [r["rel"]])
    for pr in pairs:
        issue("copy_traces", "warning", f"Тексти двох РП збігаються на {pr['similarity']:.0%}", [pr["a"], pr["b"]])

    # 8. Відповідність ОП (дешеві структурні звірки)
    opp_by_code = {c["code"]: c for c in real_comps}
    for r, m in syl:
        ok = r["match"]["ok"]
        if not ok:
            continue
        c = opp_by_code[ok]
        if m.get("control") and c["control"] and m["control"] != c["control"]:
            issue("consistency", "warning",
                  f"{ok}: форма контролю в РП «{m['control']}», в ОП «{c['control']}»", [r["rel"]], ok=ok)
        for h in m.get("hours_total", []):
            if abs(h - c["credits"] * 30) > 1:
                issue("consistency", "warning",
                      f"{ok}: у РП {h} год, а {c['credits']:g} кр. ОП = {c['credits'] * 30:g} год", [r["rel"]], ok=ok)
        if c["block"] and r["block_folder"] and c["block"] != r["block_folder"]:
            issue("consistency", "warning", f"{ok}: файл лежить у теці {r['block_folder']}, а в ОП — {c['block']}",
                  [r["rel"]], ok=ok)

    # підсумки кредитів ОП
    sums = defaultdict(float)
    for c in comps:
        sums[c["block"] or c["type"]] += c["credits"]
    struct = dict(totals=totals, sums={k: round(v, 2) for k, v in sums.items()})
    line_totals = {k: v for k, v in totals.items() if k.lower().startswith("разом за лінію")}
    cyc22 = next((v for k, v in totals.items() if re.search(r"цикл\s*2\.2\b", k)), None)
    if cyc22 and line_totals:
        for k, v in line_totals.items():
            if abs(v - cyc22) > 0.01:
                issue("consistency", "question",
                      f"«{k}» = {v:g} кр., а цикл 2.2 = {cyc22:g} кр.: чим добирається різниця {cyc22 - v:g} кр.?")
                break

    # ---- вердикт ----
    blocking = [i for i in issues if i["severity"] == "blocking"]
    hard_block = not base["program"]
    if hard_block:
        verdict = "insufficient"
    elif blocking:
        verdict = "sufficient_with_limits"
    else:
        verdict = "sufficient"

    n_rp = len(real_comps) - len([c for c in real_comps if c["type"] in ("практика", "атестація")])
    summary = dict(
        files=len(files), syllabi=len(syl), opp_components=len(real_comps),
        opp_disciplines=n_rp, covered=len(covered), missing=len(missing),
        free_choice_credits=sum(c["credits"] for c in comps if c["free_choice"]),
    )
    return dict(
        schema_version="1.0", root=root, generated=dt.datetime.now().isoformat(timespec="seconds"),
        level=level, base_documents=base, standard=std_info,
        program_file=program["rel"] if program else None, opp_components=comps, structure=struct,
        files=[{k: v for k, v in r.items() if k != "path"} for r in recs],
        similar_pairs=pairs, issues=issues, summary=summary, verdict=verdict,
        blocked=hard_block,
    )

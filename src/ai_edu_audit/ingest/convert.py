# -*- coding: utf-8 -*-
"""Перетворення документів ОП у текст зі сторінками.

doc / docx / odt → PDF (LibreOffice) → текст по сторінках (pdftotext); pdf → текст напряму;
сторінка без тексту → OCR (tesseract, ukr+eng), якщо він є.
Результат кешується за sha256 файлу: <cache>/<sha12>.txt, сторінки розділено символом \\f.
На цьому тексті потім перевіряються цитати витягу (етап «закоріненість у джерелі»).
"""
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata

OFFICE_EXT = {".doc", ".docx", ".odt", ".rtf"}
PDF_EXT = {".pdf"}
MIN_PAGE_CHARS = 40  # менше — вважаємо сторінку сканом без тексту


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _soffice():
    return shutil.which("soffice") or shutil.which("libreoffice")


def office_to_pdf(paths, outdir, timeout=170):
    """Пакетне перетворення офісних файлів у PDF. Повертає {шлях: pdf | None}."""
    exe = _soffice()
    if not exe:
        raise RuntimeError("Потрібен LibreOffice (soffice) для doc/docx")
    os.makedirs(outdir, exist_ok=True)
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        links = []
        for i, p in enumerate(paths):  # короткі імена: LibreOffice погано переносить довгі шляхи з кирилицею
            ext = os.path.splitext(p)[1].lower()
            dst = os.path.join(tmp, f"f{i:04d}{ext}")
            shutil.copy(p, dst)
            links.append((p, dst))
        profile = "file://" + os.path.join(tmp, "lo_profile")
        subprocess.run([exe, f"-env:UserInstallation={profile}", "--headless", "--convert-to", "pdf",
                        "--outdir", outdir, *[d for _, d in links]],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
        for p, d in links:
            pdf = os.path.join(outdir, os.path.splitext(os.path.basename(d))[0] + ".pdf")
            out[p] = pdf if os.path.exists(pdf) else None
    return out


_LANGS = None


def ocr_available():
    """OCR має сенс лише з українською моделлю tesseract (інакше кирилиця стає «латиницею»)."""
    global _LANGS
    if _LANGS is None:
        if not shutil.which("tesseract"):
            _LANGS = set()
        else:
            r = subprocess.run(["tesseract", "--list-langs"], capture_output=True, timeout=30)
            _LANGS = set(r.stdout.decode().split()[1:]) if r.returncode == 0 else set()
    return "ukr" in _LANGS


def scan_pages(pages):
    """Номери сторінок (з 1), на яких немає тексту."""
    return [i + 1 for i, t in enumerate(pages) if len(t.strip()) < MIN_PAGE_CHARS]


def pdf_pages(pdf, ocr=True):
    """Текст кожної сторінки PDF; порожні сторінки — через OCR. Повертає (pages, ocr_pages)."""
    res = subprocess.run(["pdftotext", "-enc", "UTF-8", pdf, "-"], capture_output=True, timeout=120)
    pages = res.stdout.decode("utf-8", "replace").split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    ocr_pages = []
    if ocr and ocr_available() and shutil.which("pdftoppm"):
        for i, t in enumerate(pages):
            if len(t.strip()) >= MIN_PAGE_CHARS:
                continue
            with tempfile.TemporaryDirectory() as tmp:
                base = os.path.join(tmp, "p")
                subprocess.run(["pdftoppm", "-r", "200", "-f", str(i + 1), "-l", str(i + 1), "-png", pdf, base],
                               capture_output=True, timeout=120)
                imgs = sorted(f for f in os.listdir(tmp) if f.endswith(".png"))
                if imgs:
                    r = subprocess.run(["tesseract", os.path.join(tmp, imgs[0]), "-", "-l", "ukr+eng"],
                                       capture_output=True, timeout=120)
                    txt = r.stdout.decode("utf-8", "replace")
                    if len(txt.strip()) >= MIN_PAGE_CHARS:
                        pages[i] = txt
                        ocr_pages.append(i + 1)
    return pages, ocr_pages


def convert_all(paths, cache_dir, ocr=True):
    """Перетворити список файлів. Повертає {шлях: {sha, text_path, pages, ocr_pages, error}}."""
    os.makedirs(cache_dir, exist_ok=True)
    info, todo_office = {}, []
    for p in paths:
        sha = sha256(p)
        txt = os.path.join(cache_dir, sha[:12] + ".txt")
        info[p] = dict(sha=sha, text_path=txt, pages=None, ocr_pages=[], error=None)
        if os.path.exists(txt):
            with open(txt, encoding="utf-8") as f:
                info[p]["pages"] = f.read().split("\f")
            continue
        ext = os.path.splitext(p)[1].lower()
        if ext in OFFICE_EXT:
            todo_office.append(p)
        elif ext in PDF_EXT:
            _finish(info[p], p, ocr)
        else:
            info[p]["error"] = f"непідтримуваний формат {ext}"
    if todo_office:
        pdf_dir = os.path.abspath(os.path.join(cache_dir, "pdf"))
        os.makedirs(pdf_dir, exist_ok=True)
        for i in range(0, len(todo_office), 25):  # пакети, щоб не впертися в ліміт часу
            batch = todo_office[i:i + 25]
            with tempfile.TemporaryDirectory() as out_tmp:  # спершу локально, потім у кеш під іменем sha
                try:
                    pdfs = office_to_pdf(batch, out_tmp)
                except Exception as e:  # noqa: BLE001
                    for p in batch:
                        info[p]["error"] = f"перетворення не вдалося: {e}"
                    continue
                for p in batch:
                    if pdfs.get(p):
                        dst = os.path.join(pdf_dir, info[p]["sha"][:12] + ".pdf")
                        shutil.copyfile(pdfs[p], dst)
                        _finish(info[p], dst, ocr)
                    else:
                        info[p]["error"] = "файл пошкоджений або не відкривається"
    return info


def _finish(rec, pdf, ocr):
    try:
        pages, ocr_pages = pdf_pages(pdf, ocr)
    except Exception as e:  # noqa: BLE001
        rec["error"] = f"не вдалося прочитати PDF: {e}"
        return
    rec["pages"], rec["ocr_pages"] = pages, ocr_pages
    with open(rec["text_path"], "w", encoding="utf-8") as f:
        f.write("\f".join(pages))


# ---------- нормалізація для пошуку цитат ----------

_APOS = "'’ʼ`´‘"
_DASH = "‐‑‒–—―−"


def normalize(text):
    """Нижній регістр, єдині апострофи/лапки/тире, без переносів і зайвих пробілів."""
    t = unicodedata.normalize("NFC", text).lower()
    for a in _APOS:
        t = t.replace(a, "'")
    for d in _DASH:
        t = t.replace(d, "-")
    t = re.sub(r"[«»„“”\"]", '"', t)
    t = re.sub(r"-\s*\n\s*", "", t)          # перенос слова
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def find_quote(pages, quote, min_words=6):
    """Номер сторінки (з 1), де знайдено цитату, 0 — якщо лише через межу сторінок, None — немає.

    Порядок: точний збіг у нормалізованому тексті; без пробілів (таблиці в PDF рвуть рядки);
    перші min_words слів цитати (довгі клітинки таблиць переносяться в інший стовпець тексту).
    """
    q = normalize(quote)
    if not q:
        return None
    norm_pages = [normalize(p) for p in pages]
    for i, p in enumerate(norm_pages):
        if q in p:
            return i + 1
    q_ns = q.replace(" ", "")
    for i, p in enumerate(norm_pages):
        if q_ns in p.replace(" ", ""):
            return i + 1
    if q_ns in "".join(norm_pages).replace(" ", ""):
        return 0
    words = q.split()
    if len(words) >= min_words:
        head = "".join(words[:min_words])
        for i, p in enumerate(norm_pages):
            if head in p.replace(" ", ""):
                return i + 1
    # слова цитати в тому самому порядку з невеликими вставками (колонтитули, мітки сусідніх клітинок)
    for i, p in enumerate(norm_pages + ["\n".join(norm_pages)]):
        if _ordered_with_gaps(words, p.split()):
            return i + 1 if i < len(norm_pages) else 0
    return None


def _ordered_with_gaps(qw, pw, max_gap=12, min_share=0.9):
    if len(qw) < 4:
        return False
    starts = [k for k in range(len(pw)) if pw[k] == qw[0]]
    for st in starts:
        j, k, found, gap = 1, st + 1, 1, 0
        while j < len(qw) and k < len(pw) and gap <= max_gap:
            if pw[k] == qw[j]:
                j += 1
                found += 1
                gap = 0
            else:
                gap += 1
            k += 1
        if found / len(qw) >= min_share and j >= len(qw) * min_share:
            return True
    return False

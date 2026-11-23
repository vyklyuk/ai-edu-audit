# -*- coding: utf-8 -*-
"""python -m ai_edu_audit.extract <тека прогону> [--decisions decisions.json]

Читає inventory.json і рішення гаранта, пише program.json, courses.jsonl і grounding.json
(перевірка: кожна цитата знайдена в тексті джерела).
"""
import argparse
import json
import os

from .program_opp import extract_program
from ..ingest.convert import find_quote
from .syllabus import extract_course, missing_course
from .topics import candidate_topics


def _pages(run_dir, rec):
    with open(os.path.join(run_dir, rec["text_file"]), encoding="utf-8") as f:
        return f.read().split("\f")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m ai_edu_audit.extract")
    ap.add_argument("run_dir")
    a = ap.parse_args(argv)
    run = a.run_dir
    inv = json.load(open(os.path.join(run, "inventory.json"), encoding="utf-8"))
    dec_path = os.path.join(run, "decisions.json")
    dec = json.load(open(dec_path, encoding="utf-8")) if os.path.exists(dec_path) else {}
    use_file = dec.get("use_file", {})          # ОК -> відносний шлях вибраної версії
    excluded = set(dec.get("excluded", []))

    from ..ingest.inventory import office_doc_to_docx
    opp_rec = next(f for f in inv["files"] if f["kind"] == "program")
    opp_docx = office_doc_to_docx(os.path.join(inv["root"], opp_rec["rel"]), os.path.join(run, "text"))
    program = extract_program(opp_docx, _pages(run, opp_rec), inv, inv.get("standard"))

    opp = {c["code"]: c for c in inv["opp_components"] if c["code"]}
    by_ok = {}
    for f in inv["files"]:
        m = f.get("match") or {}
        if f["kind"] == "syllabus" and m.get("ok"):
            by_ok.setdefault(m["ok"], []).append(f)
    rows = []
    for code, c in opp.items():
        files = by_ok.get(code, [])
        if code in use_file:
            files = [f for f in files if f["rel"] == use_file[code]] or files
        if not files:
            rows.append(missing_course(c, "виключено з аудиту рішенням гаранта: документ відсутній"
                                       if code in excluded else "РП/силабус відсутній у наданих документах"))
            continue
        f = files[0]
        row = extract_course(f["rel"], os.path.join(inv["root"], f["rel"]), _pages(run, f), c, c.get("block"))
        topics, src, how = candidate_topics(row.get("description", ""), row.get("summary", ""))
        pages = _pages(run, f)
        row["lectures"] = topics
        row["topics_source"] = f"силабус: «{src}» ({how})" if src else "тем не виділено"
        for i, t in enumerate(topics):
            row["evidence"].append(dict(field=f"lectures[{i}]", quote=t[:200], file=f["rel"], page=find_quote(pages, t[:200])))
        if len(by_ok.get(code, [])) > 1:
            row["notes"].append(f"знайдено {len(by_ok[code])} версії; взято {f['rel']}")
        rows.append(row)

    with open(os.path.join(run, "program.json"), "w", encoding="utf-8") as fh:
        json.dump(program, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(run, "courses.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    evs = program["evidence"] + [e for r in rows for e in r.get("evidence", [])]
    lost = [e for e in evs if e["page"] is None]
    g = dict(total=len(evs), found=len(evs) - len(lost), share=round((len(evs) - len(lost)) / max(1, len(evs)), 4),
             not_found=lost)
    with open(os.path.join(run, "grounding.json"), "w", encoding="utf-8") as fh:
        json.dump(g, fh, ensure_ascii=False, indent=1)
    print(f"program.json: {len(program['courses'])} ОК, {len(program['competences'])} компетентностей, "
          f"{len(program['outcomes'])} ПРН; courses.jsonl: {len(rows)} рядків "
          f"({sum(r['status'] == 'missing' for r in rows)} missing); цитати знайдено {g['found']}/{g['total']}")


if __name__ == "__main__":
    main()

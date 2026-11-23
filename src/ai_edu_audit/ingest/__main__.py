# -*- coding: utf-8 -*-
"""python -m ai_edu_audit.ingest <тека з документами ОП> <тека прогону> [--title "…"]

Перетворює документи в текст, проводить інвентаризацію, пише inventory.json і inventory.md.
"""
import argparse
import json
import os

from .inventory import run_inventory
from .report import build_questions, render_markdown


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m ai_edu_audit.ingest")
    ap.add_argument("docs")
    ap.add_argument("run_dir")
    ap.add_argument("--title", default="ОП")
    ap.add_argument("--level", default="bachelor")
    a = ap.parse_args(argv)
    os.makedirs(a.run_dir, exist_ok=True)
    inv = run_inventory(a.docs, a.run_dir, level=a.level)
    inv["questions"] = build_questions(inv)
    with open(os.path.join(a.run_dir, "inventory.json"), "w", encoding="utf-8") as f:
        json.dump(inv, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.run_dir, "inventory.md"), "w", encoding="utf-8") as f:
        f.write(render_markdown(inv, a.title))
    print(inv["verdict"], inv["summary"])
    print("записано", os.path.join(a.run_dir, "inventory.md"))


if __name__ == "__main__":
    main()

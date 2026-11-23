# -*- coding: utf-8 -*-
"""python -m ai_edu_audit.calc <тека лінії> [-o data.json]

Тека лінії містить line.json і courses.jsonl. Без -o пише data.json у ту саму теку.
"""
import argparse
import os

from ..io import read_json, read_jsonl, write_data
from .line import build_line_data


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m ai_edu_audit.calc", description="Розрахунок даних хабу лінії")
    ap.add_argument("line_dir")
    ap.add_argument("-o", "--out")
    a = ap.parse_args(argv)
    line = read_json(os.path.join(a.line_dir, "line.json"))
    courses = read_jsonl(os.path.join(a.line_dir, "courses.jsonl"))
    data = build_line_data(line, courses)
    out = a.out or os.path.join(a.line_dir, "data.json")
    write_data(data, out)
    print("B1 лінії", data["b1"], "B2", data["b2"])
    print("Індекс програми (до → хвиля 1 → хвиля 2):", data["prog_index"])
    print("записано", out)


if __name__ == "__main__":
    main()

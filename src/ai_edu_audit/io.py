# -*- coding: utf-8 -*-
"""Читання й запис файлів даних в одному детермінованому форматі."""
import json


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def dumps_data(obj):
    """Формат data.json еталону: UTF-8 без екранування, стандартні роздільники."""
    return json.dumps(obj, ensure_ascii=False)


def write_data(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(dumps_data(obj))

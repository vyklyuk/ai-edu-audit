# -*- coding: utf-8 -*-
"""JSON Schema файлів даних і перевірка за ними (потрібен пакет jsonschema)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = ("course", "line_inputs", "data_line", "program", "finding")


def load(name):
    with open(os.path.join(HERE, f"{name}.schema.json"), encoding="utf-8") as f:
        return json.load(f)


def errors(name, obj):
    """Список повідомлень про помилки (порожній — документ відповідає схемі)."""
    import jsonschema
    v = jsonschema.Draft202012Validator(load(name))
    return [f"{'/'.join(map(str, e.absolute_path)) or '<корінь>'}: {e.message}" for e in v.iter_errors(obj)]

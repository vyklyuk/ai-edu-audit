# -*- coding: utf-8 -*-
"""Конфігурація моделей: який постачальник і яка модель виконує кожен агентний крок."""
import os
from dataclasses import dataclass

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

STEPS = ("inventory", "extract", "research", "review", "fix")


@dataclass
class StepConfig:
    provider: str
    model: str
    max_retries: int = 2
    temperature: float | None = None


def load_models_config(path=None):
    """Читає config/models.toml (або шлях з AI_EDU_MODELS). Повертає {крок: StepConfig}."""
    path = path or os.environ.get("AI_EDU_MODELS") or os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "config", "models.toml")
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    default = cfg.get("default", {})
    out = {}
    for step in STEPS:
        merged = dict(default, **cfg.get("steps", {}).get(step, {}))
        out[step] = StepConfig(**merged)
    return out

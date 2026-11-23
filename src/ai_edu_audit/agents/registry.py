# -*- coding: utf-8 -*-
"""Вибір адаптера за конфігурацією і виклик кроку з перевіркою відповіді за схемою."""
from .base import StepOutputError, StepRequest, StepResult
from .config import load_models_config

_ADAPTERS = {}


def register(provider, factory):
    _ADAPTERS[provider] = factory


def _adapter(provider):
    if provider not in _ADAPTERS:
        if provider == "anthropic":
            from .claude_sdk import ClaudeAgentAdapter
            register("anthropic", ClaudeAgentAdapter)
        else:
            raise KeyError(f"Немає адаптера для постачальника «{provider}»")
    return _ADAPTERS[provider]()


def run_step(req: StepRequest, config=None) -> StepResult:
    """Виконати агентний крок моделлю з конфігурації; відповідь перевіряється за req.output_schema."""
    import jsonschema
    cfg = (config or load_models_config())[req.step]
    adapter = _adapter(cfg.provider)
    last_err = None
    for _ in range(cfg.max_retries + 1):
        res = adapter.run(req, cfg.model, temperature=cfg.temperature)
        try:
            jsonschema.validate(res.output, req.output_schema)
            return res
        except jsonschema.ValidationError as e:
            last_err = e
    raise StepOutputError(f"Крок {req.step}: відповідь не відповідає схемі: {last_err.message}")

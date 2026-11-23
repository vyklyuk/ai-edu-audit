# -*- coding: utf-8 -*-
"""Адаптер Claude Agent SDK — єдине місце, де код залежить від SDK конкретного постачальника.

Статус: заготовка. Справжні виклики підключаються на етапі витягу (етап 5 плану), коли буде
відомо з прототипу, які інструменти й розміри контексту потрібні кожному кроку.
"""
from .base import StepRequest, StepResult


class ClaudeAgentAdapter:
    def run(self, req: StepRequest, model: str, **options) -> StepResult:
        try:
            import claude_agent_sdk  # noqa: F401
        except ModuleNotFoundError as e:
            raise RuntimeError("Встановіть claude-agent-sdk: pip install claude-agent-sdk") from e
        raise NotImplementedError("Адаптер Claude Agent SDK буде реалізовано на етапі витягу")

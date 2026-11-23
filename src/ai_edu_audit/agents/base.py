# -*- coding: utf-8 -*-
"""Єдиний інтерфейс агентного кроку: інструкція + вхідні дані → JSON за схемою.

Кожен крок (витяг, дослідження, рецензія, виправлення) викликається однаково, а постачальника
й модель для нього задає config/models.toml. Можливості конкретного SDK ізольовані в адаптерах
(agents/claude_sdk.py тощо), тож перенесення на іншу модель = зміна конфігурації + прогін
еталонних тестів, без змін у конвеєрі.
"""
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class StepRequest:
    step: str                       # extract | inventory | research | review | fix
    instruction: str                # текст інструкції (частина навички + завдання кроку)
    inputs: dict[str, Any]          # вхідні дані кроку (тексти РП, записи даних, зауваження …)
    output_schema: dict[str, Any]   # JSON Schema відповіді
    files: list[str] = field(default_factory=list)   # шляхи до першоджерел, до яких крок має доступ
    tools: list[str] = field(default_factory=list)   # дозволені інструменти: web_search, web_fetch, read_file


@dataclass
class StepResult:
    output: Any                     # JSON, що пройшов перевірку за output_schema
    model: str
    usage: dict[str, int] = field(default_factory=dict)   # токени: input, output
    raw: str | None = None          # сира відповідь для журналу


class ModelAdapter(Protocol):
    """Адаптер постачальника. Реалізація має повернути JSON, що відповідає output_schema."""

    def run(self, req: StepRequest, model: str, **options: Any) -> StepResult: ...


class StepOutputError(RuntimeError):
    """Модель повернула відповідь, що не відповідає схемі, навіть після повторів."""

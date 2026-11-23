# AI-Edu Audit

Пілотний застосунок автоматичного аудиту освітніх програм за методикою AI-Edu.
Технічне завдання: `../Навички_AI-Edu/AI-Edu_Audit_технічне_завдання.docx`.

> Конфіденційно. `src/ai_edu_audit/calc/methodology.py` і `scoring.py` містять формули, пороги,
> ваги й вето методики. Передавати лише своїй команді.
> © 2026 Ярослав Виклюк. Концепція та методика AI-Edu — НУ «Львівська політехніка».

## Встановлення (macOS)

```bash
cd AI_Edu/ai_edu_audit
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # ядро + тести
# pip install -e ".[agents]"     # Claude Agent SDK — знадобиться з етапу витягу
python -m pytest                 # 11 тестів, зокрема регресійний на лінії 1
```

Без встановлення тести також працюють: `python3 -m unittest discover tests`
(тест схем пропуститься, якщо немає `jsonschema`).

## Розрахунок лінії

```bash
python -m ai_edu_audit.calc data/reference/line1 -o /tmp/data.json
```

Тека лінії містить `line.json` (вхідні дані) і `courses.jsonl` (витяг РП). Результат — `data.json`,
тобто об'єкт `D` хабу лінії. На еталоні лінії 1 результат побайтово збігається з `expected/data.json`.

## Структура

| Шлях | Що це |
|---|---|
| `src/ai_edu_audit/calc/methodology.py` | метрики, цілі, допуски, ваги, вето, пороги (методика) |
| `src/ai_edu_audit/calc/scoring.py` | бал метрики, ознака проблеми, підсумок курсу, бал P-метрики |
| `src/ai_edu_audit/calc/line.py` | розрахунок лінії: вердикти зв'язків, B1/B2, консенсус, P1–P12, бали курсів |
| `src/ai_edu_audit/schemas/` | JSON Schema: `course`, `program`, `line_inputs`, `data_line`, `finding` |
| `src/ai_edu_audit/agents/` | єдиний інтерфейс агентного кроку, конфіг моделей, адаптер Claude (заготовка) |
| `config/models.toml` | постачальник і модель для кожного кроку |
| `data/reference/line1/` | еталон лінії 1: `line.json`, `courses.jsonl`, `recs.json`, `details.json`, `expected/data.json` |
| `tools/extract_reference.py` | одноразове перенесення `build_data.py` у `line.json` (з перевіркою методики) |
| `tests/` | регресія лінії 1, властивості балу, схеми |

## Інвентаризація вхідних даних

```bash
python -m ai_edu_audit.ingest "../ООП/ОП Інтер_єр та просторовий дизай _ В2" runs/interior_b \
    --title "ОПП «Інтер'єр та просторовий дизайн», бакалавр"
```

Потрібні LibreOffice (`soffice`) і poppler (`pdftotext`, `pdftoppm`); для сканів — `tesseract` з моделлю `ukr`
(macOS: `brew install --cask libreoffice && brew install poppler tesseract tesseract-lang`).
Результат у теці прогону: `text/` (текст кожного документа зі сторінками, кеш за sha256), `inventory.json`,
`inventory.md` — звіт і питання гаранту. Без підтвердження гаранта витяг не запускається.

## Конвеєр прототипу (ОП «Інтер'єр», лінія L1)

```bash
R=runs/interior_b
python -m ai_edu_audit.ingest "../ООП/ОП Інтер_єр та просторовий дизай _ В2" $R   # інвентаризація + звіт гаранту
# рішення гаранта й припущення: $R/decisions.json, $R/assumptions.json
python -m ai_edu_audit.extract $R          # program.json, courses.jsonl, grounding.json
(cd $R/line_L1 && python build_recs.py)    # line.json, recs.json, details.json (судження аудитора записані в коді)
python -m ai_edu_audit.calc $R/line_L1     # data.json
python -m ai_edu_audit.hubs.build $R       # hubs/overview.html, hubs/line_L1.html
```

Хаби мають вкладку «Вхідні дані й припущення»: що відсутнє, що прийнято замість цього, вплив, журнал перевірок.

## Що в `line.json` обчислюється, а що задано

Обчислюються кодом: вердикти пререквізитів, B1/B2, консенсусні теми, P1 (повнота РП), P4, P5, P6,
P7, P8 (вік літератури з `courses.jsonl`), P9 (частка лабораторних з годин РП), бали й вето курсів, індекс.

Задано як вхідні дані (у майбутньому наповнюють агенти з доказами): паспорт корпусу, зв'язки з РП,
матриця тем, частки попиту, покриття тем університетами, значення 24 метрик курсів у трьох станах,
решта P-метрик. Значення в `program_metrics.values` може бути числом або посиланням `{"calc": …}`.

## Хаб усієї ОП (зафіксована версія v1, 23.11.2026)

```bash
R=runs/interior_b
(cd $R && PYTHONPATH=../../src python3 ../../tools/extract_links_all.py)   # зв'язки з усіх силабусів → links_all.json
PYTHONPATH=src python3 -m ai_edu_audit.program $R        # дані хабу ОП → $R/program/*.json
PYTHONPATH=src python3 -m ai_edu_audit.hubs.build $R     # $R/hubs/program.html — основний звіт (лінія L1 входить у нього) + overview.html; окремий хаб лінії — ключ --line-hubs
PYTHONPATH=src python3 -m unittest discover -s tests     # зокрема tests/test_program_hub.py — фіксація вигляду v1
```

- Шаблон вигляду — `src/ai_edu_audit/hubs/templates/hub.html` (один для хабу лінії й хабу ОП). Його ключові елементи
  (ширина, меню, перемикачі циклів, матриця тем, теми курсів, провідні програми, згорнуті шляхи) перевіряє `tests/test_program_hub.py`.
- Загальний код збірки — `src/ai_edu_audit/program/`; судження аудитора для конкретної ОП — `runs/<прогон>/program/`:
  `notes_program.py` (цикли й тексти висновків), `topics_program.py` (теми), `unis_program.py` (провідні програми), `paths_program.py` (шляхи вдосконалення).
  Нова ОП = новий прогон з такими самими чотирма файлами.
- Незмінні копії звітів — `archive/` (відкриваються без коду).
- Методика (`src/ai_edu_audit/calc/methodology.py`) конфіденційна: репозиторій — лише приватний.

## Стан етапів

- [x] 1. Каркас проєкту
- [x] 2. Розрахунковий модуль і схеми даних (регресія лінії 1 — побайтово)
- [x] 3. Прототип на ОП «Інтер'єр та просторовий дизайн»: огляд ОП + лінія L1 (рецензенти-агенти — ще ні)
- [ ] 4. Збір та інвентаризація
- [ ] 5. Витяг з цитатами
- [ ] 6. Перевірки, рецензенти, цикл виправлення
- [ ] 7. Хаби
- [ ] 8. Локальний вебінтерфейс
- [ ] 9. Пілот і затвердження

# -*- coding: utf-8 -*-
"""Звіт про вхідні дані для гаранта (markdown) з inventory.json.

Звіт оцінює документи, а не людей: жодних прізвищ (ні авторів РП, ні з метаданих файлів).
"""
import os
from collections import defaultdict

VERDICT = {
    "sufficient": "Достатньо",
    "sufficient_with_limits": "Достатньо з обмеженнями",
    "insufficient": "Недостатньо",
}
BASE = [("program", "Освітня програма (перелік ОК, компетентності, ПРН, матриці)"),
        ("curriculum", "Навчальний план (семестри, години, види занять)"),
        ("standard", "Стандарт вищої освіти"),
        ("prof_standard", "Профстандарт"),
        ("practice", "Програми практик і атестації")]


def _short(rel):
    return os.path.basename(rel)


def build_questions(inv):
    """Конкретні питання гаранту, з яких складається діалог перед витягом."""
    q = []
    by = defaultdict(list)
    for i in inv["issues"]:
        by[i["check"]].append(i)
    if any(i["severity"] == "blocking" for i in by["content"]):
        q.append(dict(id="Q-full-rp", text="Документи в теці — силабуси без тематичного плану й годин. Чи є повні "
                      "робочі програми (теми лекцій і практичних/студійних занять з годинами, розподіл балів)? "
                      "Якщо ні — аудит піде з обмеженнями: матриця тем і метрики практикуму рахуватимуться за "
                      "«Коротким змістом», з позначкою «оцінка за силабусом».",
                      options=["Докладу повні РП", "Продовжити за силабусами з обмеженнями"]))
    if not inv["base_documents"]["curriculum"]:
        q.append(dict(id="Q-curriculum", text="Навчального плану немає. Семестри зараз беруться лише з назв тек "
                      "(«3 семестр» тощо), години аудиторних занять невідомі. Чи можете докласти навчальний план?",
                      options=["Докладу план", "Брати семестри з тек"]))
    for i in by["base"]:
        if "Стандарт — для спеціальності" in i["text"]:
            q.append(dict(id="Q-standard", text=i["text"] + " Якщо нового немає, беремо стандарт 022 (2018) "
                          "і дескриптори НРК 6-го рівня.", options=["Є новий — докладу", "Брати стандарт 022"]))
    for i in by["duplicates"]:
        if i["severity"] == "question":
            q.append(dict(id=f"Q-dup-{i['ok']}", text=i["text"], files=i["files"],
                          options=[_short(f) + " (тека " + f.split(os.sep)[1] + ")" if len(f.split(os.sep)) > 2 else f
                                   for f in i["files"]]))
    miss = [i for i in by["completeness"]]
    if miss:
        q.append(dict(id="Q-missing", text=f"Немає {len(miss)} документів (див. «Повнота»). Докласти чи свідомо "
                      "виключити з аудиту? Виключені ОК буде видно в хабі.",
                      options=["Докладу", "Виключити відсутні", "Частково — уточню"]))
    for i in by["consistency"]:
        if i["severity"] == "question":
            q.append(dict(id="Q-credits", text=i["text"] + " (Можливо, 6 кр. — дисципліна вільного вибору "
                          "з каталогу; уточніть.)", options=["Так, це вільний вибір", "Інше — уточню"]))
    q.append(dict(id="Q-roles", text="На які 1–3 ролі чи траєкторії готує ОП і приблизні частки випускників "
                  "(напр. дизайнер інтер'єру в студії, дизайнер просторів / виставок, фриланс)? Це задає джерела "
                  "зовнішнього попиту (профіль «творчий»).", options=[]))
    q.append(dict(id="Q-scope", text="Межі аудиту: огляд усієї ОП + поглиблення однієї лінії. Яку лінію "
                  "поглиблювати першою — запропонувати мені за пріоритетом чи у вас є вибір?",
                  options=["Запропонуй за пріоритетом", "Мій вибір — уточню"]))
    return q


def render_markdown(inv, title):
    s = inv["summary"]
    by = defaultdict(list)
    for i in inv["issues"]:
        by[i["check"]].append(i)
    L = []
    a = L.append
    a(f"# Звіт про вхідні дані · {title}")
    a("")
    a(f"Сформовано: {inv['generated'][:16].replace('T', ' ')} · рівень: бакалавр · файлів у теці: {s['files']}")
    a("")
    a(f"## Вердикт: **{VERDICT[inv['verdict']]}**")
    a("")
    blocking = [i for i in inv["issues"] if i["severity"] == "blocking"]
    if blocking:
        a("Що обмежує аудит:")
        a("")
        for i in blocking:
            a(f"- {i['text']}")
        a("")
    a(f"ОП містить **{s['opp_components']}** освітніх компонентів (+ {s['free_choice_credits']:g} кр. вільного вибору); "
      f"документ знайдено для **{s['covered']}**, бракує **{s['missing']}**. Силабусів у теці: {s['syllabi']}.")
    a("")

    a("## 1. Базові документи")
    a("")
    a("| Документ | Є? |")
    a("|---|---|")
    for k, name in BASE:
        a(f"| {name} | {'так' if inv['base_documents'][k] else '**ні**'} |")
    a("")
    for i in by["base"] + by["readability"]:
        a(f"- {i['text']}")
    a("")

    a("## 2. Повнота: ОК з ОП ↔ знайдені документи")
    a("")
    if by["completeness"]:
        for i in by["completeness"]:
            a(f"- {i['text']}")
    else:
        a("Усі ОК мають документ.")
    a("")

    a("## 3. Зміст документів")
    a("")
    for i in by["content"]:
        a(f"- {i['text']}")
    ai = [f for f in inv["files"] if f.get("syllabus", {}).get("ai_policy")]
    a(f"- Політика використання ШІ є в {len(ai)} з {s['syllabi']} документів.")
    a("")

    a("## 4. Дублікати")
    a("")
    for i in by["duplicates"] or [dict(text="Не виявлено.", files=[])]:
        a(f"- {i['text']}" + (" Файли: " + "; ".join(i["files"]) if i["files"] else ""))
    a("")

    a("## 5. Відповідність ОП")
    a("")
    ctrl = [i for i in by["consistency"] if "форма контролю" in i["text"]]
    other = [i for i in by["consistency"] if i not in ctrl]
    if ctrl:
        a(f"Форма підсумкового контролю в документі не збігається з ОП — **{len(ctrl)}** ОК:")
        a("")
        a("| ОК | У документі | В ОП |")
        a("|---|---|---|")
        for i in ctrl:
            t = i["text"]
            rp = t.split("«")[1].split("»")[0]
            op = t.split("«")[2].split("»")[0]
            a(f"| {i['ok']} | {rp} | {op} |")
        a("")
    for i in other:
        a(f"- {i['text']}")
    a("")

    a("## 6. Сліди копіювання (попередження)")
    a("")
    for i in by["copy_traces"] or [dict(text="Не виявлено.", files=[])]:
        files = " · ".join(_short(f) for f in i["files"])
        a(f"- {i['text']}" + (f" — {files}" if files else ""))
    a("")

    a("## 7. Актуальність і сторонні файли")
    a("")
    for i in by["actuality"] + by["foreign"]:
        files = " · ".join(_short(f) for f in i["files"] if f != "…")
        a(f"- {i['text']}" + (f" — {files}" if files and i["check"] == "foreign" else ""))
    a("")

    a("## Питання до гаранта")
    a("")
    for n, q in enumerate(build_questions(inv), 1):
        opts = f" _Варіанти: {' / '.join(q['options'])}._" if q.get("options") else ""
        a(f"{n}. {q['text']}{opts}")
    a("")
    a("Без підтвердження гаранта витяг і аналіз не запускаються. Рішення записуються в журнал аудиту.")
    a("")
    return "\n".join(L)

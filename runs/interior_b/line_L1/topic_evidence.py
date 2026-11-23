# -*- coding: utf-8 -*-
"""Докази для клітинок матриці тем: речення силабуса, де тема присутня (точна цитата)."""
import re

KW = {
 "T01": [r"конструктивн", r"пропорц", r"побудов"],
 "T02": [r"тональн", r"світлотін", r"фактур", r"матеріальн", r"гризайл"],
 "T03": [r"перспектив", r"ізометр", r"в інтер.єрі", r"простор\w* середовищ"],
 "T04": [r"живопис", r"колорит", r"\bгам", r"поліхром", r"етюд"],
 "T05": [r"кольор", r"колір", r"колірн", r"палітр"],
 "T06": [r"компон", r"композиц", r"рівновага", r"ритм"],
 "T07": [r"стилізац", r"декоративн"],
 "T08": [r"голов", r"череп", r"фігур", r"портрет", r"анатом", r"обличч", r"кист"],
 "T09": [r"начерк", r"по пам", r"по уяв", r"короткочасн", r"зарисов"],
 "T10": [r"пленер", r"пейзаж", r"урбаніст", r"ландшафтн"],
 "T11": [r"об.ємн", r"тривимірн", r"об.єм", r"конструкці", r"просторов"],
 "T12": [r"макет"],
 "T14": [r"інтер.єр", r"освітлен", r"колористик", r"світлов"],
 "T15": [r"маркер", r"графічне відображення", r"подач", r"антураж", r"поліхромі\w* у проект"],
 "T17": [r"копі", r"відомого", r"стил"],
}


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 15]


def best_sentence(text, topic):
    pats = KW.get(topic, [])
    best, score = None, 0
    for s in sentences(text):
        sc = sum(1 for p in pats if re.search(p, s, re.I))
        if sc > score:
            best, score = s, sc
    return best


def evidence_for(row, topic, value):
    src = (row.get("description", "") + " " + row.get("summary", "")).strip()
    s = best_sentence(row.get("description", ""), topic) or best_sentence(row.get("summary", ""), topic)
    if not s:
        return None
    s = s if len(s) <= 230 else s[:227].rsplit(" ", 1)[0] + "…"
    kind = "Завдання" if value == 2 else "Згадка"
    return f"{kind}: «{s}»"

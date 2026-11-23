# -*- coding: utf-8 -*-
"""Збірка хабів підстановкою даних у шаблони (без генерації HTML моделлю).

python -m ai_edu_audit.hubs.build <тека прогону>
Пише <run>/hubs/program.html (основний звіт, поглиблені лінії входять у нього) і overview.html;
окремі line_<ID>.html — лише з ключем --line-hubs.
"""
import argparse
import glob
import json
import os
import re
from collections import defaultdict

TPL = os.path.join(os.path.dirname(__file__), "templates")
AUTHOR = "Концепція та методика AI-Edu — проф. Ярослав Виклюк, НУ «Львівська політехніка», ORCID 0000-0003-4766-4659"


def _j(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def _inject(tpl_name, title, data, extra=None):
    css = open(os.path.join(TPL, "base.css"), encoding="utf-8").read()
    html = open(os.path.join(TPL, tpl_name), encoding="utf-8").read()
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("__CSS__", css).replace("__TITLE__", title).replace("__DATA__", payload)
    for k, v in (extra or {}).items():
        html = html.replace(k, v)
    return html


def common_meta(run):
    inv = _j(os.path.join(run, "inventory.json"))
    dec = _j(os.path.join(run, "decisions.json"))
    g = _j(os.path.join(run, "grounding.json"))
    rows = _jsonl(os.path.join(run, "courses.jsonl"))
    missing = [f"{r['ok']} «{r['title']}» ({r['credits']:g} кр.)" for r in rows if r["status"] == "missing"]
    s = inv["summary"]
    inv_rows = [["Файлів у теці", s["files"]], ["Силабусів", s["syllabi"]], ["ОК в ОП", s["opp_components"]],
                ["ОК з документом", s["covered"]], ["ОК без документа", s["missing"]],
                ["Вердикт", {"sufficient": "достатньо", "sufficient_with_limits": "достатньо з обмеженнями",
                             "insufficient": "недостатньо"}[inv["verdict"]]]]
    jp = os.path.join(run, "journal.json")
    journal = _j(jp)["checks"] if os.path.exists(jp) else []
    return dict(missing=missing, grounding=dict(found=g["found"], total=g["total"], share=g["share"]), journal=journal,
                guarantor=dec.get("guarantor_statement", ""), inventory=inv_rows), inv, dec, rows


def build_line(run, line_dir, meta_common, prog):
    D = _j(os.path.join(line_dir, "data.json"))
    R = _j(os.path.join(line_dir, "recs.json"))
    X = _j(os.path.join(line_dir, "details.json"))
    L = _j(os.path.join(line_dir, "line.json"))
    A = _j(os.path.join(run, "assumptions.json"))
    opp = {c["code"]: c for c in prog["courses"]}
    m = L["meta"]
    meta = dict(meta_common,
                eyebrow=f"{m['program']} · поглиблений аудит лінії",
                h1=f"Лінія {m['line_id']} «{m['line_name']}»",
                lede=f"{len(D['line'])} курсів і {len(D['cols']) - len(D['line'])} сусідні: що в силабусах, де теми повторюються, "
                     f"чого чекають роботодавці, як учать провідні школи й як зміняться метрики після правок.",
                credits=sum(opp[c]["credits"] for c in D["line"]), roles=L["demand"]["roles"],
                n_vac=sum(X.get("n", {}).values()), topic_scale=m["topic_scale"],
                footer=[f"Джерела: ОПП «{prog['name']}» 2026 (перелік ОК, компетентності, ПРН, матриці); силабуси дисциплін; "
                        f"стандарт 022 «Дизайн» (2018); {m['sources']['demand']}; {m['sources']['universities']}.",
                        "Метрики силабуса — 24 метрики AI-Edu у 7 вимірах; значення «після» — прогноз за умови впровадження правок. "
                        "Внутрішня версія: коди ОК кафедри; прізвищ авторів РП у звіті немає.", AUTHOR])
    title = f"{m['line_id']} · {m['line_name']} · аудит лінії"
    if m["line_id"] == "OP":
        meta.update(eyebrow=f"{m['institution']} · аудит освітньої програми",
                    h1=f"ОП «{prog['name']}»",
                    lede=f"{len(D['line'])} компонентів, {meta['credits']:g} кр. з обома вибірковими лініями: що в силабусах, як курси пов'язані між собою, "
                         f"чого чекають роботодавці, як учать провідні школи й як зміняться метрики після правок.")
        title = f"Аудит ОП «{prog['name']}»"
    ui_path = os.path.join(line_dir, "ui.json")
    if os.path.exists(ui_path):     # шаблон еталонного хабу (той самий CSS і взаємодії), тексти — з ui.json
        U = _j(ui_path)
        meta["K"] = None if not (L.get("pilot") or {}).get("before") else 0.67
        tpl = open(os.path.join(TPL, "hub.html"), encoding="utf-8").read()
        payload = json.dumps(dict(D=D, R=R, X=X, U=U, A=A, META=meta), ensure_ascii=False).replace("</", "<\\/")
        html = tpl.replace("__TITLE__", title).replace("__DATA__", payload).replace("__OVERVIEW_LINK__", "overview.html")
        return html, D, L
    html = _inject("line_hub.html", title, dict(D=D, R=R, X=X, A=A, META=meta), {"__OVERVIEW_LINK__": "overview.html"})
    return html, D, L


def build_overview(run, meta_common, inv, dec, rows, prog, lines_built):
    A = _j(os.path.join(run, "assumptions.json"))
    ex = _j(os.path.join(run, "express.json"))
    lines = _j(os.path.join(run, "lines.json"))
    opp = {c["code"]: c for c in prog["courses"]}
    # структура
    by_sem = defaultdict(lambda: dict(mand=0.0, el=0.0, total=0.0))
    no_sem = 0.0
    for c in prog["courses"]:
        if c["block"] == "ВБ2":
            continue                              # одна лінія вибіркових (ВБ1), щоб не рахувати двічі
        if not c["semesters"]:
            no_sem += c["credits"]
            continue
        s = c["semesters"][0]
        k = "el" if c["type"] == "вибіркова" else "mand"
        by_sem[s][k] += c["credits"]
        by_sem[s]["total"] += c["credits"]
    totals = inv["structure"]["totals"]
    # компетентності
    rp_claims = defaultdict(int)
    for r in rows:
        for code in set(r.get("comps", []) + r.get("prn", [])):
            rp_claims[code] += 1
    comp = []
    for c in prog["competences"] + prog["outcomes"]:
        if c["code"].startswith(("КОМ", "АіВ")):
            continue
        mx = prog["comp_matrix"] if c in prog["competences"] else prog["prn_matrix"]
        comp.append(dict(code=c["code"], text=c["text"][:220], opp=sum(1 for v in mx.values() if c["code"] in v),
                         rp=rp_claims.get(c["code"], 0)))
    undefined = [i["text"] for i in prog["issues"] if i["type"] in ("codes", "matrix")]
    # лінії
    olines = []
    for l in ex["lines"]:
        built = lines_built.get(l["id"])
        olines.append(dict(id=l["id"], name=l["name"], courses=l["courses"], credits=l["credits"], express=l["express_index"],
                           priority=l["priority"], light=l["light"], metrics=l["metrics"],
                           hub="program.html" if built else None,
                           index=built["prog_index"] if built else None,
                           prog=[dict(key=p["key"], name=p["name"], v=p["v"], s=p["s"]) for p in built["prog"]] if built else None))
    ctrl = [i for i in inv["issues"] if i["check"] == "consistency" and "форма контролю" in i["text"]]
    late = [l for l in ex["links"] if l["verdict"] == "late"]
    absent = [l for l in ex["links"] if l["verdict"] == "absent"]
    mand = totals.get("Разом за обов’язкові освітні компоненти") or totals.get("Разом за обов'язкові освітні компоненти")
    el = totals.get("Разом за вибіркові освітні компоненти")
    checks = [
        dict(name="Обсяг ОП у кредитах", state="ok", evidence=f"{prog['credits_total']:g} кр.: обов'язкові {mand:g} + вибіркові {el:g}"),
        dict(name="Частка вибіркових дисциплін", state="н/д",
             evidence=f"{el:g} / {prog['credits_total']:g} = {el / prog['credits_total']:.0%}; нормативне значення не звірялося з чинною редакцією в цій сесії"),
        dict(name="Реальність вибору", state="ok", evidence="дві лінії вибіркових по 13 ОК (48 кр. кожна) + 6 кр. вільного вибору"),
        dict(name="Узгодженість кредитів циклу 2.2", state="увага", evidence="«Разом за Лінію» 48 кр., цикл 2.2 — 54 кр.: 6 кр. не розподілено (припущення A6)"),
        dict(name="Рівномірність навантаження за семестрами", state="н/д", evidence="немає навчального плану; розподіл за теками — вкладка «Структура»"),
        dict(name="Практики й атестація", state="увага", evidence="програм практик (ОК2.23, ОК2.24) немає; силабуси виконання й захисту БКР збігаються на 97 %"),
        dict(name="Структурно-логічна схема", state="увага", evidence="у тексті ОПП схеми не знайдено; зв'язки взято з силабусів"),
        dict(name="Пререквізити не суперечать семестрам", state="увага",
             evidence=f"{len(late)} зв'язків «пізніше за наступний», {len(absent)} посилань на дисципліни, яких немає в ОП"),
        dict(name="Форма контролю: ОП ↔ силабуси", state="порушення", evidence=f"розбіжність у {len(ctrl)} ОК"),
        dict(name="Коди компетентностей і ПРН: перелік ↔ матриці", state="порушення",
             evidence="; ".join(undefined[:3])),
    ]
    L1 = lines_built.get("L1")
    findings = [
        dict(t="Аудит на силабусах, а не на повних РП", x="57 з 59 силабусів не мають переліку тем, жоден — розподілу годин за темами; метрики практикуму й трудомісткості не вимірні (припущення A1)."),
        dict(t="ОП і силабуси говорять різними кодами", x="Матриці ОП і силабуси використовують ФКС1.x–2.x, ПРН21–23, РНПС, яких немає в переліку компетентностей і ПРН ОП."),
        dict(t=f"Форма контролю розходиться в {len(ctrl)} ОК", x="Найчастіше «залік» у силабусі проти «диф. заліку» в ОП."),
        dict(t="Курсові проєкти — копії силабусів дисциплін", x="Силабуси КП збігаються з силабусами відповідних дисциплін на 97–100 % (4 пари), «Технології і матеріали» однакові в обох лініях."),
    ]
    if L1:
        findings.append(dict(t=f"Лінія L1 «Художня підготовка»: {L1['prog_index'][0]} → {L1['prog_index'][2]}",
                             x="Сім курсів повторюють живопис, стилізацію й тональний рисунок; простір і ручну подачу (консенсус провідних програм) майже не малюють; «скульптура» лише в назві."))
    order = [f"{l['id']} {l['name']}" + (" — поглиблено" if l["id"] in lines_built else "") for l in
             sorted([x for x in ex["lines"] if x["priority"] is not None], key=lambda x: -x["priority"])]
    O = dict(program=dict(credits=prog["credits_total"], duration=prog["duration"], n_courses=len(prog["courses"]),
                          n_covered=sum(1 for r in rows if r["status"] == "ok"), n_missing=sum(1 for r in rows if r["status"] == "missing")),
             structure=dict(mandatory=mand, elective=el, by_sem={k: {kk: round(vv, 1) for kk, vv in v.items()} for k, v in by_sem.items()},
                            no_sem=no_sem, totals=totals),
             comp=comp, undefined_codes=undefined, lines=olines, checks=checks,
             naqa="Не виконано в прототипі: зіставлення з критеріями потребує чинної редакції положення про акредитацію ОП (НАЗЯВО), відкритої в сесії. Знахідки вкладок «Відповідність нормам» і «Компетентності і ПРН» — вихідний матеріал для цього кроку.",
             roadmap=dict(order=order,
                          decisions=["Чи писати повні РП з тематичними планами (знімає припущення A1–A2)",
                                     "Узгодити коди компетентностей і ПРН у переліку, матрицях і силабусах",
                                     "Узгодити форми контролю силабусів з ОП", "Окремі силабуси курсових проєктів",
                                     "Розбиття ОП на лінії (A11) і ролі випускників (A7)"],
                          wave1=[["усі викладачі", "форма контролю як в ОП, бали = 100, коди з ОП, політика ШІ", "P2, P10, P12"],
                                 ["гарант", "навчальний план і повні РП", "A1, A2 → метрики практикуму стають вимірними"],
                                 ["гарант", "силабуси 9 відсутніх ОК", "P1"]]),
             verdict={"sufficient": "достатньо", "sufficient_with_limits": "достатньо з обмеженнями", "insufficient": "недостатньо"}[inv["verdict"]],
             findings=findings)
    meta = dict(meta_common, eyebrow=f"{prog['institution']} · {prog['specialty']['code']} «{prog['specialty']['name']}» · бакалавр · 2026",
                h1=f"Огляд ОП «{prog['name']}»",
                lede="Структура, компетентності, лінії дисциплін і відповідність нормам; поглиблений аудит обраної лінії — окремий хаб.",
                footer=[f"Джерела: ОПП «{prog['name']}» (редакція 2026); {len(rows) - sum(1 for r in rows if r['status'] == 'missing')} силабусів; стандарт 022 «Дизайн» (наказ МОН 13.12.2018 № 1391). Станом на 23.11.2026.",
                        "Внутрішня версія: коди ОК кафедри; прізвищ авторів РП у звіті немає.", AUTHOR])
    return _inject("overview_hub.html", f"Огляд ОП «{prog['name']}» · AI-Edu", dict(O=O, A=A, META=meta))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m ai_edu_audit.hubs.build")
    ap.add_argument("run_dir")
    ap.add_argument("--line-hubs", action="store_true",
                    help="також писати окремі хаби поглиблених ліній (line_<ID>.html); за замовчуванням лінія входить у хаб ОП")
    a = ap.parse_args(argv)
    run = a.run_dir
    meta_common, inv, dec, rows = common_meta(run)
    prog = _j(os.path.join(run, "program.json"))
    out_dir = os.path.join(run, "hubs")
    os.makedirs(out_dir, exist_ok=True)
    built = {}
    for ld in sorted(glob.glob(os.path.join(run, "line_*"))):
        if not os.path.exists(os.path.join(ld, "data.json")):
            continue
        html, D, L = build_line(run, ld, meta_common, prog)
        lid = L["meta"]["line_id"]
        built[lid] = D
        if a.line_hubs:
            with open(os.path.join(out_dir, f"line_{lid}.html"), "w", encoding="utf-8") as f:
                f.write(html)
    pd = os.path.join(run, "program")
    if os.path.exists(os.path.join(pd, "data.json")):
        html, D, L = build_line(run, pd, meta_common, prog)
        with open(os.path.join(out_dir, "program.html"), "w", encoding="utf-8") as f:
            f.write(html)
    with open(os.path.join(out_dir, "overview.html"), "w", encoding="utf-8") as f:
        f.write(build_overview(run, meta_common, inv, dec, rows, prog, built))
    print("хаби:", sorted(os.listdir(out_dir)))


if __name__ == "__main__":
    main()

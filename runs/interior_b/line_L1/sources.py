# -*- coding: utf-8 -*-
"""Зовнішні дані лінії L1 «Художня підготовка», зібрані в сесії 23.11.2026 (прототип: роль агентів дослідження
виконує аудитор). Кожна частка — з URL, датою і n. Вибірка вакансій — фрагменти оголошень у результатах
пошуку (сторінки work.ua / robota.ua напряму недоступні з робочого середовища), тому n малі й частки орієнтовні."""

AS_OF = "23.11.2026"

# Одиниці зовнішнього попиту, що стосуються художньої підготовки (S8–S10 — 3D, креслення, графічні
# редактори — є в більшості вакансій, але належать іншим лініям; показані в хабі як контекст).
SKILLS = [
    ("S1", "Композиція, принципи дизайну"),
    ("S2", "Колір, колористика, естетичний смак"),
    ("S3", "Ескіз, скетч, малювання від руки"),
    ("S4", "Концепції, мудборди, візуальні референси"),
    ("S5", "Портфоліо"),
    ("S6", "Креативне / творче мислення"),
    ("S7", "Просторове мислення, об'ємне формотворення"),
    ("S11", "Матеріали й фактури"),
    ("S12", "ШІ у творчому процесі"),
]
CONTEXT_SKILLS = [("S8", "3D-моделювання й візуалізація"), ("S9", "Креслення, проєктна документація (CAD)"),
                  ("S10", "Photoshop / графічна подача")]

ROLES = [dict(key="ri", name="Дизайнер інтер'єру"), dict(key="rs", name="Дизайнер просторів (виставки, події)")]

VACANCIES = [  # role, url, позначені одиниці (зі знайденого тексту вимог)
    ("ri", "https://www.work.ua/jobs/4741591/", ["S5", "S6", "S8", "S9"]),
    ("ri", "https://www.work.ua/jobs/4208566/", ["S6", "S8", "S9"]),
    ("ri", "https://work.ua/jobs/5042171/", ["S2", "S6", "S8", "S9", "S10"]),
    ("ri", "https://work.ua/jobs/6801184/", ["S8", "S9"]),
    ("ri", "https://www.work.ua/jobs/5017270/", ["S4", "S8", "S9"]),
    ("ri", "https://www.work.ua/jobs/7734438/", ["S6", "S8", "S9", "S10", "S11", "S12"]),
    ("ri", "https://www.work.ua/jobs/5639357/", ["S1", "S2", "S3", "S4", "S8", "S9"]),
    ("ri", "https://www.work.ua/jobs/3446713/", ["S6", "S8", "S9", "S11"]),
    ("ri", "https://work.ua/jobs/5370444/", ["S5", "S8", "S9", "S10"]),
    ("ri", "https://www.work.ua/jobs/5230029/", ["S9", "S10"]),
    ("ri", "https://djinni.co/jobs/772189-workplace-interior-designer/", ["S8", "S9"]),
    ("ri", "https://work.ua/jobs/8276562/", ["S8", "S11", "S12"]),
    ("rs", "https://djinni.co/jobs/856257-creative-3d-exhibition-stand-designer/", ["S4", "S6", "S8"]),
    ("rs", "https://www.work.ua/jobs/5473667/", ["S1", "S8", "S10"]),
    ("rs", "https://work.ua/jobs/6554599/", ["S4", "S8", "S10"]),
    ("rs", "https://work.ua/jobs/8298936/", ["S1", "S3", "S7", "S8", "S12"]),
]

ESCO = {  # кваліфікаційний профіль ESCO (essential/optional skills), доступ 23.11.2026
    "url": "https://ec.europa.eu/esco/api/resource/occupation?uri=http://data.europa.eu/esco/occupation/73e776fb-4d99-4031-bad4-7716f121155d",
    "occupation": "interior designer",
    "maps": {"S4": "create mood boards", "S5": "maintain an artistic portfolio; manage portfolio",
             "S1": "translate requirement concepts into visual design", "S11": "monitor textile manufacturing developments",
             "S2": "understand artistic concepts (optional)", "S6": "research new ideas"},
    "architect_url": "https://ec.europa.eu/esco/api/resource/occupation?uri=http://data.europa.eu/esco/occupation/efa81635-9125-4276-8902-9deb12170ea7",
    "architect_maps": {"S3": "create architectural sketches (optional)", "S1": "design principles; aesthetics",
                       "S11": "materials for interior design"},
}

# Провідні програми: публічні навчальні плани й описи курсів (доступ 23.11.2026)
UNIS = [
    ("Pratt Institute", "BFA Interior Design: Foundation, Language of Drawing I–II, Color Materials Lighting", "США",
     "https://catalog.pratt.edu/undergraduate/design/interior-design/interior-design-bfa"),
    ("RISD", "BFA Interior Studies: EFS Drawing / Design / Spatial Dynamics, Spatial Perception: Light & Color", "США",
     "https://risd.coursedog.com/pages/To3izKBouKgTELH6AhO1"),
    ("SCAD", "BFA Interior Design: Drawing I–II, Color: Theory and Application, Design I–II (3-D Form)", "США",
     "https://issuu.com/scad/docs/scad_2017-18_academic_catalog/206"),
    ("SVA", "BFA Interior Design: Drafting and Presentation Drawing; Drawing: Perspective, Rendering and Color Theory; Draw NYC", "США",
     "https://sva.edu/academics/undergraduate/bfa-interior-design/curriculum"),
    ("RIT", "BFA Interior Design: Drawing I, Design Drawing, Color and Lighting Theory", "США",
     "https://www.rit.edu/study/curriculum/2f63003f-5a1d-4bb7-b581-52d101753281"),
    ("MIAD", "BFA Interior Architecture & Design: Systems of Drawing; composition and color theory", "США",
     "https://www.miad.edu/academic-programs/degree-programs/interior-architecture-design/program-of-study"),
    ("Politecnico di Milano", "Laurea Design degli Interni: Laboratorio del disegno; luce, colore, materiali", "Італія",
     "https://www.polimi.it/futuri-studenti/corsi-di-laurea/design-degli-interni"),
]

# ---------- Закордонний ринок (доступ 23.11.2026) ----------
# Вибірка оголошень «дизайнер інтер'єру» з текстом вимог у результатах пошуку: Велика Британія, Німеччина, Польща, США.
VACANCIES_ABROAD = [
 ("UK", "https://www.studentjob.co.uk/vacancies/6729002-junior-interior-designer", ["S4", "S5", "S6", "S11"]),
 ("UK", "https://www.dezeenjobs.com/?p=1099403", ["S4", "S5", "S8", "S9"]),
 ("UK", "https://www.dezeenjobs.com/?p=1111759", ["S3", "S5", "S8", "S9", "S10", "S11"]),
 ("UK", "https://careers.thelight.co.uk/job/891592", ["S4", "S8", "S9", "S11"]),
 ("UK", "https://www.dezeenjobs.com/?p=1101930", ["S2", "S4", "S5", "S9", "S11"]),
 ("UK", "https://www.itjobswatch.co.uk/jv/Touched-Interiors-Ltd/Junior-Interior-Designer-Job-M1-Manchester-UK-510eex", ["S4", "S8", "S9"]),
 ("UK", "https://www.jobbird.com/uk/job/24490969-junior-interior-designer", ["S2", "S4", "S8", "S9", "S10"]),
 ("UK", "https://biid.org.uk/junior-interior-designer-1", ["S3", "S6", "S7", "S10"]),
 ("UK", "https://www.dezeenjobs.com/?p=1067509", ["S4", "S5", "S8", "S9"]),
 ("UK", "https://employmenthero.com/jobs/position/maris-interiors-llp-junior-interior-designer-u6051/", ["S4", "S10", "S11"]),
 ("DE", "https://www.make-it-in-germany.com/en/working-in-germany/job-listings/job/job-10001-1003372536-S", ["S3", "S4", "S11"]),
 ("DE", "https://www.make-it-in-germany.com/en/working-in-germany/job-listings/job/job-10001-1003589634-S", ["S2", "S4", "S11"]),
 ("DE", "https://baunetz.de/dl/3136439/apop36715-102893-241205-web.pdf", ["S3", "S8", "S10"]),
 ("PL", "https://www.pracuj.pl/praca/architekt-architektka-wnetrz-projektant-projektantka-sosnowiec,oferta,1004998615", ["S4", "S5", "S8", "S9", "S11"]),
 ("PL", "https://www.pracuj.pl/praca/architekt-projektant-wnetrz-horeca-hotele-restauracje-warszawa-nowogrodzka-18a,oferta,1004985932", ["S4", "S8", "S9", "S10"]),
 ("PL", "https://wseiz.pl/app/uploads/2023/04/W_Samodzielny-Architekt-Projektant-Wnetrz-1804.pdf", ["S3", "S5", "S6", "S8", "S9", "S10"]),
 ("PL", "https://www.pracuj.pl/praca/architekt-architektka-wnetrz-wroclaw-januszowicka-5,oferta,1004932830", ["S8", "S9"]),
 ("PL", "https://www.pracuj.pl/praca/architekt-architektka-wnetrz-projektant-projektantka-wnetrz-warszawa-koszykowa-24,oferta,1004948806", ["S2", "S4", "S11"]),
 ("US", "https://businessofhome.com/jobs/junior-interior-designer-b46dbecc-1ee2-452b-888f-deb38aefa212", ["S1", "S2", "S3", "S7", "S11"]),
 ("US", "https://aiaoregon.jobboard.io/jobs/549663379-interior-designer-at-jones-architecture", ["S3", "S5", "S8", "S9", "S10"]),
 ("US", "https://careers.nari.org/job/associate-designer/84180388/", ["S3", "S5", "S9", "S10"]),
 ("US", "https://businessofhome.com/jobs/project-manager-41bfe9d9-1822-45cb-bbce-309652ec3c11", ["S3", "S8", "S9"]),
 ("US", "https://www.mediabistro.com/jobs/2166794346-interior-designer-hybrid-working-style", ["S3", "S8"]),
 ("US", "https://jobs.workable.com/jobs/2b876212-247a-4d48-b96b-ab8d512491a7.md", ["S5", "S8", "S9"]),
]
SALARIES_ABROAD = [
 dict(country="Польща", role="projektant / architekt wnętrz", med="7 380 PLN", per="на місяць, брутто",
      lad=["6 390", "7 380", "9 300"], ladl=["25 %, PLN", "медіана", "75 %"],
      note="Медіана всієї економіки — 7 695 PLN (ГУС, квітень 2026): дизайнер інтер'єру заробляє на рівні середнього працівника.",
      src=[("https://wynagrodzenia.pl/moja-placa/ile-zarabia-architekt-wnetrz", "wynagrodzenia.pl, 2026"),
           ("https://superbiz.se.pl/wiadomosci/mediana-wynagrodzen-gus-pokazal-zarobki-polakow-aa-RkYK-eU5N-4u3C.html", "ГУС, квітень 2026")]),
 dict(country="Німеччина", role="Innenarchitekt/-in", med="4 324 €", per="на місяць, брутто",
      lad=["3 882", "4 324", "4 817"], ladl=["25 %, €", "медіана", "75 %"],
      note="≈ 52 тис. € на рік; медіана для початківців усіх професій — 46 250 € (Stepstone 2026). На Stepstone — понад 500 вакансій «Innenarchitekt».",
      src=[("https://www.gehalt.de/einkommen/suche/innenarchitektur-bachelor-of-arts", "gehalt.de (Stepstone)"),
           ("https://www.business-punk.com/?p=237677", "Stepstone Gehaltsreport 2026")]),
 dict(country="Велика Британія", role="interior designer", med="£23–45 тис.", per="на рік, брутто",
      lad=["£21k", "£26k", "£55k"], ladl=["старт", "ранній етап", "досвід 20+ р."],
      note="Діапазон — National Careers Service (на основі ONS). Оголошення junior у Лондоні — £26–34 тис.",
      src=[("https://nationalcareers.service.gov.uk/job-profiles/interior-designer", "National Careers Service"),
           ("https://www.payscale.com/research/UK/Job=Interior_Designer/Salary/d6ba003a/Early-Career", "Payscale UK, 2026")]),
 dict(country="США", role="interior designer", med="$63 490", per="на рік ($30,52 / год)",
      lad=["87 100", "+3 %", "7 800"], ladl=["робочих місць", "зростання до 2034", "вакансій на рік"],
      note="BLS: «частина ескізів може бути від руки, але більшість креслень — у CAD». Обов'язкове портфоліо; у багатьох штатах — ліцензія NCIDQ.",
      src=[("https://www.bls.gov/ooh/arts-and-design/interior-designers.htm", "BLS Occupational Outlook Handbook, травень 2024")]),
 dict(country="Віддалено", role="фриланс на Upwork", med="$15–28", per="за годину (медіанний діапазон)",
      lad=["—", "—", "—"], ladl=None,
      note="На Upwork — понад 1 000 відкритих замовлень «Interior Designer»; часто просять рендери в SketchUp і мудборди. Фрилансер у США (самозайнятий) — медіана $75 / год за Payscale.",
      src=[("https://www.upwork.com/freelance-jobs/apply/Interior-Designer-for-home_~022058965746917970302/", "Upwork"),
           ("https://www.payscale.com/research/US/Job=Interior_Designer/Hourly_Rate/4c0e6b4a/Self-Employed", "Payscale US")]),
]

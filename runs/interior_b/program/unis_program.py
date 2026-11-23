# -*- coding: utf-8 -*-
"""Етап 4: покриття тем усієї ОП у навчальних планах 7 провідних програм (судження аудитора за публічними планами).

Порядок: Pratt, RISD, SCAD, SVA, RIT, MIAD, Politecnico di Milano.
2 — окремий обов'язковий курс; 1 — частина курсу / студії або названо в описі програми; 0 — у повному плані немає;
None — немає даних (план SCAD і Politecnico відомий лише частково, тому для них частіше None, ніж 0).
Джерела (доступ 23.11.2026): каталоги Pratt, SVA, RIT, MIAD, RISD (coursedog), каталог SCAD 2016–17, опис і перелік модулів Politecnico.
"""
P, R, S, V, T, M, L = range(7)

# тема -> {індекс програми: (значення, курс)}
U = {
 "T18": {P: (1, "FDC-150 «Space, Form, Process»"), R: (1, "FOUND 1005/1006 «Spatial Dynamics»"), S: (2, "INDS 102 «Form, Space and Order»"),
         V: (1, "IDD-1050 «Design Studio I»"), T: (1, "FDTN-131/132 «3D Design I–II»"), M: (1, "FYE110 «Visual Language»"), L: (1, "Laboratorio di teorie e pratiche del progetto")},
 "T19": {P: (1, "FDC-150 «Space, Form, Process»"), R: (1, "INTAR 2301 «Introduction to Interior Studies» — масштаб"), S: (1, "INDS 102 «Form, Space and Order»")},
 "T20": {P: (1, "INT-342 «Time Culture Context»"), R: (1, "INTAR 2331 «Digital Representation and Visual Narrative»; INTAR 2355 «Interiority and Power»"),
         V: (1, "HMD-3232 «Critical Thinking for Interior Designers»"), T: (1, "INDE-222 «Design Issues»")},
 "T22": {P: (2, "FDC-140 «Visualization/Representation»"), R: (2, "INTAR 2341 «Drawing for Interior Studies»"), S: (2, "DRAW 115 «Graphics for the Built Environment»"),
         V: (2, "IDD-1010 «Drafting and Presentation Drawing»"), T: (2, "INDE-102/202 «Design Drawing I–II»"), M: (2, "FYE100 «Systems of Drawing»"), L: (2, "Laboratorio del disegno")},
 "T23": {P: (2, "INT-419 «The Working Set»"), R: (2, "INTAR 2372 «Scheme Detailing»"), V: (2, "IDD-4210 «Construction Documents»"),
         T: (2, "INDE-307 «Contract Documents»"), M: (2, "IAD425 «Details & Working Drawings»"), L: (1, "CAD-креслення інтер'єру (опис програми)")},
 "T24": {P: (1, "INT-325 «Emergent Platforms»"), R: (1, "INTAR 2331 «Digital Representation…»"), S: (1, "ELDS 225 «Electronic Design I»"),
         V: (2, "IDD-2341 «Rhino and Digital Fabrication»; IDD-3384 «Introduction to Revit»"), T: (1, "INDE-203 «Digital Graphics»"), M: (2, "IAD222/223 «IAD CAD 1–2»"), L: (1, "фізичне й віртуальне моделювання (опис програми)")},
 "T25": {P: (1, "FDC-141 «Visualization/Representation/Concept»"), R: (2, "INTAR 2331 «Digital Representation and Visual Narrative»"), S: (2, "INDS 204 «Rendering for the Interior»"),
         V: (2, "IDD-3412 «Design Visualization»"), T: (1, "INDE-203 «Digital Graphics»"), M: (2, "IAD423 «IAD CAD 3: Thesis Presentation»")},
 "T26": {P: (1, "FDC-180 «Time and Movement»"), R: (1, "INTAR 2331 — visual narrative"), V: (1, "IDD-3413 «Advanced Design Visualization»")},
 "T27": {P: (2, "INT-441 «Positioning Practice Portfolio»"), R: (1, "INTAR 2301 — презентація пропозицій"), V: (1, "IDD-1010 «Drafting and Presentation Drawing»"),
         T: (1, "INDE-412 «Interior Design Capstone II»"), M: (2, "IAD423 «Thesis Presentation»"), L: (1, "Laboratorio di Sintesi Finale")},
 "T28": {P: (1, "HAD-111/112 «Themes in Art and Culture I–II»"), R: (2, "LAEL 1017 «History of Interior Architecture I»"), S: (1, "INDS 211 «History of Interior Design»"),
         V: (2, "AHD-2210/2220 «World / Western Architecture: Art and Interior Design»"), T: (2, "INDE-345 «History of Architecture, Interiors, and Furniture I»"),
         M: (1, "ARTH151 «Intro to the Practice of Art & Design History»"), L: (1, "Storia dell'architettura")},
 "T29": {P: (2, "HAD-364 «History of Interior Design»"), R: (2, "LAEL 1027 «History of Interior Architecture II: 1850 to Present»"), S: (1, "INDS 211 «History of Interior Design»"),
         V: (2, "AHD-3370 «Influences in Contemporary Interiors»"), T: (2, "INDE-346 «History of Architecture, Interiors, and Furniture II»"),
         M: (2, "ARTH215 «History of IAD since 1850»"), L: (1, "Storia dell'arte contemporanea")},
 "T30": {P: (0, ""), R: (0, ""), V: (0, ""), T: (0, ""), M: (0, "")},
 "T31": {P: (1, "HAD-364 «History of Interior Design»"), R: (1, "LAEL 1017/1027"), S: (1, "INDS 211"), V: (1, "AHD-3370 «Influences in Contemporary Interiors»"),
         T: (1, "INDE-345/346"), M: (1, "ARTH215")},
 "T32": {P: (1, "INT-342 «Time Culture Context»"), R: (1, "INTAR 2355 «Interiority and Power»"), V: (1, "HMD-3232 «Critical Thinking for Interior Designers»"),
         T: (1, "INDE-222 «Design Issues»"), L: (2, "Laboratorio di teorie e pratiche del progetto")},
 "T33": {P: (2, "INT-405 «Design Research Strategies»"), R: (1, "INTAR 23ST «Advanced Design Studio»"), V: (2, "IDD-4010 «Design Studio VII: Thesis Preparation»"),
         T: (1, "INDE-411 «Capstone I»"), M: (2, "FYE121 «Research, Process and Connection»; IAD420 «Schematic Design»")},
 "T34": {R: (2, "INTAR 2374 «Human Factors»; INTAR 2353 «Spatial Perception»"), S: (1, "INDS 110 «Exploring People and Space»"), L: (1, "поведінка й потреби користувача (опис програми)")},
 "T35": {L: (1, "житлові простори (опис програми)")},
 "T36": {S: (1, "INDS 210 «Specialized Interior Environments»"), T: (2, "INDE-212 Hospitality, INDE-301 Office, INDE-401 Multi-Story, INDE-403 Health Care"),
         L: (1, "робочі, громадські, готельні простори (опис програми)")},
 "T37": {R: (1, "INTAR 2374 «Human Factors»"), V: (2, "IDD-1240 «Furniture and Furnishings»; IDD-3513 «Furniture Design»"), T: (1, "INDE-345 — історія меблів"), L: (1, "ергономіка (опис програми)")},
 "T38": {V: (1, "IDD-3451 «Introduction to Set Design»"), T: (1, "INDE-302 «Exhibition and Merchandising Design»"), L: (1, "retail, ristorazione, intrattenimento (опис програми)")},
 "T39": {P: (2, "INT-326 «Materials Methods Meaning»; INT-218 «Color Materials Lighting»"), R: (2, "INTAR 2315 «Building Materials»"), S: (2, "INDS 209 «Interior Materials»"),
         V: (2, "IDD-2140 «Interior Materials and Finishes»"), T: (2, "INDE-303 «Materials and Specifications»"), M: (2, "IAD224 «Materials & Specifications for Interiors»"),
         L: (2, "095246 «Materiali per il design degli interni»")},
 "T40": {P: (2, "INT-217 «Assemblies & Environments»"), R: (2, "INTAR 2318 «Building Structures and Systems»"), S: (2, "INDS 220 «Building Construction and Systems for the Interior»"),
         V: (2, "IDD-2030 «Building and Interior Systems I»"), T: (2, "INDE-304 «Building Systems»"), M: (2, "IAD322 «Building Systems 1»"), L: (2, "Scienza delle costruzioni; Tecnologia dell'architettura")},
 "T41": {P: (1, "INT-218 «Color Materials Lighting»"), R: (1, "INTAR 2318; INTAR 2353 «Light and Color»"), S: (2, "INDS 302 «Lighting for the Interior»"),
         V: (2, "IDD-2035 «Building and Interior Systems II»; HSD-3053 «Lighting Design»"), T: (2, "INDE-304 «Building Systems»"), M: (2, "IAD323 «Building Systems 2»; IAD225 «Interior Design Lighting»"),
         L: (1, "світло й комфорт середовища (опис програми)")},
 "T42": {P: (0, ""), R: (0, ""), V: (0, ""), T: (0, ""), M: (0, "")},
 "T43": {P: (0, ""), R: (0, ""), V: (0, ""), T: (0, ""), M: (0, "")},
 "T44": {P: (0, ""), R: (0, ""), V: (0, ""), T: (0, ""), M: (0, ""), L: (1, "міські інтер'єри (опис програми)")},
 "T45": {P: (0, ""), R: (0, ""), V: (1, "IDD-3451 «Introduction to Set Design»"), T: (2, "INDE-302 «Exhibition and Merchandising Design»"), M: (0, ""),
         L: (2, "allestimenti, spazi espositivi ed eventi (опис програми)")},
 "T46": {P: (0, ""), R: (0, ""), V: (0, ""), T: (0, ""), M: (0, "")},
 "T47": {P: (1, "INT-325 «Emergent Platforms»"), R: (0, ""), V: (0, ""), T: (0, ""), M: (1, "FYE151 «Digital 4D»")},
 "T48": {P: (0, ""), R: (0, ""), V: (0, ""), T: (1, "INDE-302 «Exhibition and Merchandising Design»"), M: (0, ""), L: (1, "point of sale (опис програми)")},
 "T49": {P: (1, "INT-419 «The Working Set»"), R: (1, "INTAR 2318"), V: (1, "IDD-2030/2035 «Building and Interior Systems»"), T: (1, "INDE-307 «Contract Documents»"), M: (1, "IAD422 «Building Systems 3»")},
 "T50": {R: (1, "INTAR 2374 «Human Factors»"), T: (1, "INDE-403 «Health Care Design»")},
 "T51": {R: (1, "програма Adaptive Reuse; INTAR 3351 «The Scrap Lab»"), V: (2, "HSD-3147 «Sustainable Design»"), M: (2, "IAD424 «Interiors Practice: Green Studio — Sustainability»")},
 "T52": {P: (1, "INT-325 «Emergent Platforms»")},
 "T54": {P: (1, "HMS-101A «Literary and Critical Studies I»"), R: (1, "LAS-E101 «First-Year Literature Seminar»"), V: (1, "HCD-1020 «Writing and Thinking NYC»"), M: (1, "WRTG120 «Processes of Inquiry»")},
 "T56": {P: (1, "HAD-111 «Themes in Art and Culture»"), R: (1, "HPSS-S101 «Topics in History, Philosophy, and the Social Sciences»"), M: (1, "HUMT121 «Intro to Humanities»")},
 "T57": {P: (2, "INT-441 «Positioning Practice Portfolio»"), V: (1, "IDD-4030 «Professional Practice»"), T: (2, "INDE-405 «Business Practices and Career Planning»"), M: (1, "WRTG300 «The Creative Professional in Context»")},
 "T58": {P: (1, "INT-441 «Positioning Practice Portfolio»"), V: (2, "IDD-4030 «Interior Design: Professional Practice»"), T: (2, "INDE-405 «Business Practices and Career Planning»"), M: (1, "IAD424 «Interiors Practice»")},
 "T60": {P: (2, "INT-402 «Design Studio VI — Thesis»"), R: (1, "INTAR 23ST «Advanced Design Studio»"), V: (2, "IDD-4015 «Design Studio VIII: Thesis»"),
         T: (2, "INDE-411/412 «Capstone I–II»"), M: (2, "IAD420/421 «Senior Thesis»"), L: (2, "Laboratorio di Sintesi Finale")},
}

URLS = {
 "Pratt Institute": "https://catalog.pratt.edu/undergraduate/design/interior-design/interior-design-bfa",
 "RISD": "https://risd.coursedog.com/programs/cfa6776e92151000bce67f21895c0000",
 "SCAD": "https://issuu.com/scad/docs/scad-2016-2017-academic-catalog/210",
 "SVA": "https://sva.edu/academics/undergraduate/bfa-interior-design/curriculum",
 "RIT": "https://www.rit.edu/study/curriculum/2f63003f-5a1d-4bb7-b581-52d101753281",
 "MIAD": "https://www.miad.edu/academic-programs/degree-programs/interior-architecture-design/program-of-study",
 "Politecnico di Milano": "https://www.polimi.it/formazione/corsi-di-laurea/dettaglio-corso/design-degli-interni",
}

# ---------- лінія ВБ2 «Просторовий дизайн» проти програм ландшафтного й просторового дизайну ----------
UNIS2 = [
 ("Penn State", "BLA Landscape Architecture", "США", "https://bulletins.psu.edu/undergraduate/colleges/arts-architecture/landscape-architecture-bla"),
 ("Univ. of Washington", "BLA Landscape Architecture", "США", "https://larch.be.uw.edu/wp-content/uploads/sites/88/2025/05/BLA.Sequence.Chart-2025.05-1.pdf"),
 ("UAL Camberwell", "BA Interior and Spatial Design", "Велика Британія", "https://www.arts.ac.uk/subjects/architecture-spatial-and-interior-design/undergraduate/ba-hons-interior-and-spatial-design-camberwell"),
 ("UEL", "BA Interior and Spatial Design", "Велика Британія", "https://uel.ac.uk/sites/default/files/course-specification---ba-hons-interior-and-spatial-design.pdf"),
 ("Politecnico di Milano", "LM Interior and Spatial Design", "Італія", "https://www.polimi.it/formazione/corsi-di-laurea-magistrale/dettaglio-corso/interior-and-spatial-design"),
]
U2 = {  # тема -> [(значення, курс) для кожної програми UNIS2]
 "T42": [(2, "LARCH 215 «Site Design»; LARCH 60 «Cultural History of Designed Places»"), (2, "LARCH 341 «Site Design and Planning»; LARCH 352 «History of Landscape Architecture»"), (None, ""), (0, ""), (1, "лабораторія landscape design (1 рік)")],
 "T43": [(2, "LARCH 145/245 «Ecology and Plants»; LARCH 335 «Planting Methods»; LARCH 336 «Stormwater»"), (2, "LARCH 322 «Intro to Planting Design»; LARCH 363 «Ecological Design and Planning»"), (0, ""), (0, ""), (None, "")],
 "T44": [(1, "LARCH 216/315 «Expanded Use, Scale, and Context»"), (1, "LARCH 341 «Site Design and Planning»"), (1, "громадські простори, live-проєкти в місті"), (1, "new public realms"), (None, "")],
 "T45": [(0, ""), (0, ""), (2, "exhibition design, installation, події й поп-ап"), (2, "event and exhibition design, temporary pop-up environments"), (2, "лабораторія spazi temporanei; museologia")],
 "T46": [(0, ""), (0, ""), (0, ""), (0, ""), (0, "")],
 "T47": [(0, ""), (0, ""), (1, "time-based media"), (1, "atmospheres and technologies, multi-sensorial experience"), (None, "")],
 "T48": [(0, ""), (0, ""), (None, ""), (1, "retail spaces"), (1, "museologia")],
 "T39": [(2, "LARCH 236 «Design Implementation II: Materials»"), (2, "LARCH 432 «Landscape Construction»"), (1, "workshop skills, fabrication"), (1, "1:1 prototype design and fabrication"), (None, "")],
 "T23": [(2, "LARCH 235 «Grading»; LARCH 255/256 «Digital Graphics», «GIS»"), (2, "LARCH 433 «Design Implementation»"), (1, "orthographic drawing, CAD"), (None, ""), (None, "")],
 "T51": [(1, "LARCH 336 «Stormwater»"), (2, "LARCH 363 «Ecological Design and Planning»"), (1, "climate and social justice"), (None, ""), (None, "")],
 "T58": [(2, "LARCH 386 «Professional Practice»"), (2, "LARCH 473 «Professional Practice»"), (1, "professional practice dialogues"), (None, ""), (None, "")],
}
NOTES2 = [
 "<b>Ландшафтна частина ВБ2</b> (ВБ2.2, ВБ2.3, ВБ2.10) відповідає ядру програм ландшафтної архітектури лише частково: там окремо вчать рослини й екологію, вертикальне планування (grading), водовідведення, матеріали й конструкції ландшафту та професійну практику. У нас немає вертикального планування, водовідведення й ландшафтних конструкцій.",
 "<b>Подієві й тимчасові простори</b> (ВБ2.5, ВБ2.11, ВБ2.13) — сильна сторона ВБ2: так само в центрі програм interior and spatial design у Лондоні й Мілані.",
 "<b>Меморіальних просторів</b> (ВБ2.6, ВБ2.12) немає в жодній із п'яти програм — це власний профіль ОП, обґрунтований потребою України після 2022 року; його варто зберегти й описати як конкурентну перевагу.",
 "<b>Ширина лінії:</b> ВБ2 поєднує ландшафт і подієвий дизайн, які за кордоном — окремі програми. Варто або чітко розвести дві траєкторії в межах лінії, або сфокусуватися на одній (наприклад, «простори подій, пам'яті й міста»).",
]

# -*- coding: utf-8 -*-
"""Робить параметризований шаблон хабу лінії з еталонного line1_IAD_hub.html:
той самий CSS, розмітка й взаємодії; усі специфічні для лінії 1 тексти й списки — з даних (U, META)."""
import re, sys
src = open(sys.argv[1], encoding="utf-8").read()
out = sys.argv[2]

def rep(old, new, count=1):
    global src
    if old not in src:
        raise SystemExit("NOT FOUND: " + old[:90])
    src = src.replace(old, new, count)

def rep_between(start, end, new):
    """Замінити фрагмент від start (включно) до end (не включно)."""
    global src
    i = src.index(start); j = src.index(end, i)
    src = src[:i] + new + src[j:]

# ---- шапка й футер ----
rep_between('<title>', '</title>', '<title>__TITLE__')
rep_between('<header class="top">', '<main>', '''<header class="top"><div class="wrap">
  <div class="headrow">
    <div style="display:grid;gap:8px">
      <a class="small" href="__OVERVIEW_LINK__" style="color:inherit">← Огляд ОП</a>
      <span class="eyebrow" id="hEyebrow"></span>
      <h1 id="hTitle"></h1>
      <p class="lede" id="hLede"></p>
    </div>
    <div class="tile" style="min-width:250px" id="headIdx"></div>
  </div>
  <nav class="tabs" id="tabs" aria-label="Звіти"></nav>
</div></header>

''')
rep_between('<footer><div class="wrap">', '</div></footer>', '<footer><div class="wrap" id="foot">')

# ---- дані ----
rep_between('const D = ', 'const K = 0.67', 'const DATA = __DATA__;\nconst {D, R, X, U, A, META} = DATA;\n')
rep_between('const K = 0.67', 'const $ = ', '''const K = META.K;  // частка ефекту хвилі 2 з пілоту; null — пілоту немає
const EXP = (w1, w2) => (K==null || w1==null || w2==null) ? null : w1 + K*(w2 - w1);

''')
rep('const VIEWS = [\n  ["summary","Зведення"],["passport","Паспорт корпусу"],["prereq","Пререквізити"],["topics","Матриця тем"],\n  ["market","Ринок праці"],["unis","Університети"],["metrics","Метрики до / після"],["paths","Шляхи вдосконалення"]\n];',
    'const VIEWS = U.views;')
# індекс у шапці
rep('''   <span class="small muted">зараз → хвиля 1 → хвиля 2 (повне виконання). Очікувано з урахуванням досвіду пілоту: <b class="num">${f1(exp)}</b></span>`;''',
    '''   <span class="small muted">зараз → хвиля 1 → хвиля 2 (повне виконання)${exp!=null?`. Очікувано з урахуванням досвіду пілоту: <b class="num">${f1(exp)}</b>`:`. ${esc(U.index_note||"")}`}</span>`;''')
rep('<span class="eyebrow">Індекс програмного рівня</span>', '<span class="eyebrow">${esc(U.index_label)}</span>')

# ---- зведення ----
rep('const ORDER=[["Лінія 1",["ОК41","ОК42","ОК43","ОК44","ОК45","ОК46","ОК47","ОК48","ОК49"]],["Пілот",["ОК29"]],["Пререквізити й сусіди",["ОК14","ОК19","ОК26","ОК27","ОК28","ОК32"]]];',
    'const ORDER=U.order;')
rep_between('function vSummary(){', '/* ---------- Паспорт ---------- */', r'''function vSummary(){
  const chart = scoreChart();
  return `<section class="view">
   <div class="sechead"><span class="eyebrow">Звіт 8 · для гаранта</span><h2>Зведення по лінії</h2>
   <p class="muted">${esc(U.summary_lede)}</p></div>
   <div class="grid xtiles">${U.summary_tiles.map(xtile).join("")}</div>
   <div class="card"><h3>Бали робочих програм: зараз, після хвилі 1 і після хвилі 2</h3>
     <p class="small muted">Кожен рядок — один курс (силабус). Кружок — зараз, ромб — після формальних правок, бірюзова позначка — після змістового оновлення. Фон шкали — зони інтерпретації. Клацніть рядок, щоб відкрити 24 метрики курсу.</p>
     ${chart}
     <div class="grid g2" style="margin-top:6px">${U.summary_chart_notes.map(t=>`<p class="small muted">${esc(t)}</p>`).join("")}</div></div>
   <div class="card"><h3>${esc(U.wave1_title)}</h3>
     <div class="tblwrap"><table><thead><tr><th>Хто</th><th>Що зробити</th><th>Яку метрику рухає</th></tr></thead><tbody>
     ${R.wave1.map(w=>`<tr><td class="code">${esc(w[0])}</td><td>${esc(w[1])}</td><td class="code">${esc(w[2])}</td></tr>`).join("")}
     </tbody></table></div>
     <p class="small muted">Хвиля 2 (змістова) і зміни ОП — у вкладці «Шляхи вдосконалення».</p></div>
  </section>`;
}

''')
rep('''<span class="chip bad">РП немає</span>''', '''<span class="chip bad">${esc(U.missing_label)}</span>''')

# ---- паспорт ----
rep('''    const crOk = ocr===rcr''', '''    if(rcr==null) return `<tr><td class="code">${c}</td><td>${esc(t)}</td><td class="c num">${sem??"—"}</td><td class="c num">${ocr}</td><td>${octl}</td>
     <td class="small">${esc(kind||"")}</td><td class="c"><span class="chip neu">—</span></td><td>${rctl?`<span class="chip ${rctl===octl?"ok":(octl==="диф. залік"&&rctl==="залік")?"warn":"bad"}">${rctl}</span>`:'<span class="chip neu">не визначено</span>'}</td>
     <td><span class="chip ${/немає в ОП/.test(codes||"")?"bad":"ok"}">${esc(codes||"—")}</span></td><td class="small">${iss.map(esc).join("; ")}</td></tr>`;
    const crOk = ocr===rcr''')
rep('''if(st==="missing") return `<tr><td class="code">${c}</td><td>${esc(t)}</td><td class="c num">${sem}</td>''', '''if(st==="missing") return `<tr><td class="code">${c}</td><td>${esc(t)}</td><td class="c num">${sem??"—"}</td>''')
rep('''<td colspan="4"><span class="chip bad">РП відсутня</span></td>''', '''<td colspan="4"><span class="chip bad">${esc(U.missing_label)}</span></td>''')
rep_between('''   <div class="sechead"><span class="eyebrow">Звіт 1</span><h2>Паспорт корпусу</h2>''', '''  </section>`;
}

/* ---------- Пререквізити ---------- */''', r'''   <div class="sechead"><span class="eyebrow">Звіт 1</span><h2>Паспорт корпусу</h2>
   <p class="muted">${esc(U.passport_lede)}</p></div>
   <div class="grid g4">${U.passport_tiles.map(t=>`<div class="tile"><span class="eyebrow">${esc(t.l)}</span><div class="big">${esc(t.v)}</div><span class="small muted">${esc(t.s)}</span></div>`).join("")}</div>
   <h3>${esc(U.passport_h_line)}</h3>
   <div class="tblwrap"><table><thead>${th}</thead><tbody>${line.map(row).join("")}</tbody></table></div>
   ${pre.length?`<h3>Пререквізити й сусіди</h3><div class="tblwrap"><table><thead>${th}</thead><tbody>${pre.map(row).join("")}</tbody></table></div>`:""}
   <p class="note small">${esc(U.passport_note)}</p>
''')
rep('''<th>РП</th><th class="c">Кр. РП</th><th>Контроль РП</th><th>Коди в РП</th>''', '''<th>${esc(U.doc_label)}</th><th class="c">Кр. у док.</th><th>Контроль у док.</th><th>Коди в док.</th>''')
rep('''const th = `''', '''const th = `''')

# ---- пререквізити ----
rep('''const VT={ok:["ok","коректно"],same:["warn","той самий семестр"],late:["bad","пізніший семестр"],absent:["bad","немає в ОПП 2026"]};''',
    '''const VT={ok:["ok","коректно"],same:["warn","той самий семестр"],late:["bad","пізніший семестр"],absent:["bad","немає в ОП"]};''')
rep('''Замінити на курс ОПП 2026 з кодом або прибрати. Курсу «${txt.replace(/ — .*/,"").replace(/[«»]/g,"")}» у програмі немає.''',
    '''Замінити на курс ОП з кодом або прибрати. Курсу «${txt.replace(/ — .*/,"").replace(/ \\(у РП.*\\)/,"").replace(/[«»]/g,"")}» у програмі немає.''')
rep('''  const nodes = ["ОК25","ОК8","ОК18","ОК20","ОК14","ОК19","ОК28","ОК26","ОК27","ОК29","ОК32","ОК41","ОК46","ОК23","ОК33","ОК42","ОК44","ОК43","ОК45","ОК47","ОК48","ОК49","ПБКР"];''',
    '''  const nodes = U.prereq_nodes;''')
rep('''  [["ОК42","ОК47"],["ОК47","ОК49"]].forEach(''', '''  (U.chain||[]).forEach(''')
rep('''<p class="muted">Клацніть курс або стрілку — під картою з'явиться розбір: що заявлено в РП, у якому семестрі, що не так і як виправити. Червоне число на курсі — кількість проблем. Бірюзова смуга — проєктний ланцюжок з ОПП.</p></div>''',
    '''<p class="muted">${esc(U.prereq_lede)}</p></div>''')
rep('''<span><span class="sw" style="background:var(--deep-soft);border-color:var(--deep)"></span>курс лінії 1</span><span><span class="sw" style="border:1.5px dashed var(--bad)"></span>РП відсутня</span>''',
    '''<span><span class="sw" style="background:var(--deep-soft);border-color:var(--deep)"></span>курс лінії</span><span><span class="sw" style="border:1.5px dashed var(--bad)"></span>${esc(U.missing_label)}</span>''')
rep_between('''    <div class="card"><h3>Що видно з карти</h3>''', '''   </div>
  </section>`;
}
function prDescribe(){''', r'''    <div class="card"><h3>Що видно з карти</h3>
     <ul class="clean">${U.prereq_notes.map(x=>`<li><b>${esc(x.b)}</b> ${esc(x.t)}</li>`).join("")}</ul></div>
''')
rep('''<div><div class="wavehead">Семестри за ОПП</div>''', '''<div><div class="wavehead">${esc(U.sem_source)}</div>''')
rep('''r[6]==="missing" ? `<span class="chip bad">РП відсутня</span>` : `<span class="chip ok">РП ${r[7]}</span>`;''',
    '''r[6]==="missing" ? `<span class="chip bad">${esc(U.missing_label)}</span>` : `<span class="chip ok">${esc(U.doc_label)} є</span>`;''')
rep('''<p>${r[3]} семестр · ${r[4]} кр. · ${r[5]} за ОПП</p>${r[6]==="ok"?`<p class="small muted">У РП: ${r[8]} кр., ${r[9]}, ${esc(r[10])}</p>`:""}''',
    '''<p>${r[3]??"?"} семестр · ${r[4]} кр. · ${r[5]} за ОП</p>${r[6]==="ok"?`<p class="small muted">У документі: ${r[9]||"форма контролю не визначена"}</p>`:""}''')
rep('''<div><div class="wavehead">Неточності в РП</div>''', '''<div><div class="wavehead">Неточності в документі</div>''')
rep('''  if(!prSel) prSel={t:"node",c:"ОК46"};''', '''  if(!prSel) prSel={t:"node",c:U.prereq_default};''')

# ---- матриця тем ----
rep('''title="${esc(SH(c))}: РП відсутня"''', '''title="${esc(SH(c))}: ${esc(U.missing_label)}"''')
rep('''title="${esc(SH(c))}: ${v===2?"лекція і лабораторна":"лише лекція"}"''', '''title="${esc(SH(c))}: ${v===2?esc(U.scale[2]):esc(U.scale[1])}"''')
rep('''<p class="muted">21 тема лінії × 16 курсів. Клацніть клітинку — у плаваючій панелі з'явиться, що саме про цю тему є в РП курсу (номери лекцій і лабораторних), з якими курсами вона перетинається і хто має стати власником теми. Клацніть назву теми — побачите всі курси одразу.</p></div>''',
    '''<p class="muted">${D.topics.length} тем лінії × ${D.cols.length} курсів. ${esc(U.topics_lede)}</p></div>''')
rep('''<span><span class="sw v2"></span>● є лекція і лабораторна</span><span><span class="sw v1"></span>○ є лише лекція або згадка</span>''',
    '''<span><span class="sw v2"></span>● ${esc(U.scale[2])}</span><span><span class="sw v1"></span>○ ${esc(U.scale[1])}</span>''')
rep('''<span><span class="sw vN"></span>? РП відсутня, а тема очікується</span>''', '''<span><span class="sw vN"></span>? ${esc(U.missing_label)}, а тема очікується</span>''')
rep('''<th class="grp" colspan="${pre.length}">пререквізити й сусіди</th><th class="gap"></th><th class="grp" colspan="${ln.length}">лінія 1</th>''',
    '''<th class="grp" colspan="${pre.length}">${pre.length?"сусіди":""}</th><th class="gap"></th><th class="grp" colspan="${ln.length}">${esc(U.line_label)}</th>''')
rep_between('''   <div class="grid g2">
    <div class="card"><h3>Дублювання</h3>''', '''  </section>`;
}
function tpDescribe(){''', r'''   <div class="grid g2">
    <div class="card"><h3>Дублювання</h3><ul class="clean">${U.topic_dups.map(x=>`<li><b>${esc(x.b)}</b> ${esc(x.t)}</li>`).join("")}</ul></div>
    <div class="card"><h3>Прогалини</h3><ul class="clean">${U.topic_gaps.map(x=>`<li><b>${esc(x.b)}</b> ${esc(x.t)}</li>`).join("")}</ul></div>
   </div>
''')
rep('''const lvl=v=>v===2?`<span class="chip v2c">● лекція + лабораторна</span>`:v===1?`<span class="chip v1c">○ лише лекція</span>`:v===null?`<span class="chip neu">? РП відсутня</span>`:`<span class="chip neu">теми немає</span>`;''',
    '''const lvl=v=>v===2?`<span class="chip v2c">● ${esc(U.scale[2])}</span>`:v===1?`<span class="chip v1c">○ ${esc(U.scale[1])}</span>`:v===null?`<span class="chip neu">? ${esc(U.missing_label)}</span>`:`<span class="chip neu">теми немає</span>`;''')
rep('''<p class="small">${esc(ev[c]||"У РП цієї теми немає.")}</p>''', '''<p class="small">${esc(ev[c]||"У силабусі цієї теми немає.")}</p>''')
rep('''`<p class="small">Ні в лекціях, ні в лабораторних.</p>`''', '''`<p class="small">${esc(U.gap_text)}</p>`''')
rep('''<div class="wavehead">Очікується в РП, яких немає</div>''', '''<div class="wavehead">Очікується в документах, яких немає</div>''')
rep('''<p><b>Власник теми:</b> ${owner.split(" → ").map(x=>cchip(x)).join(" → ")}</p>''', '''<p><b>Власник теми:</b> ${ownerChips(owner)}</p>''')

# ---- ринок ----
rep_between('const ROLES=[', 'function rolesHtml(){', 'const ROLES=U.roles;\nconst ownerChips=o=>(o||"").split(" → ").map(x=>/^(ОК|ВБ)\\d/.test(x.trim())?cchip(x.trim().split(" ")[0], x.trim().split(" ").slice(1).join(" ")):esc(x)).join(" → ");\n')
rep('''<p class="small muted">Медіани — чиста місячна зарплата в Україні, DOU «Зарплати дата-фахівців», зима 2026 (554 аналітики, 332 DS/DE/ML); зміна — відносно літа 2025. Junior/Middle/Senior для Data Engineer і Data Analyst — з того самого звіту; для інших ролей DOU розбивки не дає. Літо 2026: медіана аналітиків $2 225 (+$25), DS/DE/ML разом $3 275 (+$100). Старт junior на Djinni — близько $500.</p>`;}''',
    '''<p class="small muted">${esc(U.roles_note)}</p>`;}''')
rep('''<div class="tr ${r.tr[0]}">${r.tr[0]==="up"?"▲":"▼"} ${esc(r.tr[1])}</div>''', '''${r.tr?`<div class="tr ${r.tr[0]}">${r.tr[0]==="up"?"▲":"▼"} ${esc(r.tr[1])}</div>`:""}''')
rep('''`<p class="small muted">Розбивки за рівнями DOU не дає.</p>`''', '''`<p class="small muted">${esc(U.no_ladder)}</p>`''')
rep('''<td style="min-width:110px"><div class="small num">${s[2]}%</div><div class="bar"><span style="width:${s[2]}%;background:var(--after)"></span></div></td>''',
    '''<td style="min-width:110px"><div class="small num">${s[2]}%</div><div class="bar"><span style="width:${s[2]}%;background:var(--after)"></span></div></td>''')
rep_between('''   <div class="sechead"><span class="eyebrow">Звіт 4</span><h2>Ринок праці</h2>''', '''   <div class="tblwrap"><table><thead><tr><th>Навичка</th><th>Data Analyst</th><th>Data Engineer</th>''', r'''   <div class="sechead"><span class="eyebrow">Звіт 4</span><h2>${esc(U.market_title)}</h2>
   <p class="muted">${esc(U.market_lede)}</p></div>
   <h3>${esc(U.roles_title)}</h3>
   ${rolesHtml()}
   <h3>${esc(U.skills_title)}</h3>
   <div class="grid xtiles x2">${U.market_tiles.map(xtile).join("")}</div>
   <div class="panel small">${U.market_panel}</div>
   <p class="note">${esc(U.market_note)}</p>
''')
rep('''<div class="tblwrap"><table><thead><tr><th>Навичка</th><th>Data Analyst</th><th>Data Engineer</th>''',
    '''<div class="tblwrap"><table><thead><tr><th>Одиниця попиту</th><th>${esc(U.role_cols[0])}</th><th>${esc(U.role_cols[1])}</th>''')
rep_between('''   <p class="small muted">Частки вакансій: InterviewStack.io''', '''  </section>`;
}

/* ---------- Університети ---------- */''', r'''   <p class="small muted">${esc(U.market_foot)}</p>
   ${U.context_html||""}
''')

# ---- університети ----
rep_between('function uniCourse(u,t){', 'function vUnis(){', 'function uniCourse(u,t){ const m=(X.uni_map||{})[u[0]+"|"+t]; if(m) return m; const cs=X.uni_courses[u[0]]||[]; return cs.length?`${cs[0][0]} «${cs[0][1]}»`:u[1]; }\n')
rep('''<td class="c num">${n}/9</td>''', '''<td class="c num">${n}/${D.unis.length}</td>''')
rep('''cchip(c,v===2?"лекція + лаб.":"лекція")).join(""):'<span class="chip bad">немає в лінії</span>'}''', '''cchip(c,v===2?U.scale_short[2]:U.scale_short[1])).join(""):'<span class="chip bad">немає в лінії</span>'}''')
i = src.index('<div class="sechead"><span class="eyebrow">Звіт 5</span>')
j = src.index('</p></div>', i)
src = src[:i] + '<div class="sechead"><span class="eyebrow">Звіт 5</span><h2>${esc(U.unis_title)}</h2>\n   <p class="muted">${esc(U.unis_lede)}' + src[j:]
rep_between('''    <div class="card"><h3>Що показує порівняння</h3>''', '''    <div class="card"><h3>Курси порівняння</h3>''', r'''    <div class="card"><h3>Що показує порівняння</h3><ul class="clean">${U.unis_notes.map(x=>`<li>${x}</li>`).join("")}</ul></div>
''')
rep('''<p class="small muted">Оцінка за публічними силабусами станом на листопад 2026. Програму КПІ на рівні курсів у публічному доступі не знайшли.</p>''',
    '''<p class="small muted">${esc(U.unis_foot)}</p>''')
rep('''${X.uni_courses[u[0]].map(x=>`${esc(x[0])} «${esc(x[1])}»`).join("; ")}</li>`''', '''${X.uni_courses[u[0]].map(x=>`${esc(x[0])} «${esc(x[1])}»`).join("; ")}${X.uni_url&&X.uni_url[u[0]]?` · <a href="${esc(X.uni_url[u[0]])}" target="_blank" rel="noopener">план</a>`:""}</li>`''')
rep('''cchip(c,v===2?"лекція + лаб.":"лекція")).join(""):'<span class="chip bad">немає</span>'}''', '''cchip(c,v===2?U.scale_short[2]:U.scale_short[1])).join(""):'<span class="chip bad">немає</span>'}''')
rep('''<p>Власник: ${D.owner[t[0]].split(" → ").map(x=>cchip(x)).join(" → ")}</p>''', '''<p>Власник: ${ownerChips(D.owner[t[0]])}</p>''')

# ---- метрики ----
rep('let curCourse="ОК44";', 'let curCourse=U.default_course;')
rep('''<p class="muted">Два рівні. Програмний — 12 метрик лінії. Курсовий — 24 метрики РП із системи пілоту AI-Edu. Для кожної метрики три значення: зараз, після хвилі 1 (формальні правки й нові РП) і після хвилі 2 (зміст). «Очікувано» — хвиля 1 повністю плюс ${Math.round(K*100)}% ефекту хвилі 2, як вийшло в пілоті.</p></div>''',
    '''<p class="muted">${esc(U.metrics_lede)}</p></div>''')
rep('''   const fmt=v=>p.key==="P8"?f1(v):pct(v);''', '''   const fmt=v=>v==null?"н/д":p.key==="P8"?f1(v):pct(v);''')
rep('''<td class="r num">${f1(p.s[0])} → ${f1(p.s[2])}</td><td class="r num">${f1(exp)}</td></tr>`}).join("");''', '''<td class="r num">${f1(p.s[0])} → ${f1(p.s[2])}</td>${K!=null?`<td class="r num">${f1(exp)}</td>`:""}</tr>`}).join("");''')
rep('''<th class="r">Бал</th><th class="r">Очікувано</th></tr></thead>''', '''<th class="r">Бал</th>${K!=null?'<th class="r">Очікувано</th>':""}</tr></thead>''')
rep('''<td></td><td class="r num"><b>${f1(EXP(D.prog_index[1],D.prog_index[2]))}</b></td></tr>''', '''<td></td>${K!=null?`<td class="r num"><b>${f1(EXP(D.prog_index[1],D.prog_index[2]))}</b></td>`:""}</tr>''')
rep('''<h3>Курсовий рівень · 24 метрики РП</h3><p class="small muted">Оцінено 16 курсів: 9 курсів лінії, ОК29 і 6 пререквізитів. Для ОК8, ОК23 і ОК33 робочих програм у папках кафедри немає.</p>''',
    '''<h3>Курсовий рівень · 24 метрики</h3><p class="small muted">${esc(U.metrics_course_note)}</p>''')
rep('''<div class="cgrp"><span class="eyebrow">РП відсутні</span><div class="seg">${["ОК8","ОК23","ОК33"].map(c=>`<button type="button" disabled title="${esc(NM(c))}: РП немає в папках кафедри">${c} <span class="bn">${esc(SH(c))}</span></button>`).join("")}</div></div>''',
    '''${(U.metrics_missing||[]).length?`<div class="cgrp"><span class="eyebrow">${esc(U.missing_label)}</span><div class="seg">${U.metrics_missing.map(c=>`<button type="button" disabled title="${esc(NM(c))}">${c} <span class="bn">${esc(SH(c))}</span></button>`).join("")}</div></div>`:""}''')
rep('''<span class="small muted">${o?`${zoneTxt(o.final)}${o.veto?` · сирий бал ${f1(o.raw)}`:""}`:"РП відсутня"}</span>''', '''<span class="small muted">${o?`${zoneTxt(o.final)}${o.veto?` · сирий бал ${f1(o.raw)}`:""}`:esc(U.missing_label)}</span>''')
rep('''    <div class="tile"><span class="eyebrow">Очікувано</span><div class="big num">${f1(EXP(sc[1].final,sc[2].final))}</div><span class="small muted">з поправкою на досвід пілоту</span></div>''',
    '''    ${K!=null?`<div class="tile"><span class="eyebrow">Очікувано</span><div class="big num">${f1(EXP(sc[1].final,sc[2].final))}</div><span class="small muted">з поправкою на досвід пілоту</span></div>`:`<div class="tile"><span class="eyebrow">Без даних</span><div class="big num">${D.mdef.filter(m=>vals[m[0]].every(x=>x==null)).length} з 24</div><span class="small muted">метрик не обчислено — немає тематичного плану й годин</span></div>`}''')
rep('''<p><b>${c}</b> · ${esc(NM(c))}${c==="ОК29"?' <span class="chip aft">остання РП v15, 04.11.2026</span>':''}${missing?' <span class="chip bad">РП відсутня — значення проєктні</span>':""}</p>''',
    '''<p><b>${c}</b> · ${esc(NM(c))}${missing?` <span class="chip bad">${esc(U.missing_label)} — значення проєктні</span>`:""}</p>''')
rep('''  const fmtV=(code,v)=>{ if(v==null) return "—";''', '''  const fmtV=(code,v)=>{ if(v==null) return "н/д";''')
rep('''`<p class="small">Бал хвилі 1 — для РП, написаної за структурою з вкладки «Шляхи вдосконалення».</p>`''', '''`<p class="small">Бал хвилі 1 — для документа, написаного за структурою з вкладки «Шляхи вдосконалення».</p>`''')
rep('''<p class="small muted">Колір — зона бала метрики: зелений ≥ 85, жовтий 70–84, червоний < 70. Вето: підсумок не вище 75, поки хоча б одна метрика вимірів A або B у проблемній зоні.</p></div>`;''',
    '''<p class="small muted">Колір — зона бала метрики: зелений ≥ 85, жовтий 70–84, червоний < 70; сірий «н/д» — немає даних, метрика не входить у бал. Вето: підсумок не вище 75, поки хоча б одна метрика вимірів A або B у проблемній зоні.</p></div>`;''')

# ---- шляхи ----
rep('''${labs?`<div class="labs"><div><div class="colh">Лабораторні зараз</div>${p.labs_now&&p.labs_now.length?`<ol>${p.labs_now.map(x=>`<li>${esc(x)}</li>`).join("")}</ol>`:'<p class="small muted">РП відсутня</p>'}</div><div class="labarr" aria-hidden="true">→</div><div><div class="colh">Пропоновані лабораторні</div>''',
    '''${labs?`<div class="labs"><div><div class="colh">${esc(U.labs_now_label)}</div>${p.labs_now&&p.labs_now.length?`<ol>${p.labs_now.map(x=>`<li>${esc(x)}</li>`).join("")}</ol>`:`<p class="small muted">${esc(U.missing_label)}</p>`}</div><div class="labarr" aria-hidden="true">→</div><div><div class="colh">${esc(U.labs_new_label)}</div>''')
rep('''<span class="chip bad">нова РП</span>''', '''<span class="chip bad">новий документ</span>''')
rep_between('''   <div class="sechead"><span class="eyebrow">Звіт 7</span><h2>Шляхи вдосконалення</h2>''', '''   <h3>Для лінії · рішення кафедри</h3>''', r'''   <div class="sechead"><span class="eyebrow">Звіт 7</span><h2>Шляхи вдосконалення</h2>
   <p class="muted">${esc(U.paths_lede)}</p></div>
   <div class="seg"><button type="button" id="openAll">Розгорнути всі</button><button type="button" id="closeAll">Згорнути всі</button></div>
   ${U.path_groups.map(g=>grp(g[0],g[1],g[2])).join("")}
''')
rep('''<h3>Для наступного перегляду ОПП · хвиля 3</h3>''', '''<h3>Для наступного перегляду ОП · хвиля 3</h3>''')
rep('''  const first=document.querySelector('details.pc[data-c="ОК44"]'); if(first) first.open=true;''', '''  const first=document.querySelector(`details.pc[data-c="${U.default_course}"]`); if(first) first.open=true;''')

# ---- вкладка «Вхідні дані й припущення» ----
rep('''const RENDER={summary:vSummary,passport:vPassport,prereq:vPrereq,topics:vTopics,market:vMarket,unis:vUnis,metrics:vMetrics,paths:vPaths};''',
r'''function vInputs(){
  const st={ok:["ok","ok"],advisory:["warn","варто"],pending:["neu","очікує"],blocking:["bad","блокує"]};
  return `<section class="view">
   <div class="sechead"><span class="eyebrow">Звіт 9 · вхідні дані</span><h2>Вхідні дані й припущення аудитора</h2>
   <p class="muted">Аудит побудовано лише на наданих документах. Тут — чого бракувало, що аудитор прийняв замість цього, як це вплинуло на висновки і що треба надати, щоб припущення зняти.</p></div>
   <div class="tblwrap"><table><thead><tr><th>№</th><th>Чого бракує</th><th>Що прийнято замість цього</th><th>Вплив на аудит</th><th>Як зняти</th></tr></thead><tbody>
   ${A.items.map(a=>`<tr><td class="code">${esc(a.id)}</td><td>${esc(a.missing)}</td><td class="small">${esc(a.assumed)}</td><td class="small">${esc(a.impact)}</td><td class="small">${esc(a.fix)}</td></tr>`).join("")}
   </tbody></table></div>
   <div class="grid g2">
    <div class="card"><h3>Документи, яких немає · ${META.missing.length}</h3><ul class="clean">${META.missing.map(m=>`<li>${esc(m)}</li>`).join("")}</ul>
     <p class="small muted">Ці ОК враховано в структурі ОП і матрицях, але не в аналізі змісту.</p></div>
    <div class="card"><h3>Перевірка витягу</h3><p>Цитати-докази знайдено в тексті джерел: <b>${META.grounding.found} з ${META.grounding.total}</b> (${pct(META.grounding.share)}).</p>
     <p class="small muted">Рішення гаранта: «${esc(META.guarantor)}»</p></div>
   </div>
   <h3>Журнал перевірок</h3>
   <div class="tblwrap"><table><thead><tr><th>Перевірка</th><th>Результат</th><th>Стан</th></tr></thead><tbody>
   ${(META.journal||[]).map(c=>`<tr><td>${esc(c.check)}</td><td class="small">${esc(c.result)}</td><td><span class="chip ${(st[c.status]||["neu",c.status])[0]}">${(st[c.status]||["neu",c.status])[1]}</span></td></tr>`).join("")}
   </tbody></table></div>
  </section>`;
}
const RENDER={summary:vSummary,passport:vPassport,prereq:vPrereq,topics:vTopics,market:vMarket,unis:vUnis,metrics:vMetrics,paths:vPaths,inputs:vInputs};''')
rep('''headIdx(); route();''', '''document.getElementById("hEyebrow").textContent=META.eyebrow; document.getElementById("hTitle").textContent=META.h1; document.getElementById("hLede").textContent=META.lede;
document.getElementById("foot").innerHTML=META.footer.map(s=>`<span>${esc(s)}</span>`).join("");
headIdx(); route();''')
open(out, "w", encoding="utf-8").write(src)
left = [w for w in ("ОК44","ОК46","ОК29","Data Analyst","InterviewStack","ОПП 2026") if w in src]
print("ok; residual mentions:", left)

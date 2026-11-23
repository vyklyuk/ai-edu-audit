import json,sys
from collections import Counter
from ai_edu_audit.extract.links import extract_links
P=json.load(open('program.json')); inv=json.load(open('inventory.json'))
rs={json.loads(l)['ok']:json.loads(l) for l in open('courses.jsonl')}
byrel={f['rel']:f for f in inv['files']}
sem={c['code']:(min(c['semesters']) if c['semesters'] else None) for c in P['courses']}
allL=[]; secs={}
for ok,r in rs.items():
  if r['status']!='ok': continue
  t=open(byrel[r['file']]['text_file']).read()
  L,sec=extract_links(t,ok,P['courses'],sem); secs[ok]=sec
  if not L: print('EMPTY',ok,(sec or '')[:120])
  allL+=L
print(len(allL),Counter(l[4] for l in allL),Counter(l[2] for l in allL))
deg=Counter(); [deg.update([l[0],l[1]]) for l in allL]
print('isolated',[c['code'] for c in P['courses'] if deg[c['code']]==0])
json.dump(dict(links=allL, sections=secs), open('links_all.json','w'), ensure_ascii=False, indent=1)

from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
from .model import GLOSSARY,oid,org_value,slug,summary

def write_org(docs,root:Path,links):
 research=root/"research/larry-fink";index=root/"indexes/larry-fink";research.mkdir(parents=True);index.mkdir(parents=True)
 by={d["_id"]:d for d in docs};ids={k:oid(k) for k in by}
 for d in docs:
  tags=sorted({slug(str(x)) for x in [*d.get("tags",[]),d.get("dtype","record"),"generated"] if x})
  lines=[":PROPERTIES:",f":ID:       {ids[d['_id']]}",f":STARINTEL_ID: {d['_id']}",f":DATASET:  {d.get('dataset','')}",":END:",f"#+title: {d.get('title',d['_id'])}",f"#+description: {summary(d)[:300]}",f"#+status: {str(d.get('verification',{}).get('status','record')).upper()}",f"#+filetags: :{':'.join(tags)}:","","* Summary","",summary(d),"","* Typed predicates",""]
  for p in d.get("predicates",[]):
   if isinstance(p,dict):
    q={k:v for k,v in p.items() if k not in {"predicate","object"}}
    lines.append(f"- *{p.get('predicate','predicate')}*: {org_value(p.get('object'))}"+(f" — qualifiers {org_value(q)}" if q else ""))
  if not d.get("predicates"):lines.append("- No typed predicates recorded.")
  if d.get("comparison_matrix"):
   lines += ["","* Comparative feature matrix","","| Feature | Score | Assessment |","|-"]+[f"| {r.get('feature','')} | {r.get('score','')} | {r.get('assessment','').replace('|','\\vert{}')} |" for r in d["comparison_matrix"]]
  for heading,key in [("Corporatism risks","corporatism_risks"),("Counterevidence and limits","counterevidence_and_limits")]:
   if d.get(key):
    lines += ["",f"* {heading}",""]
    for item in d[key]:lines.append(f"- *{item.get('risk','Finding')}*: {item.get('mechanism','')}" if isinstance(item,dict) else f"- {item}")
  lines += ["","* Evidence and provenance",""]
  for s in d.get("sources",[]):
   if isinstance(s,dict):lines.append(f"- [[{s.get('url','')}][{s.get('publisher','Source')} — {s.get('title','Untitled')}]]"+(f" — reliability {s['reliability']}" if 'reliability' in s else ""))
  lines += ["","* Exploration links",""]+[f"- [[id:{ids[n]}][{by[n].get('title',n)}]]" for n in links.get(d["_id"],[])]
  if not links.get(d["_id"]):lines.append("- No computed neighbors.")
  lines += ["","* Raw StarIntel document","","#+begin_src json",json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True),"#+end_src","","* Footnotes and Glossary",""]+[f"[fn:{slug(k)}] {k}: {v}" for k,v in GLOSSARY.items()]
  (research/f"{slug(d['_id'])}.org").write_text("\n".join(lines)+"\n")
 grouped=defaultdict(list)
 for d in docs:grouped[d.get("dtype","record")].append(d)
 lines=[":PROPERTIES:",":ID:       starintel-index-larry-fink-exploration",":END:","#+title: Larry Fink StarIntel Exploration Index","#+description: Generated index for the canonical Larry Fink StarIntel dataset.","#+status: GENERATED","#+filetags: :starintel:index:larry-fink:generated:","","* Dataset","",f"- Documents: ={len(docs)}=","- Canonical source: =digs/larry-fink/2026-07-25-public-record-dossier/records/*.jsonl=",""]
 for dtype in sorted(grouped):lines += [f"* {dtype}",""]+[f"- [[id:{ids[d['_id']]}][{d.get('title',d['_id'])}]]" for d in sorted(grouped[dtype],key=lambda x:str(x.get('title','')))] + [""]
 lines += ["* Footnotes and Glossary",""]+[f"[fn:{slug(k)}] {k}: {v}" for k,v in GLOSSARY.items()]
 (index/"LARRY-FINK-000-exploration-index.org").write_text("\n".join(lines)+"\n")

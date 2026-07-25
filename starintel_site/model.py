from __future__ import annotations
import hashlib, json, re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
ENTITY_KEYS={"entity_id","organization","person","candidate","administration","principal","contractor","acquirer","target","seller","member","author","participants","parties","defendants","plaintiffs","buyer_group"}
GLOSSARY={
 "StarIntel":"A document-centered research system storing typed facts, claims, relations, events, evidence, confidence, and provenance.",
 "Org-roam":"An Emacs knowledge system linking Org notes through stable identifiers and backlinks.",
 "provenance":"Information showing where a claim came from and how it was verified.",
 "corporatism":"A political arrangement where organized social or economic bodies receive a recognized role in public coordination; it is not merely another word for business power.",
 "policy capture":"Public decisions repeatedly directed away from the public interest toward a specific interest group or person.",
 "fascism":"An ultranationalist authoritarian system opposed to pluralist democracy and historically associated with one-party rule, suppression, political violence, and primacy of the nation over the individual.",
 "assets under management":"Investments managed for clients, not the manager's personal property.",
}
def slug(s:str)->str:return re.sub(r"[^a-z0-9]+","-",s.lower().replace(":","-")).strip("-") or "record"
def oid(s:str)->str:return f"starintel-{slug(s)[:60]}-{hashlib.sha1(s.encode()).hexdigest()[:12]}"
def load(data:Path)->list[dict[str,Any]]:
 docs=[];seen=set()
 for path in sorted(data.glob("*.jsonl")):
  for n,line in enumerate(path.read_text().splitlines(),1):
   if not line.strip():continue
   try:d=json.loads(line)
   except json.JSONDecodeError as e:raise SystemExit(f"{path}:{n}: {e}") from e
   if not d.get("_id") or d["_id"] in seen:raise SystemExit(f"missing or duplicate _id at {path}:{n}")
   seen.add(d["_id"]);docs.append(d)
 if not docs:raise SystemExit("no JSONL records")
 return docs
def _scalars(value:Any,key:str|None=None):
 if isinstance(value,dict):
  for k,v in value.items():yield from _scalars(v,k)
 elif isinstance(value,list):
  for v in value:yield from _scalars(v,key)
 elif isinstance(value,(str,int,float,bool)):yield key,str(value)
def entities(d):
 found=set();subject=d.get("subject",{})
 if isinstance(subject,dict) and isinstance(subject.get("entity_id"),str):found.add(subject["entity_id"])
 for p in d.get("predicates",[]):
  if isinstance(p,dict):
   for k,v in _scalars(p):
    if k in ENTITY_KEYS and len(v)<180:found.add(v)
 return found
def related(docs):
 groups=defaultdict(set)
 for d in docs:
  for tag in d.get("tags",[]):groups[f"tag:{tag}"].add(d["_id"])
  for ent in entities(d):groups[f"entity:{ent}"].add(d["_id"])
 scores=defaultdict(Counter)
 for group in groups.values():
  for a in group:
   for b in group:
    if a!=b:scores[a][b]+=1
 return {k:[x for x,_ in v.most_common(12)] for k,v in scores.items()}
def summary(d):return str(d.get("summary") or d.get("bottom_line",{}).get("classification") or d.get("title") or d["_id"])
def org_value(v):
 if isinstance(v,(dict,list)):return f"={json.dumps(v,ensure_ascii=False,sort_keys=True)}="
 if v is True:return "=true="
 if v is False:return "=false="
 return str(v).replace("[","\\[").replace("]","\\]")

from __future__ import annotations
import html,json,shutil
from collections import Counter
from pathlib import Path
from .model import entities,slug,summary

def graph(docs,links):
 nodes=[];edges=[];seen=set()
 def node(i,label,kind,**extra):
  if i not in seen:seen.add(i);nodes.append({"id":i,"label":label,"kind":kind,**extra})
 for d in docs:
  node(d["_id"],d.get("title",d["_id"]),"document",dtype=d.get("dtype","record"),url=f"nodes/{slug(d['_id'])}.html",confidence=d.get("confidence"))
  for e in entities(d):node(f"entity:{e}",e.split(":",1)[-1].replace("-"," ").title(),"entity");edges.append({"source":d["_id"],"target":f"entity:{e}","type":"references"})
  for s in d.get("sources",[]):
   if isinstance(s,dict):p=str(s.get("publisher","Unknown source"));node(f"publisher:{p}",p,"publisher");edges.append({"source":d["_id"],"target":f"publisher:{p}","type":"cites"})
 pairs=set()
 for a,targets in links.items():
  for b in targets[:6]:
   pair=tuple(sorted((a,b)))
   if pair not in pairs:pairs.add(pair);edges.append({"source":a,"target":b,"type":"related"})
 return {"nodes":nodes,"edges":edges}
def shell(title,body,root=""):
 return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><link rel="stylesheet" href="{root}assets/site.css"></head><body><header><a class="brand" href="{root}index.html">STARINTEL // GPT AUTO DIG</a><nav><a href="{root}index.html">Index</a><a href="{root}graph.html">Exploration graph</a><a href="https://github.com/lost-rob0t/starintel-gpt-auto-dig">Repository</a></nav></header><main>{body}</main><footer>Generated from canonical StarIntel JSONL. Facts, allegations, estimates, and agent analysis retain separate verification labels.</footer></body></html>'''
def render(v):return f"<pre>{html.escape(json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True))}</pre>" if isinstance(v,(dict,list)) else html.escape(str(v))
def write_site(docs,site:Path,links,data:Path,assets:Path):
 (site/"assets").mkdir(parents=True);(site/"nodes").mkdir();(site/"data").mkdir();shutil.copy2(assets/"site.css",site/"assets/site.css");shutil.copy2(assets/"graph.js",site/"assets/graph.js")
 by={d["_id"]:d for d in docs};counts=Counter(d.get("dtype","record") for d in docs);analysis=by.get("starintel:analysis:larry-fink-corporatism-fascism-comparison")
 cards=[]
 for d in sorted(docs,key=lambda x:(x.get("dtype",""),x.get("title",""))):
  search=" ".join([d.get("title",""),summary(d),d.get("dtype",""),*map(str,d.get("tags",[]))]).lower()
  cards.append(f'<article class="record" data-search="{html.escape(search,quote=True)}"><div class="eyebrow">{html.escape(d.get("dtype","record"))}</div><h3><a href="nodes/{slug(d["_id"])}.html">{html.escape(d.get("title",d["_id"]))}</a></h3><p>{html.escape(summary(d))}</p><div class="tags">{" ".join(map(html.escape,map(str,d.get("tags",[]))))}</div></article>')
 stats="".join(f"<div><strong>{n}</strong><span>{html.escape(t)}</span></div>" for t,n in sorted(counts.items()));narrative=""
 if analysis:
  rows="".join(f"<tr><td>{html.escape(str(r['feature']))}</td><td>{r['score']}</td><td>{html.escape(str(r['assessment']))}</td></tr>" for r in analysis.get("comparison_matrix",[]));risks="".join(f"<li><strong>{html.escape(str(r['risk']))}:</strong> {html.escape(str(r['mechanism']))}</li>" for r in analysis.get("corporatism_risks",[]));classification=analysis.get("bottom_line",{}).get("classification","")
  narrative=f'<section class="narrative"><div class="eyebrow">Agent research // comparative political economy</div><h2>Corporatism, policy capture, and fascism: evidence matrix</h2><p>{html.escape(summary(analysis))}</p><div class="verdict"><span>Best-supported classification</span><strong>{html.escape(classification)}</strong></div><p class="warning">The 0–3 scores are transparent heuristic judgments, not statistical measurements or claims of moral equivalence.</p><div class="table-wrap"><table><thead><tr><th>Feature</th><th>Score</th><th>Assessment</th></tr></thead><tbody>{rows}</tbody></table></div><h3>Documented risks of concentrated corporatist influence</h3><ul>{risks}</ul><p><a href="nodes/{slug(analysis["_id"])}.html">Open complete analysis, limits, definitions, and sources →</a></p></section>'
 body=f'<section class="hero"><div class="eyebrow">Public-record dossier // verified through July 25, 2026</div><h1>Larry Fink exploration graph</h1><p>One canonical StarIntel dataset generates the Org-roam research tree, backlinks, evidence pages, and interactive graph. No hand-maintained duplicate dossier.</p><div class="actions"><a class="button" href="graph.html">Explore graph</a><a href="data/starintel-documents.jsonl">Download combined JSONL</a></div></section><section class="stats">{stats}</section>{narrative}<section><div class="section-head"><div><div class="eyebrow">Record browser</div><h2>StarIntel documents</h2></div><input id="search" type="search" placeholder="Search records"></div><div class="records">{"".join(cards)}</div></section><script>const q=document.querySelector("#search");q.addEventListener("input",()=>{{const v=q.value.toLowerCase();document.querySelectorAll(".record").forEach(c=>c.hidden=!c.dataset.search.includes(v));}});</script>'
 (site/"index.html").write_text(shell("Larry Fink — StarIntel Exploration",body));(site/"graph.json").write_text(json.dumps(graph(docs,links),ensure_ascii=False,indent=2))
 graph_body='<section class="graph-shell"><div class="section-head"><div><div class="eyebrow">Interactive topology</div><h1>Exploration graph</h1><p>Documents connect to entities, source publishers, and computed research neighbors.</p></div><div class="graph-controls"><input id="graph-search" type="search" placeholder="Find a node"><button id="reset">Reset</button></div></div><canvas id="graph"></canvas><aside id="inspector"><strong>Select a node</strong><p>Drag nodes and scroll to zoom.</p></aside><div class="legend"><span class="document">Document</span><span class="entity">Entity</span><span class="publisher">Publisher</span></div></section><script src="assets/graph.js"></script>'
 (site/"graph.html").write_text(shell("Exploration Graph — Larry Fink",graph_body))
 for d in docs:
  predicates="".join(f"<li><strong>{html.escape(str(p.get('predicate','predicate')))}</strong>{render(p.get('object'))}</li>" for p in d.get("predicates",[]) if isinstance(p,dict)) or "<li>No typed predicates recorded.</li>";sources="".join(f'<li><a href="{html.escape(str(s.get("url","")),quote=True)}">{html.escape(str(s.get("publisher","Source")))} — {html.escape(str(s.get("title","Untitled")))}</a></li>' for s in d.get("sources",[]) if isinstance(s,dict) and s.get("url")) or "<li>No source links recorded.</li>";neighbors="".join(f'<li><a href="{slug(n)}.html">{html.escape(by[n].get("title",n))}</a></li>' for n in links.get(d["_id"],[])) or "<li>No computed neighbors.</li>";extra=""
  if d.get("comparison_matrix"):
   rows="".join(f"<tr><td>{html.escape(str(r.get('feature','')))}</td><td>{r.get('score','')}</td><td>{html.escape(str(r.get('assessment','')))}</td></tr>" for r in d["comparison_matrix"]);extra+=f'<section><h2>Comparative feature matrix</h2><div class="table-wrap"><table><thead><tr><th>Feature</th><th>Score</th><th>Assessment</th></tr></thead><tbody>{rows}</tbody></table></div></section>'
  if d.get("counterevidence_and_limits"):extra+=f'<section><h2>Counterevidence and limits</h2><ul>{"".join(f"<li>{html.escape(str(x))}</li>" for x in d["counterevidence_and_limits"])}</ul></section>'
  page=f'<article class="node-page"><div class="eyebrow">{html.escape(d.get("dtype","record"))} // {html.escape(d.get("verification",{}).get("status","unclassified"))}</div><h1>{html.escape(d.get("title",d["_id"]))}</h1><p class="lede">{html.escape(summary(d))}</p><dl class="metadata"><dt>StarIntel ID</dt><dd>{html.escape(d["_id"])}</dd><dt>Confidence</dt><dd>{html.escape(str(d.get("confidence","not scored")))}</dd></dl><section><h2>Typed predicates</h2><ul class="predicates">{predicates}</ul></section>{extra}<section><h2>Evidence and provenance</h2><ul>{sources}</ul></section><section><h2>Exploration links</h2><ul>{neighbors}</ul></section><details><summary>Raw StarIntel document</summary><pre>{html.escape(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True))}</pre></details></article>'
  (site/"nodes"/f"{slug(d['_id'])}.html").write_text(shell(d.get("title",d["_id"]),page,"../"))
 combined="\n".join(json.dumps(d,ensure_ascii=False,separators=(",",":")) for d in docs)+"\n";(site/"data/starintel-documents.jsonl").write_text(combined);(site/".nojekyll").write_text("")

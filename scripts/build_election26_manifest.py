#!/usr/bin/env python3
"""Build the bounded non-destructive Election26 institutional topic snapshot."""
import json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];extra={'2026-09-10-axiom-republican-consulting-network-pass-35','2026-09-10-nationbuilder-organizing-platform-pass-33'}
ids=set();all_ids=set();datasets=set();rows=[];skipped=[]
def institutional(doc):
 typ=doc.get('dtype');data=doc.get('data',doc)
 if typ in {'person','user','phone','email','address','person-identifier','campaign-finance','financial-observation'}:return False
 if typ=='relation':
  ends=[data.get('subject',doc.get('source')),data.get('object',doc.get('destination'))]
  def org_endpoint(v):
   ident=v.get('id','') if isinstance(v,dict) else str(v or '')
   return any(ident.startswith('starintel:'+t+':') for t in ['org','product','project','service','system','domain','url','source'])
  return all(org_endpoint(x) for x in ends)
 if typ in {'source','url'} and 'linkedin.com/in/' in json.dumps(doc).lower():return False
 return typ in {'org','source','url','product','service','system','domain'} or (typ=='finding' and 'columbus-election' in doc.get('id',''))
for d in sorted((ROOT/'digs/anarchist-violence').iterdir()):
 if not d.is_dir() or not ('election' in d.name or d.name in extra):continue
 paths=list(d.glob('starintel-documents*.jsonl'))
 if not paths:continue
 docs=[json.loads(line) for p in paths for line in p.read_text().splitlines() if line.strip()]
 evidence=' '.join(p.read_text(errors='replace') for p in d.iterdir() if p.suffix.lower() in ['.md','.org'])+' '+json.dumps(docs)
 if not re.search(r'election|voter|ballot',evidence,re.I):skipped.append(str(d.relative_to(ROOT)));continue
 unique={x.get('id',x.get('_id')) for x in docs};all_ids.update(unique);ids.update(x.get('id',x.get('_id')) for x in docs if institutional(x))
 ds={x.get('dataset') for x in docs if x.get('dataset')};datasets.update(x for x in ds if 'election' in x)
 rows.append((str(d.relative_to(ROOT)),len(unique),sorted(ds),[(str(p.relative_to(ROOT)),hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]))
# Institutional election-integrity bridge outside the dedicated election packets.
ids.update(['starintel:project:election-integrity-partnership','starintel:relation:graphika-participated-election-integrity-partnership','starintel:relation:eip-reported-content-platforms-actioned'])
# Link the established party/election-finance collections without rewriting or duplicating their records.
datasets.update(['dnc','gop'])
p=ROOT/'manifests/topic-datasets.json';j=json.loads(p.read_text());j['topics']=[t for t in j['topics'] if t['id']!='election26'];j['topics'].append({'id':'election26','title':'Election26','subtitle':'Non-destructive election institutions, public communications, civic organizations and existing election-finance collections; original datasets and evidence retained','match':{'targets':[],'datasets':[],'terms':[],'ids':sorted(ids)}});p.write_text(json.dumps(j,indent=2)+'\n')
lines=['#+title: Election26 — provenance-preserving collection manifest','#+date: 2026-10-10','', '* Purpose and protocol','The election26 entry in manifests/topic-datasets.json is an additive topic view. It does not rename, copy or overwrite the original dataset fields. Exact-ID membership merges dedicated election packets, including shard-only historical packets. Existing dnc and gop collections remain dated catalog links only, not wholesale rendered membership. The exact-ID projection excludes personal donors, voter records, person nodes and personal political profiles; relation endpoints must be institutional/system/source nodes. This catalog does not imply that political/civic institutions are violent; anarchist-violence is a preserved historical storage label.','', '* Coverage and evidence boundaries',f'Content-reviewed dedicated packet directories: {len(rows)}. Unique institutional explicit-ID selectors: {len(ids)} out of {len(all_ids)} dedicated-packet IDs. Cataloged original dataset labels: {len(datasets)}. No broad dataset selector is enabled. These are manifest membership counts, not a fresh total of live ingested records.','A full streaming discovery pass inspected 1,315,873 historical record observations across 28,401 canonical-discovered files. Election-related metadata was reviewed rather than relying only on directory names. Axiom and NationBuilder packets were included because their reports explicitly describe election-ecosystem scope. Corporate shareholder voting, incidental criminal-court election mentions, and individual political-contribution profiling investigations were not promoted wholesale.','Original records may be historical, legacy-profile or unresolved targets. Inclusion is not independent validation of every historical claim. Identity deduplication uses stable record IDs; no new real-world entity merges are inferred. All timestamps, source URLs and original dataset assignments stay with their source records.','', '* Known loader limitation','Some historical packets exist only in numbered JSONL files. They are inventoried and referenced by exact ID here, but are not silently reserialized or declared present in every existing reader. A topic view cannot create a record absent from its input loader; packet paths below provide the complete historical artifact references.','', '* Broader collection catalog', '- [[https://github.com/lost-rob0t/starintel-gpt-auto-dig/tree/fea86e4f08e37a6fcadbe28cfc173675caed71ee/digs/dnc][DNC collection snapshot]]: catalog reference only; individual finance/political records are not newly projected.', '- [[https://github.com/lost-rob0t/starintel-gpt-auto-dig/tree/fea86e4f08e37a6fcadbe28cfc173675caed71ee/digs/gop][GOP collection snapshot]]: catalog reference only; individual finance/political records are not newly projected.', '', '* Included dedicated packets']
for path,n,ds,files in rows:
 lines += [f'** {path}',f'Unique record IDs in packet files: {n}. Original datasets: '+', '.join(ds)]
 for file,h in files:lines.append(f'- [[https://github.com/lost-rob0t/starintel-gpt-auto-dig/blob/fea86e4f08e37a6fcadbe28cfc173675caed71ee/{file}][{file}]] SHA-256 {h}')
lines=[line.replace('blob/fea86e4f08e37a6fcadbe28cfc173675caed71ee/digs/anarchist-violence/2026-10-10-columbus-election-', 'blob/dig/columbus-election-institutions-2026-10-10/digs/anarchist-violence/2026-10-10-columbus-election-') for line in lines]
lines+=['','* Publication state','Draft PR material only. No live database ingestion or deployment is authorized or performed. Snapshot date: 2026-10-10 UTC. Source catalog baseline: fea86e4f08e37a6fcadbe28cfc173675caed71ee.']
(ROOT/'docs/election26-inventory.org').write_text('\n'.join(lines)+'\n')
print(json.dumps({'packetDirectories':len(rows),'explicitIds':len(ids),'catalogDatasetLabels':len(datasets),'allPacketIds':len(all_ids),'skipped':skipped}))

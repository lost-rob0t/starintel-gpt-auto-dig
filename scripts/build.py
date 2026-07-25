#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from starintel_site.model import load,related
from starintel_site.org import write_org
from starintel_site.site import write_site
def main():
 p=argparse.ArgumentParser();p.add_argument("--data",type=Path,default=ROOT/"digs/larry-fink/2026-07-25-public-record-dossier/records");p.add_argument("--roam",type=Path,default=ROOT/"roam/generated");p.add_argument("--site",type=Path,default=ROOT/"_site");a=p.parse_args()
 for target in (a.roam,a.site):
  if target.exists():shutil.rmtree(target)
 docs=load(a.data);links=related(docs);write_org(docs,a.roam,links);write_site(docs,a.site,links,a.data,ROOT/"assets");print(json.dumps({"documents":len(docs),"roam":str(a.roam),"site":str(a.site)},indent=2))
if __name__=="__main__":main()

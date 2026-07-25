from __future__ import annotations
import json,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/"digs/larry-fink/2026-07-25-public-record-dossier/records"
class BuildTest(unittest.TestCase):
 def test_generated_graph_and_org(self):
  docs=[json.loads(line) for path in sorted(DATA.glob("*.jsonl")) for line in path.read_text().splitlines() if line];ids=[d["_id"] for d in docs]
  self.assertEqual(len(ids),len(set(ids)));self.assertIn("starintel:analysis:larry-fink-corporatism-fascism-comparison",ids)
  with tempfile.TemporaryDirectory() as tmp:
   tmp=Path(tmp);roam=tmp/"roam";site=tmp/"site";subprocess.run(["python3",str(ROOT/"scripts/build.py"),"--data",str(DATA),"--roam",str(roam),"--site",str(site)],check=True,cwd=ROOT)
   self.assertTrue((site/"index.html").exists());graph=json.loads((site/"graph.json").read_text());self.assertGreater(len(graph["nodes"]),len(docs));self.assertEqual(len(list((roam/"research/larry-fink").glob("*.org"))),len(docs));self.assertEqual(len((site/"data/starintel-documents.jsonl").read_text().splitlines()),len(docs))
if __name__=="__main__":unittest.main()

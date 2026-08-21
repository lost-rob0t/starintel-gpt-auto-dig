from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .integrity import build_corpus_seal


def _proof_verifier_script(published_root: str) -> str:
    template = r"""
const publishedRoot = "__PUBLISHED_ROOT__";
const encoder = new TextEncoder();
const leafDomain = encoder.encode("STARINTEL-EVIDENCE-LEAF-V1\0");
const nodeDomain = encoder.encode("STARINTEL-EVIDENCE-NODE-V1\0");
const concat = (...parts) => {
  const size = parts.reduce((total, part) => total + part.length, 0);
  const output = new Uint8Array(size);
  let offset = 0;
  for (const part of parts) { output.set(part, offset); offset += part.length; }
  return output;
};
const hex = bytes => [...bytes].map(value => value.toString(16).padStart(2, "0")).join("");
const unhex = value => {
  if (!/^[0-9a-f]{64}$/i.test(value)) throw new Error("invalid SHA-256 digest");
  return Uint8Array.from(value.match(/../g).map(pair => parseInt(pair, 16)));
};
const sha256 = async bytes => new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
const stable = value => {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${stable(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
};
async function verifyProof(proof) {
  if (proof.format !== "starintel-evidence-proof" || proof.format_version !== 1) throw new Error("unsupported proof format");
  if (proof.merkle_root_sha256 !== publishedRoot) throw new Error("proof is not anchored to this published seal");
  const document = JSON.parse(proof.document_canonical);
  const documentHash = hex(await sha256(encoder.encode(proof.document_canonical)));
  if (documentHash !== proof.leaf.document_sha256) throw new Error("document hash mismatch");
  for (const field of ["_id", "dataset", "dtype"]) {
    if (String(document[field] ?? "") !== String(proof.leaf[field] ?? "")) throw new Error(`${field} mismatch`);
  }
  let current = await sha256(concat(leafDomain, encoder.encode(stable(proof.leaf))));
  let index = Number(proof.leaf_index);
  let width = Number(proof.leaf_count);
  for (const step of proof.siblings) {
    const sibling = unhex(step.sha256);
    const expectedSide = index % 2 === 0 ? "right" : "left";
    if (step.side !== expectedSide) throw new Error("invalid sibling side");
    if (width % 2 === 1 && index === width - 1 && hex(sibling) !== hex(current)) throw new Error("invalid odd-tail duplication");
    current = step.side === "left"
      ? await sha256(concat(nodeDomain, sibling, current))
      : await sha256(concat(nodeDomain, current, sibling));
    index = Math.floor(index / 2);
    width = Math.floor((width + 1) / 2);
  }
  if (hex(current) !== proof.merkle_root_sha256) throw new Error("Merkle root mismatch");
  return { id: proof.leaf._id, root: hex(current) };
}
const form = document.querySelector("#proof-form");
const input = document.querySelector("#proof-file");
const result = document.querySelector("#proof-result");
form.addEventListener("submit", async event => {
  event.preventDefault();
  result.textContent = "Checking proof…";
  result.dataset.state = "working";
  try {
    const proof = JSON.parse(await input.files[0].text());
    const verified = await verifyProof(proof);
    result.textContent = `VERIFIED: ${verified.id}\n${verified.root}`;
    result.dataset.state = "ok";
  } catch (error) {
    result.textContent = `FAILED: ${error.message}`;
    result.dataset.state = "error";
  }
});
""".strip()
    return template.replace("__PUBLISHED_ROOT__", published_root)


def render_verification_page(receipt: dict[str, Any]) -> str:
    root = html.escape(str(receipt["merkle_root_sha256"]))
    leaf_count = int(receipt["leaf_count"])
    dtype_count = len(receipt.get("counts_by_dtype", {}))
    script = _proof_verifier_script(str(receipt["merkle_root_sha256"])).replace(
        "</script>", "<\\/script>"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>StarIntel Evidence Seal</title>
<style>
:root {{ color-scheme: dark; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; background: #090909; color: #f4f4f4; }}
body {{ margin: 0; }} main {{ max-width: 980px; margin: 0 auto; padding: 3rem 1.25rem 5rem; }}
a {{ color: #ffd400; }} .hero {{ border: 1px solid #ffd400; padding: 1.5rem; box-shadow: 8px 8px 0 #ffd400; margin-bottom: 2rem; }}
h1 {{ margin-top: 0; font-size: clamp(2rem, 7vw, 5rem); line-height: .95; text-transform: uppercase; }}
code, pre {{ overflow-wrap: anywhere; }} .root {{ display: block; padding: 1rem; background: #111; border-left: 5px solid #ffd400; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }}
.card {{ border: 1px solid #444; padding: 1rem; }} .card strong {{ display:block; font-size: 2rem; color:#ffd400; }}
.warning {{ border-left: 5px solid #ff4d4d; padding: 1rem; background:#1a0b0b; }}
form {{ display:grid; gap:1rem; }} button {{ background:#ffd400; color:#000; border:0; padding:.8rem 1rem; font:inherit; font-weight:800; cursor:pointer; }}
#proof-result {{ white-space:pre-wrap; min-height:3rem; padding:1rem; background:#111; }} #proof-result[data-state="ok"] {{ border-left:5px solid #35d07f; }} #proof-result[data-state="error"] {{ border-left:5px solid #ff4d4d; }}
</style>
</head>
<body><main>
<section class="hero">
<p>STARINTEL / PUBLIC VERIFICATION</p>
<h1>Evidence Seal</h1>
<p>The canonical corpus is committed to a deterministic, domain-separated SHA-256 Merkle tree. Bulk bytes are distributed as ordered compressed shards instead of being duplicated inside GitHub Pages.</p>
<code class="root">{root}</code>
</section>
<section class="grid">
<div class="card"><strong>{leaf_count:,}</strong>sealed records</div>
<div class="card"><strong>{dtype_count:,}</strong>document types</div>
<div class="card"><strong>SHA-256</strong>hash algorithm</div>
<div class="card"><strong>{int(receipt["corpus_size_bytes"]):,}</strong>canonical bytes</div>
</section>
<h2>Download and verify</h2>
<p><a href="downloads/starintel-complete-corpus.manifest.json">Canonical corpus manifest</a> · <a href="downloads/starintel-bulk-release.manifest.json">Bulk release manifest</a> · <a href="downloads/starintel-evidence-seal.json">Seal receipt</a></p>
<p>Download the ordered <code>.jsonl.gz</code> shards from the manifest, decompress them in manifest order into <code>starintel-complete-corpus.jsonl</code>, then run the verifier against that reconstructed canonical stream.</p>
<pre>python3 scripts/evidence-seal.py verify \\
  starintel-complete-corpus.jsonl \\
  _site/downloads/starintel-evidence-seal.json

python3 scripts/evidence-seal.py verify-proof proof.json \\
  --receipt _site/downloads/starintel-evidence-seal.json</pre>
<h2>Verify a record proof in this browser</h2>
<form id="proof-form"><input id="proof-file" type="file" accept="application/json,.json" required><button type="submit">Verify proof</button></form>
<pre id="proof-result">Select a proof generated by scripts/evidence-seal.py.</pre>
<h2>What this proves</h2>
<p>The seal proves that a specific canonical record was included in the published corpus and detects byte-level changes to the sealed data.</p>
<div class="warning"><strong>It does not prove a claim is true.</strong> Source quality, identity resolution, interpretation, completeness, and inference still require human review.</div>
<p><a href="index.html">← Return to Auto-Dig</a></p>
<script type="module">{script}</script>
</main></body></html>
"""


def inject_verification_link(index_path: Path, receipt: dict[str, Any]) -> None:
    if not index_path.is_file():
        raise ValueError(f"missing generated site index: {index_path}")
    marker = "data-evidence-seal"
    markup = index_path.read_text(encoding="utf-8")
    if marker in markup:
        return
    root = html.escape(str(receipt["merkle_root_sha256"]))
    card = (
        f'<section {marker}="v1" style="margin:2rem 0;padding:1.25rem;border:2px solid #ffd400">'
        '<p style="margin:0 0 .5rem;font-weight:800">CRYPTOGRAPHIC EVIDENCE SEAL</p>'
        f'<p>{int(receipt["leaf_count"]):,} published records are committed to Merkle root '
        f'<code style="overflow-wrap:anywhere">{root}</code>.</p>'
        '<a href="evidence-seal.html">Verify the corpus and record proofs →</a></section>'
    )
    if "</main>" in markup:
        markup = markup.replace("</main>", card + "</main>", 1)
    elif "</body>" in markup:
        markup = markup.replace("</body>", card + "</body>", 1)
    else:
        markup += card
    index_path.write_text(markup, encoding="utf-8")


def publish_site_seal(corpus_path: Path, site_root: Path) -> dict[str, Any]:
    receipt = build_corpus_seal(corpus_path)
    downloads = site_root / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    receipt_path = downloads / "starintel-evidence-seal.json"
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (site_root / "evidence-seal.html").write_text(
        render_verification_page(receipt), encoding="utf-8"
    )
    inject_verification_link(site_root / "index.html", receipt)
    return receipt

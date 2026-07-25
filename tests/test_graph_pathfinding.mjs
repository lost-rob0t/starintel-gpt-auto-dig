import assert from "node:assert/strict";
import { findPaths } from "../site-assets/graph-core.mjs";

const nodes = ["a", "b", "c", "d"].map((id) => ({ id }));
const edges = [
  { source: "a", target: "b", label: "founded" },
  { source: "b", target: "d", label: "member" },
  { source: "a", target: "c", label: "references" },
  { source: "c", target: "d", label: "references" },
  { source: "b", target: "c", label: "serves on" }
];

const paths = findPaths(nodes, edges, "a", "d", 5, 5);
assert.ok(paths.length >= 2, "expected alternate paths");
assert.deepEqual(paths[0].nodes, ["a", "b", "d"], "direct predicate path should rank first");
assert.ok(paths.every((path) => new Set(path.nodes).size === path.nodes.length), "paths must be simple and cycle-free");
assert.deepEqual(findPaths(nodes, edges, "a", "missing"), [], "unknown endpoints must return no paths");
console.log(`validated ${paths.length} candidate graph paths`);

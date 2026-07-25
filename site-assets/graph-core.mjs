export const TAU = Math.PI * 2;
export const URL_KEYS = [
  "layout", "type", "q", "relations", "node", "focus", "depth",
  "from", "to", "route", "scale", "panx", "pany"
];

const COLORS = {
  person: "#f59e0b", organization: "#22c55e", relation: "#38bdf8",
  event: "#a78bfa", claim: "#fb7185", analysis: "#f97316",
  concept: "#eab308", "investigation-target": "#ef4444",
  "financial-observation": "#14b8a6", education: "#60a5fa",
  employment: "#818cf8", "dataset-manifest": "#64748b",
  "research-pass": "#06b6d4", contract: "#10b981", policy: "#8b5cf6",
  source: "#64748b", entity: "#94a3b8"
};
const FALLBACK = ["#2dd4bf", "#60a5fa", "#c084fc", "#f472b6", "#fb7185", "#fbbf24", "#a3e635", "#4ade80", "#22d3ee", "#818cf8"];

export const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
export const esc = (value) => String(value).replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
})[char]);

export function hash(value) {
  let result = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    result ^= value.charCodeAt(index);
    result = Math.imul(result, 16777619);
  }
  return result >>> 0;
}

export function seeded(id, salt) {
  return (hash(`${id}:${salt}`) % 100000) / 100000;
}

export function colorFor(group, provided) {
  if (COLORS[group]) return COLORS[group];
  if (provided && provided !== COLORS.entity) return provided;
  return group === "entity" ? COLORS.entity : FALLBACK[hash(group) % FALLBACK.length];
}

export function shapeFor(group) {
  if (group === "person") return "circle";
  if (group === "organization") return "square";
  if (group === "relation") return "diamond";
  if (group === "event") return "hexagon";
  if (group === "claim" || group === "investigation-target") return "triangle";
  if (group === "research-pass" || group === "analysis") return "document";
  return "circle";
}

export function edgeKey(edge) {
  return `${edge.source}\u0000${edge.target}\u0000${edge.label || ""}`;
}

export function edgeWeight(edge, reverse = false) {
  const label = String(edge.label || "related").toLowerCase();
  let weight = 1;
  if (label === "references") weight = 2.4;
  else if (label === "documented by") weight = 1.7;
  else if (label.includes("alleg")) weight = 1.8;
  else if (label.includes("analysis")) weight = 1.5;
  else if (label === "related") weight = 1.25;
  return weight + (reverse ? 0.08 : 0);
}

export function findPaths(nodes, edges, startId, endId, limit = 5, maxDepth = 9) {
  if (!startId || !endId || startId === endId) return [];
  const known = new Set(nodes.map((node) => node.id));
  if (!known.has(startId) || !known.has(endId)) return [];
  const adjacency = new Map([...known].map((id) => [id, []]));
  edges.forEach((edge) => {
    if (!adjacency.has(edge.source) || !adjacency.has(edge.target)) return;
    adjacency.get(edge.source).push({ nodeId: edge.target, edge, reverse: false });
    adjacency.get(edge.target).push({ nodeId: edge.source, edge, reverse: true });
  });

  const queue = [{ nodes: [startId], edges: [], cost: 0 }];
  const results = [];
  const signatures = new Set();
  let expansions = 0;
  while (queue.length && results.length < limit && expansions < 12000) {
    queue.sort((a, b) => a.cost - b.cost || a.nodes.length - b.nodes.length);
    const current = queue.shift();
    const last = current.nodes.at(-1);
    if (last === endId) {
      const signature = current.nodes.join("\u0001");
      if (!signatures.has(signature)) {
        signatures.add(signature);
        results.push(current);
      }
      continue;
    }
    if (current.edges.length >= maxDepth) continue;
    (adjacency.get(last) || []).forEach((step) => {
      if (current.nodes.includes(step.nodeId)) return;
      queue.push({
        nodes: [...current.nodes, step.nodeId],
        edges: [...current.edges, { ...step.edge, reverse: step.reverse }],
        cost: current.cost + edgeWeight(step.edge, step.reverse)
      });
    });
    expansions += 1;
  }
  return results.sort((a, b) => a.edges.length - b.edges.length || a.cost - b.cost);
}

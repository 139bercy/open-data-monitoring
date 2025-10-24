export type DiffSummary = {
  added: string[];
  removed: string[];
  changed: string[];
};

function flattenObject(value: unknown, prefix = ""): Record<string, unknown> {
  if (value === null || typeof value !== "object") {
    return { [prefix || "value"]: value };
  }
  const out: Record<string, unknown> = {};
  const obj = value as Record<string, unknown>;
  for (const key of Object.keys(obj)) {
    const next = prefix ? `${prefix}.${key}` : key;
    const v = obj[key];
    if (v !== null && typeof v === "object" && !Array.isArray(v)) {
      Object.assign(out, flattenObject(v, next));
    } else {
      out[next] = v;
    }
  }
  return out;
}

export function computeDiff(base: unknown, other: unknown): DiffSummary {
  const a = flattenObject(base ?? {});
  const b = flattenObject(other ?? {});
  const added: string[] = [];
  const removed: string[] = [];
  const changed: string[] = [];
  const aKeys = new Set(Object.keys(a));
  const bKeys = new Set(Object.keys(b));
  for (const k of bKeys) {
    if (!aKeys.has(k)) {
      added.push(k);
    } else {
      const av = JSON.stringify(a[k]);
      const bv = JSON.stringify(b[k]);
      if (av !== bv) changed.push(k);
    }
  }
  for (const k of aKeys) {
    if (!bKeys.has(k)) removed.push(k);
  }
  return { added, removed, changed };
}

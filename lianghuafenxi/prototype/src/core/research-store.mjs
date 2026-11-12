let snapshot = {};
const listeners = new Set();
let notifyTimer = null;
export const getResearchSnapshot = () => snapshot;
export const subscribeResearch = (callback) => {
  listeners.add(callback);
  return () => listeners.delete(callback);
};
export function publishResearch(id, packet) {
  snapshot = { ...snapshot, [id]: { ...packet, storedAt: Date.now() } };
  if (!notifyTimer)
    notifyTimer = setTimeout(() => {
      notifyTimer = null;
      for (const f of listeners) f();
    }, 500);
}
export function invalidateResearch(ids) {
  const next = { ...snapshot };
  for (const id of ids) delete next[id];
  snapshot = next;
  for (const f of listeners) f();
}

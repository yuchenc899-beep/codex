import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import {
  getResearchSnapshot,
  subscribeResearch,
  publishResearch,
  invalidateResearch,
} from "../core/research-store.mjs";
import { loadResearchPacket } from "../core/research-packet.mjs";
type Row = Record<string, any>;
export const useResearchData = () =>
  useSyncExternalStore(
    subscribeResearch,
    getResearchSnapshot,
    getResearchSnapshot,
  ) as Record<string, Row>;
export function useResearchSync(securities: Row[], enabled: boolean) {
  const forceNext = useRef(false);
  const [visible, setVisible] = useState(!document.hidden),
    [generation, setGeneration] = useState(0),
    [status, setStatus] = useState({ done: 0, total: 0, running: false });
  const signature = securities.map((s) => s.id + ":" + s.type).join(",");
  useEffect(() => {
    const update = () => setVisible(!document.hidden);
    document.addEventListener("visibilitychange", update);
    return () => document.removeEventListener("visibilitychange", update);
  }, []);
  useEffect(() => {
    if (!enabled || !visible) return;
    const timer = setInterval(() => setGeneration(n => n + 1), 300000);
    return () => clearInterval(timer);
  }, [enabled, visible]);
  useEffect(() => {
    if (!enabled || !visible) {
      setStatus((old) => ({ ...old, running: false }));
      return;
    }
    const controller = new AbortController();
    const force = forceNext.current;
    forceNext.current = false;
    const asOf = new Date().toLocaleDateString("en-CA", {
      timeZone: "Asia/Shanghai",
    });
    const cache = getResearchSnapshot() as Record<string, Row>;
    const pending = securities.filter(
      (s) =>
        force ||
        !cache[s.id] ||
        Date.now() - cache[s.id].storedAt >= 300000 ||
        new Date(cache[s.id].asOf).toLocaleDateString("en-CA", {
          timeZone: "Asia/Shanghai",
        }) !== asOf,
    );
    let lastStatus = 0;
    let cursor = 0,
      done = securities.length - pending.length;
    setStatus({ done, total: securities.length, running: pending.length > 0 });
    const request = async (
      path: string,
      { signal }: { signal: AbortSignal },
    ) => {
      const r = await fetch("/api/v1/" + path, {
        cache: force ? 'reload' : 'default',
        signal: AbortSignal.any([signal, AbortSignal.timeout(15000)]),
      });
      const body = await r.json();
      if (!r.ok) throw Error(body.error?.message || "资料源暂不可用");
      return body.data;
    };
    const worker = async () => {
      while (!controller.signal.aborted && cursor < pending.length) {
        const s = pending[cursor++];
        try {
          const packet = await loadResearchPacket(s, {
            request,
            asOf,
            signal: controller.signal,
          });
          if (controller.signal.aborted) return;
          if (packet) publishResearch(s.id, packet);
        } catch (e: any) {
          if (controller.signal.aborted) return;
          publishResearch(s.id, {
            bars: [],
            reports: [],
            errors: [e.message],
            asOf: new Date().toISOString(),
          });
        }
        done++;
        if (
          !controller.signal.aborted &&
          (Date.now() - lastStatus >= 1000 || done === securities.length)
        ) {
          lastStatus = Date.now();
          setStatus({
            done,
            total: securities.length,
            running: done < securities.length,
          });
        }
      }
    };
    Promise.all([worker(), worker()]).then(() => {
      if (!controller.signal.aborted)
        setStatus({ done, total: securities.length, running: false });
    });
    return () => controller.abort();
  }, [signature, enabled, visible, generation]);
  return {
    ...status,
    reload: () => {
      forceNext.current = true;
      invalidateResearch(securities.map((s) => s.id));
      setGeneration((n) => n + 1);
    },
  };
}

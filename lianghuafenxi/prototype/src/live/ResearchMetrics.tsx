import { useEffect, useRef, useState } from "react";
import { echarts } from "../charts";
import { annualProfitSeries } from "../core/detail.mjs";
type Row = Record<string, any>;
const n = (v: any, d = 2) =>
  v == null || !Number.isFinite(Number(v))
    ? "—"
    : Number(v).toLocaleString("zh-CN", {
        maximumFractionDigits: d,
        minimumFractionDigits: d,
      });
const large = (v: any, currency: string) =>
  v == null
    ? "—"
    : Math.abs(v) >= 1e8
      ? `${n(v / 1e8)} 亿${currency === "HKD" ? "港元" : currency === "USD" ? "美元" : "元"}`
      : `${n(v)} ${currency === "HKD" ? "港元" : currency === "USD" ? "美元" : "元"}`;
export function ValuationMetrics({
  security,
  paused,
  interval,
}: {
  security: Row;
  paused: boolean;
  interval: number;
}) {
  const [metrics, setMetrics] = useState<Row | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    let ended = false,
      timer: ReturnType<typeof setTimeout>;
    const abort = new AbortController();
    const load = async () => {
      if (ended) return;
      if (document.hidden || paused) {
        timer = setTimeout(load, 1000);
        return;
      }
      try {
        const r = await fetch(
          "/api/v1/valuation/" + encodeURIComponent(security.id),
          {
            signal: AbortSignal.any([abort.signal, AbortSignal.timeout(12000)]),
          },
        );
        const p = await r.json();
        if (!r.ok) throw Error(p.error?.message || "指标源暂不可用");
        if (!ended) {
          setMetrics(p.data);
          setError("");
        }
      } catch (e: any) {
        if (!ended && e.name !== "AbortError") setError(e.message);
      } finally {
        if (!ended) timer = setTimeout(load, Math.max(5, interval || 5) * 1000);
      }
    };
    load();
    return () => {
      ended = true;
      clearTimeout(timer);
      abort.abort();
    };
  }, [security.id, paused, interval]);
  const m = metrics,
    currency = security.currency;
  const corporate = security.type === "stock";
  return (
    <section className="live-panel">
      <h2>当前估值与当日成交</h2>
      <p>
        估值表示当前市场交易倍数，不等于目标价。动态、静态与TTM分开；公司估值不适用于ETF和指数。
      </p>
      {error && (
        <p role="status">
          {error}。
          {m ? "保留上次指标，请核对下方源时间。" : "暂不填充替代数值。"}
        </p>
      )}
      {paused && <p>行情已暂停，此处保留上次取得的快照。</p>}
      {m?.warning && <p role="status">{m.warning}</p>}
      <div className="live-metrics valuation-grid">
        {[
          [
            "市盈率 PE(TTM)",
            corporate
              ? m?.peTTM == null
                ? "—"
                : `${n(m.peTTM)} 倍`
              : "不适用",
          ],
          [
            "市盈率 PE(动态)",
            corporate
              ? m?.peDynamic == null
                ? "—"
                : `${n(m.peDynamic)} 倍`
              : "不适用",
          ],
          [
            "市盈率 PE(静态)",
            corporate
              ? m?.peStatic == null
                ? "—"
                : `${n(m.peStatic)} 倍`
              : "不适用",
          ],
          [
            "市净率 PB",
            corporate ? (m?.pb == null ? "—" : `${n(m.pb)} 倍`) : "不适用",
          ],
          ...(corporate && m?.peSource != null ? [["来源PE（口径未区分）", `${n(m.peSource)} 倍`]] : []),
          ["总市值", corporate ? large(m?.totalMarketCap, currency) : "不适用"],
          [
            "流通市值",
            corporate ? large(m?.floatMarketCap, currency) : "不适用",
          ],
          [
            "当日成交量",
            m?.volume == null ? "—" : `${n(m.volume, 0)} ${m.volumeUnit}`,
          ],
          ["当日成交额", large(m?.amount, currency)],
          ["换手率", m?.turnover == null ? "—" : `${n(m.turnover)}%`],
          ["量比", m?.volumeRatio == null ? "—" : n(m.volumeRatio)],
          ["振幅", m?.amplitude == null ? "—" : `${n(m.amplitude)}%`],
          [
            "指标对应价格",
            n(
              m?.last,
              m?.priceDigits ??
                (security.currency === "HKD" || security.type === "etf"
                  ? 3
                  : 2),
            ),
          ],
        ].map(([label, value]) => (
          <div className="live-panel" key={label}>
            <small>{label}</small>
            <h3>{value}</h3>
          </div>
        ))}
      </div>
      <p className="source">
        {m?.provider || "东方财富个股详情"} · 源时间{" "}
        {m?.sourceTime
          ? new Date(m.sourceTime).toLocaleString("zh-CN")
          : "未取得/待核实"}{" "}
        · 接收时间{" "}
        {m?.receivedAt
          ? new Date(m.receivedAt).toLocaleTimeString("zh-CN")
          : "—"}
      </p>
      <p>
        {m?.unitNote || "成交量按各市场来源单位显示，未取得时留空。"}{" "}
        非正PE可能对应亏损，不按低估处理；估值历史分位与股息率尚未接入，不凭当前PE推断历史便宜程度。
      </p>
    </section>
  );
}
export function AnnualProfitChart({
  reports,
  type,
}: {
  reports: Row[];
  type: string;
}) {
  const host = useRef<HTMLDivElement>(null),
    data = annualProfitSeries(reports);
  const signature = JSON.stringify(data);
  useEffect(() => {
    if (!host.current || type !== "stock") return;
    const c = echarts.init(host.current, "yuchen");
    c.setOption({
      animation: false,
      tooltip: {
        trigger: "axis",
        valueFormatter: (v: any) =>
          v == null ? "缺失" : `${n(v)} ${data.unit}`,
      },
      grid: { left: 65, right: 22, top: 38, bottom: 35 },
      xAxis: { type: "category", data: data.rows.map((r) => `${r.year}年`) },
      yAxis: {
        type: "value",
        name: data.unit,
        axisLine: { show: true, lineStyle: { color: "#535b67" } },
      },
      series: [
        {
          type: "bar",
          barMaxWidth: 65,
          label: {
            show: true,
            position: "top",
            color: "#bfc8d5",
            formatter: (p: any) => (p.value == null ? "" : n(p.value)),
          },
          data: data.rows.map((r) => ({
            value: r.value,
            itemStyle: {
              color: r.value != null && r.value < 0 ? "#86b5e0" : "#e0a0a0",
              borderRadius:
                r.value != null && r.value < 0 ? [0, 0, 4, 4] : [4, 4, 0, 0],
            },
          })),
        },
      ],
    });
    const resize = new ResizeObserver(() => c.resize());
    resize.observe(host.current);
    return () => {
      resize.disconnect();
      c.dispose();
    };
  }, [signature, type]);
  if (type !== "stock") return <p>ETF与指数不适用公司归母净利润柱图。</p>;
  return (
    <>
      <div
        ref={host}
        className="profit-chart"
        role="img"
        aria-label="近五个完整财年归母净利润柱状图"
      />
      <div className="profit-year-grid">
        {data.rows.map((r) => (
          <div key={r.year}>
            <small>{r.year}年</small>
            <strong>
              {r.value == null
                ? r.status === "currency_mismatch"
                  ? "币种不一致"
                  : "缺失"
                : r.value === 0
                  ? "0（零利润）"
                  : `${n(r.value)} ${data.unit}`}
            </strong>
            <small>
              同比 {r.yoy == null ? "—（缺失或基期非正）" : `${n(r.yoy)}%`}
            </small>
          </div>
        ))}
      </div>
      <p>
        口径：完整财年归属于母公司股东的净利润，保留五个年度槽位。缺失不补零，零利润与亏损分别显示；不同币种不混画。同比仅在上年净利润为正且资料齐全时计算。
      </p>
    </>
  );
}

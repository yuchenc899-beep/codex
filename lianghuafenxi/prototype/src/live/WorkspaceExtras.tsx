import { useEffect, useRef, useState } from "react";
import Decimal from "decimal.js";
import { echarts } from "../charts";
import { comparePrices } from "../core/research.mjs";
import { priceMetrics, annualSummary } from "../core/engine.mjs";
import { researchAssessment } from "../core/research.mjs";
import { useResearchData } from "./useResearchData";
import { FilterBar, defaultFilters, SortHead } from "./SecurityTables";
import {
  buildSecurityRow,
  filterSecurities,
  sortRows,
} from "../core/table-query.mjs";
type Row = Record<string, any>;
export function BatchAnalysis({
  book,
  quotes,
  open,
  refreshData,
  syncing,
}: {
  book: Row;
  quotes: Record<string, Row>;
  open: (id: string) => void;
  refreshData: () => void;
  syncing: boolean;
}) {
  const packets = useResearchData(),
    [filters, setFilters] = useState<Row>(defaultFilters),
    [order, setOrder] = useState({ key: "distanceLow", direction: "asc" });
  const base = book.securities
    .filter((s: Row) => book.watch.some((w: Row) => w.id === s.id))
    .map((s: Row) => {
      const row = buildSecurityRow(
        s,
        quotes[s.id],
        packets[s.id],
        filters.window,
      );
      const assessment = researchAssessment({
        enabled: book.settings.rulesEnabled === true,
        security: s,
        metrics: row.metrics,
        price: row.price,
        annual: row.annual,
        historyErrors: packets[s.id]?.errors || [],
      });
      return { ...row, assessment, researchLabel: assessment.label };
    });
  const rows = sortRows(
    filterSecurities(base, filters),
    order.key,
    order.direction,
  );
  const columns = [
    ["name", "证券"],
    ["industry", "行业"],
    ["price", "现价"],
    ["historyLow", "区间最低价"],
    ["distanceLow", "距低点%"],
    ["position", "区间位置%"],
    ["profitPositiveYears", "五年盈利"],
    ["profit", "最新财年归母利润"],
    ["researchLabel", "研究标签"],
    ["dataState", "资料状态"],
  ];
  const n = (v: any) =>
    v == null
      ? "—"
      : Number(v).toLocaleString("zh-CN", { maximumFractionDigits: 2 });
  return (
    <section className="live-panel">
      <h2>自选总体分析 · 历史区位与研究分流</h2>
      <FilterBar
        value={filters}
        onChange={setFilters}
        rows={base}
        label="总体分析"
      />
      <div className="live-actions wrap">
        <button
          className="button primary"
          onClick={refreshData}
          disabled={syncing}
        >
          {syncing ? "正在补齐资料…" : "更新全部自选资料"}
        </button>
        <span>
          显示 {rows.length}/{base.length} 只；已取得历史{" "}
          {base.filter((r: Row) => r.historyRows > 0).length} 只；五年财报齐备{" "}
          {
            base.filter((r: Row) => r.type === "stock" && r.profitMissing === 0)
              .length
          }
          /{base.filter((r: Row) => r.type === "stock").length} 只适用股票。
        </span>
      </div>
      <div className="table-scroll security-table">
        <table>
          <SortHead
            columns={columns}
            order={order}
            change={(key) =>
              setOrder((old) => ({
                key,
                direction:
                  old.key === key && old.direction === "asc" ? "desc" : "asc",
              }))
            }
          />
          <tbody>
            {rows.map((r: Row) => (
              <tr key={r.id}>
                <td>
                  <button className="text-button" onClick={() => open(r.id)}>
                    {r.name}
                  </button>
                  <small>
                    {r.code} · {r.currency}
                  </small>
                </td>
                <td>{r.industry}</td>
                <td>{n(r.price)}</td>
                <td>
                  {n(r.historyLow)}
                  <small>{r.historyLowDate || "—"}</small>
                </td>
                <td>
                  {n(r.distanceLow)}
                  {r.distanceLow != null ? "%" : ""}
                  <small>
                    {r.distanceLow != null && r.distanceLow < 0
                      ? "低于已取得区间低点"
                      : r.historyRows
                        ? `${r.historyRows}根日线`
                        : "待取得历史"}
                  </small>
                </td>
                <td>
                  {n(r.position)}
                  {r.position != null ? "%" : ""}
                </td>
                <td>
                  {r.type === "stock"
                    ? r.profitPositiveYears == null
                      ? "待取得"
                      : `${r.profitPositiveYears}/5`
                    : "不适用"}
                </td>
                <td>
                  {n(r.profit)}
                  <small>
                    {r.profitYear}FY · {r.profitCurrency || "币种待核实"}
                  </small>
                </td>
                <td>
                  {r.researchLabel}
                  <small>
                    {[...r.assessment.reasons, ...r.assessment.missing].join(
                      "；",
                    )}
                  </small>
                </td>
                <td>{r.dataState}</td>
                <td>
                  <button className="text-button" onClick={() => open(r.id)}>
                    研究
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
export function Comparison({ security, bars }: { security: Row; bars: Row[] }) {
  const [benchmark, setBenchmark] = useState(""),
    [other, setOther] = useState<Row[]>([]),
    [error, setError] = useState("");
  const host = useRef<HTMLDivElement>(null);
  const start = bars[0]?.date,
    end = bars.at(-1)?.date;
  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();
    setOther([]);
    setError("");
    if (!benchmark || !start || !end) return;
    (async () => {
      let cursor = start;
      const rows: Row[] = [];
      try {
        while (cursor <= end) {
          const next = new Date(cursor + "T00:00:00Z");
          next.setUTCDate(next.getUTCDate() + 364);
          const to =
            next.toISOString().slice(0, 10) > end
              ? end
              : next.toISOString().slice(0, 10);
          const r = await fetch(
            `/api/v1/history/${encodeURIComponent(benchmark)}?interval=1d&from=${cursor}&to=${to}`,
            {
              signal: AbortSignal.any([
                controller.signal,
                AbortSignal.timeout(15000),
              ]),
            },
          );
          const p = await r.json();
          if (!r.ok) throw Error(p.error?.message || "基准数据不可用");
          rows.push(...p.data.bars);
          next.setUTCDate(next.getUTCDate() + 1);
          cursor = next.toISOString().slice(0, 10);
          if (cancelled) return;
        }
        if (!cancelled)
          setOther([...new Map(rows.map((b) => [b.date, b])).values()]);
      } catch (e: any) {
        if (!cancelled) setError(e.message);
      }
    })();
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [benchmark, start, end]);
  const data = comparePrices(bars, other);
  useEffect(() => {
    if (!host.current || !data.dates.length) return;
    const c = echarts.init(host.current, "yuchen");
    c.setOption({
      animation: false,
      tooltip: { trigger: "axis" },
      legend: { data: [security.name, "比较基准"] },
      grid: { left: 55, right: 20, top: 45, bottom: 35 },
      xAxis: { type: "category", data: data.dates },
      yAxis: { type: "value", axisLabel: { formatter: "{value}%" } },
      series: [
        {
          name: security.name,
          type: "line",
          showSymbol: false,
          data: data.subject,
        },
        {
          name: "比较基准",
          type: "line",
          showSymbol: false,
          data: data.benchmark,
        },
      ],
    });
    const resize = new ResizeObserver(() => c.resize());
    resize.observe(host.current);
    return () => {
      resize.disconnect();
      c.dispose();
    };
  }, [bars, other, security.name]);
  return (
    <section className="live-panel">
      <h2>相对基准 · 价格收益比较</h2>
      <select
        aria-label="比较基准"
        value={benchmark}
        onChange={(e) => setBenchmark(e.target.value)}
      >
        <option value="">选择比较基准</option>
        {[
          ["INDEX:SH000300", "沪深300"],
          ["INDEX:SH000001", "上证指数"],
          ["INDEX:HSI", "恒生指数"],
          ["INDEX:HSTECH", "恒生科技"],
        ].map(([k, v]) => (
          <option key={k} value={k}>
            {v}
          </option>
        ))}
      </select>
      {error && <p role="alert">{error}</p>}
      {data.dates.length ? (
        <div
          ref={host}
          className="live-chart"
          role="img"
          aria-label="同区间真实价格收益比较图"
        />
      ) : (
        <p>选择基准后按共同交易日期加载，不填补跨市场休市价格。</p>
      )}
      <p>
        共同起点归零，仅比较原币价格回报，未含分红再投资、汇率、税费；不是组合总收益。共{" "}
        {data.dates.length} 个共同日期。
      </p>
    </section>
  );
}
export function Allocation({
  book,
  positions,
  quotes,
}: {
  book: Row;
  positions: Row[];
  quotes: Record<string, Row>;
}) {
  const host = useRef<HTMLDivElement>(null);
  const groups = new Map<string, Decimal>();
  let skipped = 0;
  for (const p of positions) {
    const s = book.securities.find((s: Row) => s.id === p.id),
      q = quotes[p.id],
      fx = s?.currency === "CNY" ? 1 : book.settings.fx?.[s?.currency]?.rate;
    if (!q?.last || !fx) {
      skipped++;
      continue;
    }
    const industry = s.industry || "待分类";
    groups.set(
      industry,
      (groups.get(industry) || new Decimal(0)).plus(
        new Decimal(p.quantity).mul(q.last).mul(fx),
      ),
    );
  }
  const data = [...groups].map(([name, v]) => ({ name, value: v.toNumber() }));
  const signature = JSON.stringify(data);
  useEffect(() => {
    if (!host.current || !data.length) return;
    const c = echarts.init(host.current, "yuchen");
    c.setOption({
      tooltip: { trigger: "item", formatter: "{b}<br/>¥ {c}（{d}%）" },
      legend: { bottom: 0 },
      series: [
        {
          type: "pie",
          radius: ["45%", "72%"],
          center: ["50%", "43%"],
          avoidLabelOverlap: true,
          label: { show: false },
          data,
        },
      ],
    });
    const resize = new ResizeObserver(() => c.resize());
    resize.observe(host.current);
    return () => {
      resize.disconnect();
      c.dispose();
    };
  }, [signature]);
  return (
    <section className="live-panel">
      <h2>行业配置 · 人民币参考</h2>
      {data.length ? (
        <div
          ref={host}
          role="img"
          aria-label="真实持仓行业配置图"
          style={{ height: 280 }}
        />
      ) : (
        <p>录入持仓并获得有效报价后显示行业占比。</p>
      )}
      <p>
        按持仓市值分类；{skipped}{" "}
        笔缺报价或汇率，未纳入图表。待分类持仓单独列示。
      </p>
    </section>
  );
}
export function ManualCalendar({
  book,
  setBook,
  open,
}: {
  book: Row;
  setBook: any;
  open: (id: string) => void;
}) {
  const [error, setError] = useState("");
  const events: Row[] = book.calendar || [];
  return (
    <section className="live-panel">
      <h2>公司事件备忘 · 人工维护</h2>
      <p>
        财报、除权除息、股东大会、解禁等事项可录入核实来源。备忘不会自动生成交易或现金分红记录。
      </p>
      <form
        className="live-form"
        onSubmit={(e) => {
          e.preventDefault();
          const f = e.currentTarget;
          const v = Object.fromEntries(new FormData(f).entries());
          try {
            if (!book.securities.some((s: Row) => s.id === v.instrument))
              throw Error("请先添加证券");
            if (v.source && !/^https?:\/\//i.test(String(v.source)))
              throw Error("来源需要完整的 http(s) 链接");
            setBook((b: Row) => ({
              ...b,
              calendar: [
                ...(b.calendar || []),
                { ...v, id: crypto.randomUUID(), archived: false },
              ],
            }));
            setError("");
            f.reset();
          } catch (e: any) {
            setError(e.message);
          }
        }}
      >
        <label>
          证券
          <select name="instrument" required>
            {book.securities.map((s: Row) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          事件类型
          <select name="kind">
            {["财报披露", "除权除息", "股东大会", "解禁/减持", "其他"].map(
              (k) => (
                <option key={k}>{k}</option>
              ),
            )}
          </select>
        </label>
        <label>
          事件日期
          <input name="date" type="date" required />
        </label>
        <label>
          事件说明
          <input name="title" maxLength={200} required />
        </label>
        <label>
          依据链接
          <input name="source" type="url" placeholder="https://…" />
        </label>
        <label>
          核实状态
          <select name="verified">
            <option value="pending">待核实</option>
            <option value="confirmed">已人工核实</option>
          </select>
        </label>
        <button className="button primary">保存备忘</button>
      </form>
      {error && <p role="alert">{error}</p>}
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>日期 / 证券</th>
              <th>类型与事项</th>
              <th>依据</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            {events
              .slice()
              .sort((a, b) => a.date.localeCompare(b.date))
              .map((e) => (
                <tr key={e.id} style={{ opacity: e.archived ? 0.5 : 1 }}>
                  <td>
                    {e.date}
                    <small>
                      <button
                        className="text-button"
                        onClick={() => open(e.instrument)}
                      >
                        {
                          book.securities.find(
                            (s: Row) => s.id === e.instrument,
                          )?.name
                        }
                      </button>
                    </small>
                  </td>
                  <td>
                    {e.kind}
                    <small>{e.title}</small>
                  </td>
                  <td>
                    {e.source ? (
                      <a href={e.source} target="_blank" rel="noreferrer">
                        核实来源 ↗
                      </a>
                    ) : (
                      "未填来源"
                    )}
                    <small>
                      {e.verified === "confirmed" ? "已人工核实" : "待核实"}
                    </small>
                  </td>
                  <td>
                    <button
                      className="text-button"
                      onClick={() =>
                        setBook((b: Row) => ({
                          ...b,
                          calendar: (b.calendar || []).map((x: Row) =>
                            x.id === e.id ? { ...x, archived: !x.archived } : x,
                          ),
                        }))
                      }
                    >
                      {e.archived ? "恢复" : "归档"}
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

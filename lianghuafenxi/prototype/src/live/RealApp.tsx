import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Decimal from "decimal.js";
import {
  LayoutDashboard,
  Star,
  Wallet,
  Bell,
  Settings,
  Plus,
  Download,
  Pause,
  Play,
} from "lucide-react";
import {
  createBook,
  addSecurity,
  projectAccount,
  commitEvent,
  correctEvent,
  validateImport,
  priceMetrics,
  annualSummary,
  aggregateBars,
  evaluateAlert,
  monitoredIds,
} from "../core/engine.mjs";
import { echarts } from "../charts";
import "./live.css";
import { Allocation, ManualCalendar } from "./WorkspaceExtras";
import { BatchAnalysis, Comparison } from "./WorkspaceExtras";
import { ResearchDialog } from "./ResearchDialog";
import { AnnualProfitChart, ValuationMetrics } from "./ResearchMetrics";
import { loadResearchPacket } from "../core/research-packet.mjs";
import { WatchlistTable, HoldingsTable } from "./SecurityTables";
import { useResearchSync } from "./useResearchData";
import {
  getResearchSnapshot,
  publishResearch,
} from "../core/research-store.mjs";
import { researchAssessment } from "../core/research.mjs";
type Row = Record<string, any>;
const SESSION = "yuchen-workspace-v2";
const titles = ["市场总览", "我的自选", "持仓管理", "事件与提醒", "资料与设置"];
const icons = [LayoutDashboard, Star, Wallet, Bell, Settings];
const fmt = (n: any, d = 2) =>
  n == null || n === "" || !Number.isFinite(Number(n))
    ? "—"
    : Number(n).toLocaleString("zh-CN", {
        maximumFractionDigits: d,
        minimumFractionDigits: d,
      });
const pct = (n: any) =>
  n == null ? "—" : `${Number(n) > 0 ? "+" : ""}${fmt(n)}%`;
const today = () =>
  new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Shanghai" });
async function api(path: string, options: RequestInit = {}) {
  const r = await fetch("/api/v1/" + path, {
    ...options,
    signal: options.signal || AbortSignal.timeout(45000),
  });
  const body = await r.json();
  if (!r.ok) throw Error(body.error?.message || `接口 ${r.status}`);
  return body.data;
}
function download(name: string, text: string, type = "application/json") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function initial() {
  try {
    const raw = sessionStorage.getItem(SESSION);
    return raw ? validateImport(JSON.parse(raw)) : createBook();
  } catch {
    return createBook();
  }
}
function Source({ quote }: { quote?: Row }) {
  return (
    <small className="source">
      {quote?.provider || "尚未获取"} · 来源时间{" "}
      {quote?.sourceTime
        ? new Date(quote.sourceTime).toLocaleString("zh-CN")
        : quote?.sourceTimeRaw || "待核实"}
      <br />
      接收{" "}
      {quote?.receivedAt
        ? new Date(quote.receivedAt).toLocaleTimeString("zh-CN")
        : "—"}
    </small>
  );
}
function Price({ quote }: { quote?: Row }) {
  return (
    <>
      <strong>
        {fmt(
          quote?.last,
          quote?.id?.startsWith("XHKG:") ||
            /^XSHG:5|^XSHE:15/.test(quote?.id || "")
            ? 3
            : 2,
        )}
      </strong>{" "}
      <span className={(quote?.change || 0) >= 0 ? "up" : "down"}>
        {pct(quote?.change)}
      </span>
    </>
  );
}
function Panel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="live-panel">
      <h2>{title}</h2>
      {children}
    </section>
  );
}
function Chart({ bars, period }: { bars: Row[]; period: string }) {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!host.current) return;
    const c = echarts.init(host.current, "yuchen");
    const rows = period === "minute" ? bars : aggregateBars(bars, period);
    c.setOption({
      animation: false,
      tooltip: { trigger: "axis" },
      grid: { left: 58, right: 20, top: 20, bottom: 40 },
      xAxis: { type: "category", data: rows.map((b: Row) => b.date) },
      yAxis: { type: "value", scale: true },
      series: [
        {
          type: "line",
          showSymbol: false,
          data: rows.map((b: Row) => b.close),
          lineStyle: { width: 1.6, color: "#9ccbfa" },
          areaStyle: { color: "#9ccbfa0b" },
        },
      ],
    });
    const resize = new ResizeObserver(() => c.resize());
    resize.observe(host.current);
    return () => {
      resize.disconnect();
      c.dispose();
    };
  }, [bars, period]);
  return (
    <div
      ref={host}
      className="live-chart"
      role="img"
      aria-label="来源真实价格趋势图"
    />
  );
}

export default function RealApp() {
  const [book, setBook] = useState<Row>(initial),
    [page, setPage] = useState(0),
    [indices, setIndices] = useState<Row[]>([]),
    [quotes, setQuotes] = useState<Record<string, Row>>({}),
    [network, setNetwork] = useState("正在连接数据网关"),
    [error, setError] = useState(""),
    [selected, setSelected] = useState(""),
    [refresh, setRefresh] = useState(0),
    [adding, setAdding] = useState(false),
    [imported, setImported] = useState<Row | null>(null),
    [historyPaused, setHistoryPaused] = useState(false);
  const closeResearch = useCallback(() => setSelected(""), []);
  const bookRef = useRef(book);
  bookRef.current = book;
  const alertStates = useRef<Record<string, Row>>({});
  useEffect(() => {
    try {
      sessionStorage.setItem(SESSION, JSON.stringify(book));
    } catch {
      setError("当前浏览器无法临时保存，请及时导出数据。");
    }
  }, [book]);
  useEffect(() => {
    let ended = false,
      timer: ReturnType<typeof setTimeout>;
    const load = async () => {
      try {
        const d = await api("config");
        if (!ended) {
          setIndices(d.indices);
          setNetwork("网关已连接");
        }
      } catch {
        if (!ended) {
          setNetwork("网关未连接，10秒后重试；请检查 npm run gateway");
          timer = setTimeout(load, 10000);
        }
      }
    };
    load();
    return () => {
      ended = true;
      clearTimeout(timer);
    };
  }, []);
  const all = useMemo(
    () => [
      ...indices,
      ...book.securities.filter(
        (s: Row) => !indices.some((i) => i.id === s.id),
      ),
    ],
    [indices, book.securities],
  );
  const ids = monitoredIds(book, {
    indices: indices.map((s) => s.id),
    researchId: selected || null,
  }).join(",");
  useEffect(() => {
    if (!ids) return;
    let ended = false,
      timer: ReturnType<typeof setTimeout> | undefined;
    let abort: AbortController | undefined;
    const poll = async () => {
      if (ended) return;
      if (document.hidden || bookRef.current.settings.paused) {
        timer = setTimeout(poll, 1000);
        return;
      }
      abort = new AbortController();
      try {
        const data: Row[] = [];
        const list = ids.split(",");
        for (let n = 0; n < list.length; n += 40) {
          const result = await api("quotes/batch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              instrument_ids: list.slice(n, n + 40),
              client_round_id: crypto.randomUUID(),
            }),
            signal: abort.signal,
          });
          if (
            !Array.isArray(result.items) ||
            result.items.some((q: any) => !q || typeof q.id !== "string")
          )
            throw Error("行情响应缺少有效记录，本轮不更新");
          data.push(...result.items);
        }
        if (ended) return;
        setQuotes((old) =>
          Object.fromEntries([
            ...Object.entries(old),
            ...data.map((q) => [q.id, q]),
          ]),
        );
        setNetwork(
          `已接收 ${data.filter((q) => q.last != null).length}/${list.length} 条报价`,
        );
        const hits: Row[] = [];
        for (const rule of bookRef.current.alerts.filter(
          (a: Row) => a.enabled !== false,
        )) {
          const q = data.find((q) => q.id === rule.instrument);
          if (
            !q?.last ||
            !q.sourceTime ||
            Date.now() - Date.parse(q.sourceTime) > 60000
          )
            continue;
          const evaluated = evaluateAlert(
            rule,
            alertStates.current[rule.id + (rule.baselineId || "")],
            Number(q.last),
          );
          alertStates.current[rule.id + (rule.baselineId || "")] =
            evaluated.state;
          if (evaluated.fired)
            hits.push({
              id: crypto.randomUUID(),
              rule: rule.id,
              instrument: rule.instrument,
              value: q.last,
              at: new Date().toISOString(),
              title: rule.title,
            });
        }
        if (hits.length)
          setBook((b) => ({
            ...b,
            occurrences: [...hits, ...b.occurrences].slice(0, 500),
            alerts: b.alerts.map((r: Row) =>
              r.mode === "once" && hits.some((h) => h.rule === r.id)
                ? {
                    ...r,
                    enabled: false,
                    completedAt: new Date().toISOString(),
                  }
                : r,
            ),
          }));
      } catch (e: any) {
        if (!ended && e.name !== "AbortError")
          setNetwork(`行情请求失败：${e.message}，已保留上次结果`);
      } finally {
        if (!ended)
          timer = setTimeout(
            poll,
            Math.max(5, Number(bookRef.current.settings.interval) || 5) * 1000,
          );
      }
    };
    poll();
    const visible = () => {
      if (!document.hidden) {
        alertStates.current = {};
      }
    };
    document.addEventListener("visibilitychange", visible);
    return () => {
      ended = true;
      clearTimeout(timer);
      abort?.abort();
      document.removeEventListener("visibilitychange", visible);
    };
  }, [ids, refresh]);
  const act = (fn: () => void) => {
    try {
      fn();
      setError("");
    } catch (e: any) {
      setError(e.message);
    }
  };
  const open = (id: string) => {
    setSelected(id);
  };
  const positions = book.accounts
    .flatMap((a: Row) =>
      projectAccount(book, a.id).positions.map((p: Row) => ({
        ...p,
        account: a.id,
      })),
    )
    .filter((p: Row) => Number(p.quantity) > 0);
  const held = new Set(positions.map((p: Row) => p.id));
  const researchUniverse = book.securities
    .filter(
      (s: Row) => held.has(s.id) || book.watch.some((w: Row) => w.id === s.id),
    )
    .slice()
    .sort((a: Row, b: Row) => Number(held.has(b.id)) - Number(held.has(a.id)));
  const researchSync = useResearchSync(
    researchUniverse,
    !book.settings.paused && !historyPaused && page <= 2,
  );
  const stat = useMemo(() => {
    let value = new Decimal(0),
      cost = new Decimal(0),
      covered = 0;
    for (const p of positions) {
      const s = book.securities.find((s: Row) => s.id === p.id),
        q = quotes[p.id],
        fx = s?.currency === "CNY" ? 1 : book.settings.fx?.[s?.currency]?.rate;
      if (!q?.last || !fx) continue;
      value = value.plus(new Decimal(p.quantity).mul(q.last).mul(fx));
      cost = cost.plus(new Decimal(p.cost).mul(fx));
      covered++;
    }
    return {
      value: value.toString(),
      pnl: value.minus(cost).toString(),
      covered,
    };
  }, [book, quotes]);
  const remove = (id: string) =>
    setBook((b) => ({
      ...b,
      revision: b.revision + 1,
      watch: b.watch.filter((w: Row) => w.id !== id),
    }));
  return (
    <div className="app live-app">
      <aside className="sidebar">
        <a className="brand" href="/">
          <img
            className="brand-symbol"
            src="/brand/yuchen-symbol.svg"
            alt="宇辰标志"
          />
          <div>
            宇辰看板<span>YUCHEN DASHBOARD</span>
          </div>
        </a>
        <div className="workspace-label">个人量化工作台</div>
        <nav>
          {titles.map((t, i) => {
            const Icon = icons[i];
            return (
              <button
                key={t}
                aria-label={t}
                title={t}
                className={"nav-item " + (i === page ? "active" : "")}
                onClick={() => setPage(i)}
              >
                <Icon size={18} />
                <span>{t}</span>
              </button>
            );
          })}
        </nav>
        <div className="sidebar-bottom">
          <p>会话临时保存</p>
          <small>关闭本次会话后不保证恢复，请主动导出。</small>
          <p>
            <a href="/?mode=demo">查看独立演示模式 ↗</a>
          </p>
        </div>
      </aside>
      <div className="main">
        <header className="topbar">
          <span>工作台 / {titles[page]}</span>
          <div className="live-actions">
            <span className="muted">
              {book.settings.paused ? "刷新已暂停" : "公开行情 · 自动刷新"}
            </span>
            <button
              className="button"
              aria-label="切换行情刷新"
              onClick={() => {
                setBook((b) => ({
                  ...b,
                  settings: { ...b.settings, paused: !b.settings.paused },
                }));
                setRefresh((x) => x + 1);
              }}
            >
              {book.settings.paused ? <Play size={14} /> : <Pause size={14} />}
            </button>
          </div>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <div className="eyebrow">YOUR MARKET, IN PERSPECTIVE</div>
              <h1>{titles[page]}</h1>
              <p>真实行情与个人台账 · 点击证券名称查看研究</p>
            </div>
            <div className="heading-actions">
              <button
                className="button"
                onClick={() =>
                  download(
                    "宇辰看板-" + today() + ".json",
                    JSON.stringify(book, null, 2),
                  )
                }
              >
                <Download size={14} />
                导出会话
              </button>
              <button
                className="button primary"
                onClick={() => setAdding(true)}
              >
                <Plus size={14} />
                添加证券
              </button>
            </div>
          </div>
          <div className="notice">
            {network}。刷新目标 {book.settings.interval}{" "}
            秒，数据源可能延迟；隐藏页面暂停请求，关闭页面停止监控。
          </div>
          {page <= 2 && (
            <div className="history-sync-status" role="status">
              <span>
                历史/财报资料已处理 {researchSync.done}/{researchSync.total} ·{" "}
                {researchSync.running
                  ? "正在补齐（优先持仓）"
                  : historyPaused
                    ? "同步已暂停"
                    : "空白项为未取得或来源缺失"}
              </span>
              <button
                className="text-button"
                onClick={() => setHistoryPaused((v) => !v)}
              >
                {historyPaused ? "继续资料同步" : "暂停资料同步"}
              </button>
              <button className="text-button" onClick={researchSync.reload}>
                重新获取资料
              </button>
            </div>
          )}
          {error && (
            <div className="live-error" role="alert">
              {error}
              <button className="text-button" onClick={() => setError("")}>
                关闭
              </button>
            </div>
          )}
          {page === 0 && (
            <>
              <div className="index-grid">
                {indices.map((s) => (
                  <button
                    className="index-card"
                    key={s.id}
                    onClick={() => open(s.id)}
                  >
                    <div>
                      {s.name}
                      <span>{s.currency}</span>
                    </div>
                    <Price quote={quotes[s.id]} />
                    <Source quote={quotes[s.id]} />
                  </button>
                ))}
              </div>
              <div className="live-grid">
                <Panel title="组合概况 · 人民币参考">
                  <div className="live-big">
                    ¥{" "}
                    {positions.length && !stat.covered ? "—" : fmt(stat.value)}
                  </div>
                  <p>
                    可估值部分浮盈亏{" "}
                    <span className={Number(stat.pnl) >= 0 ? "up" : "down"}>
                      {fmt(stat.pnl)}
                    </span>
                  </p>
                  <p>
                    已估值 {stat.covered} / {positions.length}{" "}
                    笔账户持仓；缺少报价或汇率的持仓不计入。
                  </p>
                  <p>
                    自选 {new Set(book.watch.map((w: Row) => w.id)).size} 只 ·
                    持仓 {new Set(positions.map((p: Row) => p.id)).size} 只
                  </p>
                </Panel>
                <Panel title="分析与数据质量">
                  <p>
                    真实报价{" "}
                    {all.filter((s) => quotes[s.id]?.last != null).length} /{" "}
                    {all.length}
                  </p>
                  <p>央国企、红筹属性需人工核实，避免按名称推断。</p>
                  <p>低股价和历史低位只是观察条件，不能单独作为买入依据。</p>
                  <button className="button" onClick={() => setPage(1)}>
                    查看自选与分类
                  </button>
                </Panel>
              </div>
            </>
          )}
          {page === 0 && (
            <BatchAnalysis
              book={book}
              quotes={quotes}
              open={open}
              refreshData={researchSync.reload}
              syncing={researchSync.running}
            />
          )}
          {page === 0 && (
            <Allocation book={book} positions={positions} quotes={quotes} />
          )}
          {page === 1 && (
            <WatchlistTable
              book={book}
              setBook={setBook}
              quotes={quotes}
              open={open}
              remove={remove}
            />
          )}
          {page === 2 && (
            <Portfolio
              book={book}
              setBook={setBook}
              quotes={quotes}
              open={open}
              act={act}
            />
          )}
          {page === 3 && (
            <Alerts book={book} setBook={setBook} act={act} open={open} />
          )}
          {page === 3 && (
            <ManualCalendar book={book} setBook={setBook} open={open} />
          )}
          {page === 4 && (
            <>
              <Panel title="会话与数据">
                <label>
                  <input
                    type="checkbox"
                    checked={book.settings.rulesEnabled === true}
                    onChange={(e) =>
                      setBook((b) => ({
                        ...b,
                        settings: {
                          ...b.settings,
                          rulesEnabled: e.target.checked,
                        },
                      }))
                    }
                  />
                  启用候选研究规则试算（research-v0.1-draft）
                </label>
                <p>
                  规则默认关闭；启用后仍需核验历史与重大事项。阈值未经投资效果验证。
                </p>
                <p>
                  所有自选、账户和台账仅保存在当前浏览器会话，不上传到网关。
                </p>
                <p>
                  行情查询只发送证券代码给公开数据源。免费接口无时效保证，报价与财报均显示来源。
                </p>
                <p>
                  历史日线与财报采用缓存优先策略，云端数据库未连接时直接查询来源。接入本账号 D1 后：往年日线每7天复核，含当日的历史分段5分钟更新，财报6小时更新；报价、成交与估值不写入数据库。缓存保留最多30天，来源故障时明确标记旧数据。关闭页面后不主动更新。
                </p>
                <label>
                  刷新间隔（秒）
                  <select
                    value={book.settings.interval}
                    onChange={(e) =>
                      setBook((b) => ({
                        ...b,
                        settings: {
                          ...b.settings,
                          interval: Number(e.target.value),
                        },
                      }))
                    }
                  >
                    {[5, 10, 15, 30, 60].map((n) => (
                      <option key={n}>{n}</option>
                    ))}
                  </select>
                </label>
                <p>
                  <label className="button">
                    导入会话 JSON
                    <input
                      type="file"
                      accept=".json,application/json"
                      onChange={async (e) => {
                        const file = e.target.files?.[0];
                        if (!file) return;
                        if (file.size > 5e6) {
                          setError("文件不能大于 5MB");
                          return;
                        }
                        try {
                          setImported(
                            validateImport(JSON.parse(await file.text())),
                          );
                        } catch (err: any) {
                          setError(err.message);
                        }
                        e.target.value = "";
                      }}
                    />
                  </label>
                </p>
                <p>
                  <button
                    className="button"
                    onClick={() =>
                      download(
                        "宇辰台账-" + today() + ".csv",
                        "\uFEFF" +
                          [
                            [
                              "时间",
                              "类型",
                              "证券",
                              "数量",
                              "价格",
                              "费用",
                              "币种",
                            ],
                            ...book.events
                              .filter((e: Row) => e.type !== "REVISION")
                              .map((e: Row) => [
                                e.at,
                                e.type,
                                e.instrument,
                                e.quantity,
                                e.price,
                                e.fee,
                                e.currency,
                              ]),
                          ]
                            .map((row) =>
                              row
                                .map(
                                  (v: any) =>
                                    '"' +
                                    String(v ?? "")
                                      .replace(/^[=+@-]/, "'$&")
                                      .replaceAll('"', '""') +
                                    '"',
                                )
                                .join(","),
                            )
                            .join("\r\n"),
                        "text/csv;charset=utf-8",
                      )
                    }
                  >
                    导出台账 CSV（原始记录，含已更正记录）
                  </button>
                </p>
              </Panel>
              <Fx book={book} setBook={setBook} act={act} />
              <Panel title="当前数据能力">
                <p>
                  A 股与港股报价、九项主要指数报价、A 股及港股日线、A
                  股年度利润表。
                </p>
                <p>
                  港股财报、美股指数历史、自动分红及公司事件源尚未接入；不填充演示数据。汇率需手动录入日期。
                </p>
                <p>
                  运行方式：先 npm run gateway，再 npm run
                  dev。部署验证将在功能验收后进行。
                </p>
              </Panel>
            </>
          )}
          <footer>宇辰看板 · 会话版 v0.2 · 仅作研究参考</footer>
        </main>
      </div>
      {selected && (
        <ResearchDialog
          name={all.find((s) => s.id === selected)?.name || selected}
          onClose={closeResearch}
        >
          <Research
            key={selected}
            security={all.find((s) => s.id === selected)}
            choices={all}
            select={setSelected}
            quote={quotes[selected]}
            book={book}
            setBook={setBook}
          />
        </ResearchDialog>
      )}
      {adding && (
        <AddSecurity
          close={() => setAdding(false)}
          add={(s, g) => {
            setBook((b) => addSecurity(b, s, g));
            setSelected(s.id);
            setAdding(false);
          }}
        />
      )}
      {imported && (
        <div className="modal-overlay">
          <section className="modal" role="dialog" aria-label="导入预览">
            <h2>导入预览</h2>
            <p>
              证券 {imported.securities.length} · 台账 {imported.events.length}{" "}
              · 账户 {imported.accounts.length}
            </p>
            <p>
              将替换当前会话。导入后会按证券代码向公开接口请求行情；请先导出当前数据。
            </p>
            <button className="button" onClick={() => setImported(null)}>
              取消
            </button>{" "}
            <button
              className="button primary"
              onClick={() => {
                setBook(imported);
                setQuotes({});
                alertStates.current = {};
                setImported(null);
              }}
            >
              确认替换并查询行情
            </button>
          </section>
        </div>
      )}
    </div>
  );
}

function AddSecurity({
  close,
  add,
}: {
  close: () => void;
  add: (s: Row, g: string) => void;
}) {
  const [q, setQ] = useState(""),
    [rows, setRows] = useState<Row[]>([]),
    [group, setGroup] = useState("默认分组"),
    [status, setStatus] = useState("");
  const search = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("正在搜索");
    try {
      const data = await api("instruments?q=" + encodeURIComponent(q));
      setRows(data.items);
      setStatus(data.items.length ? "" : "未找到证券，请尝试完整代码");
    } catch (e: any) {
      setStatus(e.message);
    }
  };
  return (
    <div className="modal-overlay">
      <section className="modal" role="dialog" aria-label="添加证券">
        <div className="live-actions">
          <h2>添加证券</h2>
          <button className="button" onClick={close}>
            关闭
          </button>
        </div>
        <p>搜索会向腾讯公开接口提交名称或代码。点击加入后会获取该证券行情。</p>
        <form onSubmit={search} className="live-actions">
          <input
            aria-label="证券名称或代码"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="如 600905 或 00762"
            required
          />
          <button className="button primary">搜索</button>
        </form>
        <label>
          自选分组
          <input
            value={group}
            maxLength={40}
            onChange={(e) => setGroup(e.target.value)}
          />
        </label>
        <p role="status">{status}</p>
        {rows.map((s) => (
          <div className="live-search-row" key={s.id}>
            <div>
              <strong>{s.name}</strong>
              <small>
                {s.id} · {s.currency}
              </small>
            </div>
            <button
              className="button"
              onClick={() => add(s, group.trim() || "默认分组")}
            >
              加入并获取报价
            </button>
          </div>
        ))}
      </section>
    </div>
  );
}

function Portfolio({ book, setBook, quotes, act, open }: any) {
  const [account, setAccount] = useState(book.accounts[0].id),
    [accountName, setAccountName] = useState(""),
    [edit, setEdit] = useState<Row | null>(null),
    [reason, setReason] = useState(""),
    [recordType, setRecordType] = useState("OPENING"),
    [savedMessage, setSavedMessage] = useState(""),
    [formVersion, setFormVersion] = useState(0);
  const [voidId, setVoidId] = useState(""),
    [voidReason, setVoidReason] = useState("");
  const result = projectAccount(book, account);
  const submit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget),
      v = Object.fromEntries(fd.entries());
    act(() => {
      const s = book.securities.find((s: Row) => s.id === v.instrument);
      const event = {
        ...v,
        id: crypto.randomUUID(),
        account,
        currency: ["CASH_IN", "CASH_OUT"].includes(String(v.type))
          ? v.cashCurrency
          : s?.currency,
        at: new Date(String(v.at)).toISOString(),
      };
      setBook(
        edit
          ? correctEvent(book, edit.id, event, reason)
          : commitEvent(book, event),
      );
      setEdit(null);
      setReason("");
      setSavedMessage("记录已保存，持仓与成本已重新计算。");
      setFormVersion((n) => n + 1);
    });
  };
  const labels: Row = {
    OPENING: "期初持仓",
    BUY: "买入",
    SELL: "卖出/清仓",
    DIVIDEND: "现金分红",
    SPLIT: "拆合股",
    TRANSFER_IN: "转入",
    TRANSFER_OUT: "转出",
    CASH_IN: "资金转入",
    CASH_OUT: "资金转出",
  };
  return (
    <>
      {voidId && (
        <div className="modal-overlay">
          <section className="modal" role="dialog" aria-label="撤销台账记录">
            <h2>撤销台账记录</h2>
            <p>
              原始记录仍保留在审计中。系统会回放后续记录，出现负持仓时拒绝撤销。
            </p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                act(() => {
                  setBook(correctEvent(book, voidId, null, voidReason));
                  setVoidId("");
                  setVoidReason("");
                });
              }}
            >
              <label>
                撤销原因
                <input
                  aria-label="撤销原因"
                  value={voidReason}
                  onChange={(e) => setVoidReason(e.target.value)}
                  required
                  maxLength={200}
                />
              </label>
              <div className="live-actions wrap">
                <button className="button primary">确认撤销</button>
                <button
                  type="button"
                  className="button"
                  onClick={() => setVoidId("")}
                >
                  取消
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
      <Panel title="账户与持仓">
        <div className="live-actions wrap">
          <select
            aria-label="当前账户"
            value={account}
            onChange={(e) => {
              setAccount(e.target.value);
              setEdit(null);
            }}
          >
            {book.accounts.map((a: Row) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
          <input
            aria-label="新账户名称"
            placeholder="新账户名称"
            value={accountName}
            maxLength={40}
            onChange={(e) => setAccountName(e.target.value)}
          />
          <button
            className="button"
            disabled={!accountName.trim()}
            onClick={() => {
              const id = crypto.randomUUID();
              setBook((b: Row) => ({
                ...b,
                accounts: [
                  ...b.accounts,
                  { id, name: accountName.trim(), currency: "CNY" },
                ],
              }));
              setAccount(id);
              setAccountName("");
            }}
          >
            增加账户
          </button>
        </div>
        <p>
          移动平均成本法；费用未知时收益仅为暂估。资金流水为录入起点后的变动，并非券商可用余额。
        </p>
        <HoldingsTable
          positions={result.positions}
          book={book}
          quotes={quotes}
          open={open}
        />
        <p>
          已录入资金净变动{" "}
          {Object.entries(result.cash)
            .map(([c, v]) => `${c} ${fmt(v)}`)
            .join(" / ") || "—"}
          ；累计净分红{" "}
          {Object.entries(result.dividends)
            .map(([c, v]) => `${c} ${fmt(v)}`)
            .join(" / ") || "—"}
        </p>
      </Panel>
      <Panel title={edit ? "更正历史记录" : "录入已发生交易 / 资金变动"}>
        {savedMessage && <p role="status">{savedMessage}</p>}
        <form onSubmit={submit} key={(edit?.id || "new") + formVersion}>
          <div className="live-form">
            <label>
              记录类型
              <select
                name="type"
                value={recordType}
                onChange={(e) => {
                  setRecordType(e.target.value);
                  setSavedMessage("");
                }}
              >
                {Object.entries(labels).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </label>
            <label>
              证券
              <select name="instrument" defaultValue={edit?.instrument || ""}>
                <option value="">资金流水可不选</option>
                {book.securities
                  .filter((s: Row) => s.type !== "index")
                  .map((s: Row) => (
                    <option key={s.id} value={s.id}>
                      {s.name} · {s.currency}
                    </option>
                  ))}
              </select>
            </label>
            <label>
              发生时间
              <input
                name="at"
                type="datetime-local"
                required
                defaultValue={
                  edit
                    ? new Date(
                        Date.parse(edit.at) -
                          new Date().getTimezoneOffset() * 60000,
                      )
                        .toISOString()
                        .slice(0, 16)
                    : new Date(
                        Date.now() - new Date().getTimezoneOffset() * 60000,
                      )
                        .toISOString()
                        .slice(0, 16)
                }
              />
            </label>
            {[
              ["quantity", "数量", "100"],
              ["price", "成交单价 / 期初均价", "10"],
              ["fee", "费用", "0"],
              ["gross", "税前分红总额", "0"],
              ["tax", "分红税费", "0"],
              ["net", "分红净额", "0"],
              ["ratio", "拆合股倍数", "1"],
              ["cost", "转入总成本", "0"],
              ["amount", "资金金额", "0"],
            ]
              .filter(([k]) =>
                (
                  ({
                    quantity: [
                      "OPENING",
                      "BUY",
                      "SELL",
                      "TRANSFER_IN",
                      "TRANSFER_OUT",
                    ],
                    price: ["OPENING", "BUY", "SELL"],
                    fee: ["OPENING", "BUY", "SELL"],
                    gross: ["DIVIDEND"],
                    tax: ["DIVIDEND"],
                    net: ["DIVIDEND"],
                    ratio: ["SPLIT"],
                    cost: ["TRANSFER_IN"],
                    amount: ["CASH_IN", "CASH_OUT"],
                  }) as Record<string, string[]>
                )[k].includes(recordType),
              )
              .map(([k, l, v]) => (
                <label key={k}>
                  {l}
                  <input
                    name={k}
                    inputMode="decimal"
                    defaultValue={
                      edit?.[k] ??
                      ([
                        "quantity",
                        "price",
                        "amount",
                        "gross",
                        "net",
                        "cost",
                      ].includes(k)
                        ? ""
                        : v)
                    }
                    required
                  />
                </label>
              ))}
            <label>
              费用状态
              <select
                name="feeStatus"
                defaultValue={edit?.feeStatus || "known"}
              >
                <option value="known">已知</option>
                <option value="unknown">暂未知（收益暂估）</option>
              </select>
            </label>
            <label>
              资金流水币种
              <select
                name="cashCurrency"
                defaultValue={edit?.currency || "CNY"}
              >
                {["CNY", "HKD", "USD"].map((c) => (
                  <option key={c}>{c}</option>
                ))}
              </select>
            </label>
            <label>
              备注
              <input
                name="note"
                maxLength={200}
                defaultValue={edit?.note || ""}
              />
            </label>
          </div>
          {edit && (
            <label>
              更正原因
              <input
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                required
              />
            </label>
          )}
          <p className="muted">
            按类型使用对应字段：买卖填数量、单价及费用；分红填税前额、税费及净额；转入填数量和总成本；拆合股填倍数。清仓请录入全部卖出数量。
          </p>
          <button className="button primary">
            {edit ? "保存更正并回放台账" : "保存记录并回放台账"}
          </button>
          {edit && (
            <button
              className="button"
              type="button"
              onClick={() => setEdit(null)}
            >
              取消更正
            </button>
          )}
        </form>
      </Panel>
      <Panel title="原始台账与更正审计">
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>时间</th>
                <th>记录</th>
                <th>参数</th>
                <th>操作 / 更正原因</th>
              </tr>
            </thead>
            <tbody>
              {book.events
                .filter(
                  (e: Row) =>
                    e.account === account ||
                    (e.type === "REVISION" &&
                      book.events.some(
                        (x: Row) => x.id === e.target && x.account === account,
                      )),
                )
                .slice()
                .reverse()
                .map((e: Row) => (
                  <tr key={e.id}>
                    <td>{new Date(e.at).toLocaleString("zh-CN")}</td>
                    <td>
                      {labels[e.type] || "更正/撤销"}
                      <small>
                        {book.securities.find((s: Row) => s.id === e.instrument)
                          ?.name || e.target}
                      </small>
                    </td>
                    <td>
                      {e.type === "REVISION"
                        ? e.replacement
                          ? "更正记录"
                          : "撤销记录"
                        : `${e.quantity || ""} × ${e.price || ""} ${e.currency || ""}`}
                      <small>{e.note}</small>
                    </td>
                    <td>
                      {e.type === "REVISION" ? (
                        e.reason
                      ) : (
                        <>
                          <button
                            className="text-button"
                            onClick={() => {
                              const revisions = book.events.filter(
                                (x: Row) =>
                                  x.type === "REVISION" && x.target === e.id,
                              );
                              setEdit(
                                revisions.length
                                  ? revisions.at(-1).replacement || e
                                  : e,
                              );
                              setRecordType(
                                (revisions.at(-1)?.replacement || e).type,
                              );
                              setReason("");
                            }}
                          >
                            更正
                          </button>
                          <button
                            className="text-button"
                            onClick={() => {
                              setVoidId(e.id);
                              setVoidReason("");
                            }}
                          >
                            撤销
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}

function Research({ security, choices, select, quote, book, setBook }: any) {
  const minuteController = useRef<AbortController | null>(null);
  useEffect(() => () => minuteController.current?.abort(), []);
  const [pack, setPack] = useState<Row>({ bars: [], reports: [], errors: [] }),
    [loading, setLoading] = useState(false),
    [period, setPeriod] = useState("day"),
    [minute, setMinute] = useState<Row[]>([]),
    [minuteError, setMinuteError] = useState(""),
    [windowYears, setWindowYears] = useState("3");
  useEffect(() => {
    const controller = new AbortController();
    setPack({ bars: [], reports: [], errors: [] });
    setMinute([]);
    setMinuteError("");
    setPeriod("day");
    if (!security) return;
    const cached = (getResearchSnapshot() as Record<string, Row>)[security.id];
    if (cached && Date.now() - cached.storedAt < 300000) {
      setPack(cached);
      setLoading(false);
      return () => controller.abort();
    }
    setLoading(true);
    loadResearchPacket(security, {
      request: api,
      asOf: today(),
      signal: controller.signal,
    })
      .then((packet) => {
        if (packet && !controller.signal.aborted) {
          setPack(packet);
          publishResearch(security.id, packet);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (!controller.signal.aborted) {
          setPack({ bars: [], reports: [], errors: [e.message] });
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [security?.id]);
  const cutoff = new Date(today() + "T00:00:00Z");
  if (windowYears === "52w") cutoff.setUTCDate(cutoff.getUTCDate() - 364);
  else cutoff.setUTCFullYear(cutoff.getUTCFullYear() - Number(windowYears));
  const windowBars = pack.bars.filter(
    (b: Row) => b.date >= cutoff.toISOString().slice(0, 10),
  );
  const m = priceMetrics(
      windowBars,
      Number(quote?.last) || NaN,
      windowYears === "52w" ? 1 : Number(windowYears),
    ),
    annual = annualSummary(pack.reports, security?.type);
  const price = Number(quote?.last) || NaN;
  const assessment = researchAssessment({
    enabled: book.settings.rulesEnabled === true,
    security,
    metrics: priceMetrics(pack.bars, price),
    price,
    annual,
    historyErrors: pack.errors,
  });
  const label = assessment.label;
  if (!security)
    return (
      <Panel title="选择研究标的">
        <select
          aria-label="研究证券"
          value=""
          onChange={(e) => select(e.target.value)}
        >
          <option value="">请选择证券或从市场总览点击指数</option>
          {choices.map((s: Row) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        <p>添加自选后，可查看真实历史价格与年度利润资料。</p>
      </Panel>
    );
  return (
    <>
      <div className="live-actions wrap">
        <select
          aria-label="研究证券"
          value={security.id}
          onChange={(e) => select(e.target.value)}
        >
          {choices.map((s: Row) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        <span>
          {security.id} · {security.currency}
        </span>
        <Price quote={quote} />
        <span className="tag">{loading ? "正在获取资料" : label}</span>
      </div>
      <Source quote={quote} />
      <nav className="research-section-links" aria-label="研究内容导航">
        {[
          ["research-valuation", "估值与成交"],
          ["research-profit", "五年盈利"],
          ["research-trend", "历史趋势"],
        ].map(([id, label]) => (
          <a
            key={id}
            href={"#" + id}
            onClick={(e) => {
              e.preventDefault();
              document
                .getElementById(id)
                ?.scrollIntoView({ behavior: "smooth", block: "start" });
            }}
          >
            {label}
          </a>
        ))}
      </nav>
      <div id="research-valuation">
        <ValuationMetrics
          security={security}
          paused={book.settings.paused}
          interval={book.settings.interval}
        />
      </div>
      {pack.errors.length > 0 && (
        <div className="notice">
          部分资料不可用：{[...new Set(pack.errors)].join("；")}
        </div>
      )}
      {pack.warnings?.length > 0 && <p className="source">{pack.warnings.join('；')}</p>}
      {pack.cacheInfo?.length > 0 && (
        <p className="source">
          历史/财报：{pack.cacheInfo.filter((c: Row) => c.layer === 'd1').length} 段来自云端缓存，
          {pack.cacheInfo.filter((c: Row) => c.layer === 'source').length} 段在取得本次资料时查询来源。
          最早来源查询时间：{pack.cacheInfo.filter((c: Row) => c.fetchedAt).map((c: Row) => c.fetchedAt).sort()[0]
            ? new Date(pack.cacheInfo.filter((c: Row) => c.fetchedAt).map((c: Row) => c.fetchedAt).sort()[0]).toLocaleString('zh-CN') : '未知'}。
          前复权日线可能因除权或来源修订而调整，缓存按上述周期复核。
        </p>
      )}
      <div className="live-metrics">
        {[
          ["区间最低 / 最高", `${fmt(m.low)} / ${fmt(m.high)}`],
          ["距离区间低点", pct(m.distanceLow)],
          ["区间位置", m.position == null ? "—" : fmt(m.position) + "%"],
          [
            "收盘价历史分位",
            m.percentile == null ? "—" : fmt(m.percentile) + "%",
          ],
          ["20 / 60 日收益", `${pct(m.return20)} / ${pct(m.return60)}`],
          ["MA50 / MA200", `${fmt(m.ma50)} / ${fmt(m.ma200)}`],
          ["日内高 / 低", `${fmt(quote?.high)} / ${fmt(quote?.low)}`],
          ["今开 / 昨收", `${fmt(quote?.open)} / ${fmt(quote?.previous)}`],
        ].map(([t, v]) => (
          <div key={t} className="live-panel">
            <small>{t}</small>
            <h3>{v}</h3>
          </div>
        ))}
      </div>
      <div id="research-profit">
        <Panel title="近五个完整财年 · 盈利与覆盖">
          <AnnualProfitChart reports={pack.reports} type={security.type} />
          <p>
            {security.type === "etf" || security.type === "index"
              ? "此类证券不适用公司利润统计"
              : `盈利 ${annual.positive} 年 / 零利润 ${annual.zero} 年 / 亏损 ${annual.negative} 年 / 缺失 ${annual.missing} 年；最新年度归母净利率（自算） ${pct(annual.margin)}`}
          </p>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>财年</th>
                  <th>归母净利润</th>
                  <th>营业收入</th>
                  <th>币种 / 来源 / 披露日</th>
                </tr>
              </thead>
              <tbody>
                {pack.reports.map((r: Row) => (
                  <tr key={r.year}>
                    <td>{r.year}</td>
                    <td>{fmt(r.profit)}</td>
                    <td>{fmt(r.revenue)}</td>
                    <td>
                      {r.currency} · {r.provider}
                      <small>{r.disclosedAt}</small>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p>
            候选规则优先检查风险和资料完整度；价格低位不能单独判定值得买入。规则尚未完成投资效果验证。
          </p>
        </Panel>
      </div>
      <div id="research-trend">
        <Panel title="历史价格与趋势">
          <div className="live-actions wrap">
            <select
              aria-label="历史分析区间"
              value={windowYears}
              onChange={(e) => setWindowYears(e.target.value)}
            >
              <option value="52w">52周</option>
              <option value="2">近两年</option>
              <option value="3">近三年</option>
            </select>
            {[
              ["day", "日线"],
              ["week", "周线"],
              ["month", "月线"],
              ["year", "年线"],
            ].map(([k, v]) => (
              <button
                className={"button " + (period === k ? "primary" : "")}
                key={k}
                onClick={() => setPeriod(k)}
              >
                {v}
              </button>
            ))}
            <button
              className={"button " + (period === "minute" ? "primary" : "")}
              onClick={async () => {
                setPeriod("minute");
                const id = security.id;
                minuteController.current?.abort();
                const controller = new AbortController();
                minuteController.current = controller;
                try {
                  const p = await api(
                    `history/${encodeURIComponent(id)}?interval=1m&from=${today()}&to=${today()}`,
                    { signal: controller.signal },
                  );
                  if (!controller.signal.aborted) setMinute(p.bars);
                } catch (e: any) {
                  if (!controller.signal.aborted) setMinuteError(e.message);
                }
              }}
            >
              当日分时
            </button>
          </div>
          {period === "minute" && minuteError && <p>{minuteError}</p>}
          {(period === "minute" ? minute : pack.bars).length ? (
            <Chart
              bars={period === "minute" ? minute : windowBars}
              period={period}
            />
          ) : (
            <p className="live-empty">
              {loading ? "正在读取真实数据…" : "暂无可用历史数据"}
            </p>
          )}
          <p>
            日线采用前复权来源；区位按返回的 {m.rows} 根日线计算（
            {m.from || "—"} 至 {m.to || "—"}）。
            {m.completeThreeYears
              ? "时间跨度达到所选区间，交易日完整性仍待核验。"
              : "尚未确认所选区间完整覆盖。"}
            上市以来极值未核实，暂不展示。
          </p>
          <p>
            区间位置=(现价−最低)/(最高−最低)；分位为现价在历史收盘价中的排名。前复权来源可能随公司行为调整。
          </p>
        </Panel>
      </div>
      <Panel title="研究证据与核验">
        <p>
          {assessment.ruleVersion} · {assessment.reasons.join("；")}
        </p>
        {assessment.missing.length > 0 && (
          <p>缺少：{assessment.missing.join("、")}</p>
        )}
        {security.type === "stock" && (
          <>
            <label>
              <input
                type="checkbox"
                checked={!!security.historyReviewed}
                onChange={(e) =>
                  setBook((b: Row) => ({
                    ...b,
                    securities: b.securities.map((s: Row) =>
                      s.id === security.id
                        ? { ...s, historyReviewed: e.target.checked }
                        : s,
                    ),
                  }))
                }
              />
              已人工核验三年历史的复权口径、交易日期和覆盖范围
            </label>
            <label>
              重大事项核验依据
              <input
                aria-label="重大事项核验依据"
                value={security.riskEvidence || ""}
                placeholder="公告链接、核验日期与结论"
                maxLength={1000}
                onChange={(e) =>
                  setBook((b: Row) => ({
                    ...b,
                    securities: b.securities.map((s: Row) =>
                      s.id === security.id
                        ? { ...s, riskEvidence: e.target.value }
                        : s,
                    ),
                  }))
                }
              />
            </label>
            <label>
              已知重大风险
              <input
                aria-label="已知重大风险"
                value={security.majorRisk || ""}
                placeholder="无已知风险时留空，核验依据仍需填写"
                maxLength={1000}
                onChange={(e) =>
                  setBook((b: Row) => ({
                    ...b,
                    securities: b.securities.map((s: Row) =>
                      s.id === security.id
                        ? { ...s, majorRisk: e.target.value }
                        : s,
                    ),
                  }))
                }
              />
            </label>
          </>
        )}
        <p>
          <button
            className="button"
            onClick={() =>
              download(
                security.name + "-研究记录.md",
                `# ${security.name} 研究记录\n\n生成时间：${new Date().toISOString()}\n\n证券：${security.id}\n\n当前价：${quote?.last ?? "缺失"} ${security.currency}\n\n来源：${quote?.provider || "缺失"}，源时间：${quote?.sourceTimeRaw || "未知"}\n\n历史范围：${m.from || "缺失"} 至 ${m.to || "缺失"}，日线前复权\n\n最低/最高：${m.low ?? "缺失"} / ${m.high ?? "缺失"}\n\n区间位置：${m.position ?? "缺失"}%；距低点：${m.distanceLow ?? "缺失"}%\n\n标签：${assessment.label}（${assessment.ruleVersion}）\n\n依据：${assessment.reasons.join("；")}\n\n缺项：${assessment.missing.join("；") || "规则要求项已填，不代表完整尽调"}\n\n财报：新浪财报，取得 ${pack.reports.length} 个完整财年；缺失 ${annual.missing}\n\n风险核验：${security.riskEvidence || "未核实"}\n\n笔记：${book.notes[security.id] || "无"}\n`,
                "text/markdown;charset=utf-8",
              )
            }
          >
            导出本次研究记录
          </button>
        </p>
      </Panel>
      <Comparison security={security} bars={windowBars} />
      {security.type !== "index" && (
        <Panel title="研究笔记">
          <textarea
            aria-label="研究笔记"
            value={book.notes[security.id] || ""}
            maxLength={10000}
            placeholder="记录观察理由、风险与跟踪条件…"
            onChange={(e) =>
              setBook((b: Row) => ({
                ...b,
                notes: { ...b.notes, [security.id]: e.target.value },
              }))
            }
          />
        </Panel>
      )}
    </>
  );
}

function Alerts({ book, setBook, act, open }: any) {
  const form = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const v = Object.fromEntries(new FormData(e.currentTarget).entries());
    act(() => {
      if (
        !book.securities.some((s: Row) => s.id === v.instrument) ||
        !Number.isFinite(Number(v.threshold)) ||
        Number(v.threshold) <= 0
      )
        throw Error("请选择证券并输入正数阈值");
      setBook((b: Row) => ({
        ...b,
        alerts: [
          ...b.alerts,
          {
            ...v,
            id: crypto.randomUUID(),
            threshold: Number(v.threshold),
            cooldown: Number(v.cooldown),
            enabled: true,
          },
        ],
      }));
    });
  };
  return (
    <>
      <Panel title="价格穿越提醒">
        <p>
          仅当前页面运行时监控。首次收到价格不触发；数据间隔超过60秒重新建立基线；来源时间不明或延迟超过60秒不触发。
        </p>
        <form onSubmit={form} className="live-actions wrap">
          <select name="instrument" required>
            {book.securities.map((s: Row) => (
              <option value={s.id} key={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <input name="title" placeholder="提醒名称" maxLength={80} required />
          <select name="direction">
            <option value="below">向下穿越 ≤</option>
            <option value="above">向上穿越 ≥</option>
          </select>
          <input
            aria-label="提醒价格阈值"
            name="threshold"
            type="number"
            min="0.0001"
            step="any"
            placeholder="价格"
            required
          />
          <select name="cooldown">
            <option value="60">冷却1分钟</option>
            <option value="300">冷却5分钟</option>
            <option value="3600">冷却1小时</option>
          </select>
          <select name="mode" aria-label="提醒频次">
            <option value="recurring">重复穿越（受冷却限制）</option>
            <option value="once">仅一次，触发后暂停</option>
          </select>
          <button className="button primary">新增提醒</button>
        </form>
        {book.alerts.map((a: Row) => (
          <div key={a.id} className="live-search-row">
            <span>
              {a.title} ·{" "}
              <button
                className="text-button"
                onClick={() => open(a.instrument)}
              >
                {book.securities.find((s: Row) => s.id === a.instrument)
                  ?.name || a.instrument}
              </button>{" "}
              {a.direction === "below" ? "≤" : "≥"} {a.threshold}
            </span>
            <button
              className="button"
              onClick={() =>
                setBook((b: Row) => ({
                  ...b,
                  alerts: b.alerts.map((x: Row) =>
                    x.id === a.id
                      ? {
                          ...x,
                          enabled: !x.enabled,
                          baselineId: crypto.randomUUID(),
                        }
                      : x,
                  ),
                }))
              }
            >
              {a.enabled ? "暂停" : "启用"}
            </button>
            <button
              className="text-button"
              onClick={() =>
                setBook((b: Row) => ({
                  ...b,
                  alerts: b.alerts.filter((x: Row) => x.id !== a.id),
                }))
              }
            >
              删除
            </button>
          </div>
        ))}
      </Panel>
      <Panel title="已触发提醒">
        {book.occurrences.length ? (
          book.occurrences.map((o: Row) => (
            <p key={o.id}>
              {new Date(o.at).toLocaleString("zh-CN")} · {o.title} ·{" "}
              <button
                className="text-button"
                onClick={() => open(o.instrument)}
              >
                {book.securities.find((s: Row) => s.id === o.instrument)
                  ?.name || o.instrument}
              </button>{" "}
              · {o.value}
            </p>
          ))
        ) : (
          <p>暂无触发记录。关闭页面后不监控，不补造触发。</p>
        )}
      </Panel>
    </>
  );
}
function Fx({ book, setBook, act }: any) {
  return (
    <Panel title="人民币参考汇率（人工录入）">
      <p>仅用于组合汇总；收益按当前汇率折算，不代表历史汇兑损益。</p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const v = Object.fromEntries(new FormData(e.currentTarget).entries());
          act(() => {
            const rate = Number(v.rate);
            if (!Number.isFinite(rate) || rate <= 0 || String(v.date) > today())
              throw Error("请输入有效汇率及不晚于今天的日期");
            setBook((b: Row) => ({
              ...b,
              settings: {
                ...b.settings,
                fx: {
                  ...b.settings.fx,
                  [String(v.currency)]: {
                    rate: String(v.rate),
                    date: v.date,
                    source: v.source,
                  },
                },
              },
            }));
          });
        }}
        className="live-actions wrap"
      >
        <select name="currency">
          <option>HKD</option>
          <option>USD</option>
        </select>
        <input
          aria-label="兑人民币汇率"
          name="rate"
          placeholder="1外币 = 人民币"
          required
        />
        <input
          aria-label="汇率日期"
          type="date"
          name="date"
          max={today()}
          required
        />
        <input name="source" placeholder="汇率来源" required />
        <button className="button">保存汇率</button>
      </form>
      {Object.entries(book.settings.fx).map(([c, v]: any) => (
        <p key={c}>
          {c}：
          {v
            ? `${v.rate} · ${v.date} · ${v.source}`
            : "未录入，不参与跨币种合计"}
        </p>
      ))}
    </Panel>
  );
}

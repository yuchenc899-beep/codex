import { useMemo, useState, type Dispatch, type SetStateAction } from "react";
import Decimal from "decimal.js";
import {
  buildSecurityRow,
  filterSecurities,
  sortRows,
} from "../core/table-query.mjs";
import { useResearchData } from "./useResearchData";
import {
  createTableFilters,
  isValidTableFilters,
  isValidTableOrder,
} from "../core/view-schema.mjs";
type Row = Record<string, any>;
export const defaultFilters = createTableFilters;
const n = (v: any, d = 2) =>
  v == null || !Number.isFinite(Number(v))
    ? "—"
    : Number(v).toLocaleString("zh-CN", {
        minimumFractionDigits: d,
        maximumFractionDigits: d,
      });
const percent = (v: any) => (v == null ? "—" : `${v > 0 ? "+" : ""}${n(v)}%`);
const money = (v: any) =>
  v == null
    ? "—"
    : Math.abs(v) >= 1e8
      ? `${n(v / 1e8)}亿`
      : Math.abs(v) >= 1e4
        ? `${n(v / 1e4)}万`
        : n(v);
function useOrder() {
  const [order, setOrder] = useState({ key: "name", direction: "asc" });
  return {
    order,
    restore: (next: Row) => {
      if (isValidTableOrder(next))
        setOrder({ key: next.key, direction: next.direction });
    },
    change: (key: string) =>
      setOrder((old) => ({
        key,
        direction: old.key === key && old.direction === "asc" ? "desc" : "asc",
      })),
  };
}
export function SortHead({
  columns,
  order,
  change,
}: {
  columns: string[][];
  order: Row;
  change: (key: string) => void;
}) {
  return (
    <thead>
      <tr>
        {columns.map(([key, title]) => (
          <th
            key={key}
            aria-sort={
              key === order.key
                ? order.direction === "asc"
                  ? "ascending"
                  : "descending"
                : "none"
            }
          >
            <button
              className="sort-heading"
              aria-label={`${title}排序`}
              onClick={() => change(key)}
            >
              {title}
              <span aria-hidden="true">
                {key === order.key
                  ? order.direction === "asc"
                    ? " ↑"
                    : " ↓"
                  : " ↕"}
              </span>
            </button>
          </th>
        ))}
        <th>操作</th>
      </tr>
    </thead>
  );
}
export function FilterBar({
  value: v,
  onChange: set,
  rows,
  groups = [],
  holding = false,
  label = "列表",
}: {
  value: Row;
  onChange: Dispatch<SetStateAction<Row>>;
  rows: Row[];
  groups?: string[];
  holding?: boolean;
  label?: string;
}) {
  const update = (key: string, value: any) =>
    set((old) => ({ ...old, [key]: value }));
  const invalid =
    (v.minPrice !== "" &&
      (!Number.isFinite(Number(v.minPrice)) || Number(v.minPrice) < 0)) ||
    (v.maxPrice !== "" &&
      (!Number.isFinite(Number(v.maxPrice)) || Number(v.maxPrice) < 0)) ||
    (v.minPrice !== "" &&
      v.maxPrice !== "" &&
      Number(v.minPrice) > Number(v.maxPrice));
  return (
    <>
      <div
        className="security-filter-bar"
        role="group"
        aria-label={label + "筛选"}
      >
        <input
          aria-label={label + "搜索"}
          value={v.search}
          onChange={(e) => update("search", e.target.value)}
          placeholder="搜索公司名称、代码或行业"
        />
        <div className="price-range">
          <input
            aria-label={label + "最低价"}
            inputMode="decimal"
            value={v.minPrice}
            onChange={(e) => update("minPrice", e.target.value)}
            placeholder="最低价"
          />
          <span>—</span>
          <input
            aria-label={label + "最高价"}
            inputMode="decimal"
            value={v.maxPrice}
            onChange={(e) => update("maxPrice", e.target.value)}
            placeholder="最高价"
          />
        </div>
        <select
          aria-label={label + "历史区间"}
          value={v.window}
          onChange={(e) => update("window", e.target.value)}
        >
          <option value="52w">52周</option>
          <option value="2">近两年</option>
          <option value="3">近三年</option>
        </select>
        <select
          aria-label={label + "市场"}
          value={v.market}
          onChange={(e) => update("market", e.target.value)}
        >
          <option value="all">全部市场</option>
          <option>A股</option>
          <option>港股</option>
        </select>
        <select
          aria-label={label + "品种"}
          value={v.type}
          onChange={(e) => update("type", e.target.value)}
        >
          <option value="all">全部品种</option>
          <option value="stock">股票</option>
          <option value="etf">ETF</option>
        </select>
        <select
          aria-label={label + "行业"}
          value={v.industry}
          onChange={(e) => update("industry", e.target.value)}
        >
          <option value="all">全部行业</option>
          {[...new Set(rows.map((r) => r.industry || "待分类"))]
            .sort()
            .map((i) => (
              <option key={i}>{i}</option>
            ))}
        </select>
        {groups.length > 0 && (
          <select
            aria-label={label + "分组"}
            value={v.group}
            onChange={(e) => update("group", e.target.value)}
          >
            <option value="all">全部分组</option>
            {groups.map((g) => (
              <option key={g}>{g}</option>
            ))}
          </select>
        )}
        <select
          aria-label={label + "低点距离"}
          value={v.distance}
          onChange={(e) => update("distance", e.target.value)}
        >
          <option value="all">任意低点距离</option>
          <option value="below-low">低于区间低点</option>
          <option value="within5">距低点0–5%</option>
          <option value="within15">距低点0–15%</option>
          <option value="above15">距低点超过15%</option>
          <option value="missing">低点资料缺失</option>
        </select>
        <select
          aria-label={label + "公司盈利"}
          value={v.profit}
          onChange={(e) => update("profit", e.target.value)}
        >
          <option value="all">全部公司盈利状态</option>
          <option value="positive">最近完整财年盈利</option>
          <option value="loss">最近完整财年亏损</option>
          <option value="zero">最近完整财年零利润</option>
          <option value="five-positive">近五年均盈利</option>
          <option value="missing">最近财年缺失</option>
          <option value="incomplete">五年财报不全</option>
          <option value="na">公司盈利不适用</option>
        </select>
        {holding && (
          <select
            aria-label={label + "持仓盈亏"}
            value={v.pnl}
            onChange={(e) => update("pnl", e.target.value)}
          >
            <option value="all">全部持仓浮盈亏</option>
            <option value="profit">持仓浮盈</option>
            <option value="loss">持仓浮亏</option>
            <option value="flat">持仓持平</option>
            <option value="missing">持仓估值缺失</option>
          </select>
        )}
        <select
          aria-label={label + "数据状态"}
          value={v.data}
          onChange={(e) => update("data", e.target.value)}
        >
          <option value="all">全部资料状态</option>
          <option value="loaded">已有区间历史</option>
          <option value="missing">区间历史缺失/待载入</option>
          <option value="quote-missing">报价缺失</option>
        </select>
        <button className="button" onClick={() => set(defaultFilters())}>
          重置筛选
        </button>
      </div>
      {invalid && (
        <p role="alert" className="filter-error">
          价格区间需为非负数字，最低价不能大于最高价。
        </p>
      )}
      <div className="quick-row table-quick">
        <span>快捷筛选</span>
        <button className="button" onClick={() => set(defaultFilters())}>
          全部
        </button>
        <button
          className="button"
          onClick={() => set({ ...defaultFilters(), low20: true })}
        >
          A股/ETF低于20元
        </button>
        <button
          className="button"
          onClick={() => update("distance", "within5")}
        >
          接近区间低点
        </button>
        <button
          className="button"
          onClick={() => update("distance", "below-low")}
        >
          低于区间低点
        </button>
        <button
          className="button"
          onClick={() => update("profit", "five-positive")}
        >
          近五年均盈利
        </button>
      </div>
      <p className="table-unit-note">
        价格和金额按证券原币筛选、排序（CNY/HKD），未跨币种换算；历史区间按所选范围的前复权来源数据。资料未取得时保留缺失，不计为零或亏损。
      </p>
    </>
  );
}
function Distance({ row: r }: any) {
  return (
    <>
      <strong
        className={r.distanceLow != null && r.distanceLow < 0 ? "down" : ""}
      >
        {percent(r.distanceLow)}
      </strong>
      {r.distanceLow != null && (
        <div className="low-distance-track">
          <span
            style={{
              width: Math.min(100, Math.max(2, Math.abs(r.distanceLow))) + "%",
            }}
          />
        </div>
      )}
      <small>
        {r.distanceLow != null && r.distanceLow < 0
          ? "低于已取得区间低点"
          : r.historyRows
            ? `${r.historyRows}根日线，完整性待核验`
            : "历史资料待取得"}
      </small>
    </>
  );
}
function CompanyProfit({ row: r }: any) {
  return r.type !== "stock" ? (
    <>不适用</>
  ) : (
    <>
      {r.profitPositiveYears == null
        ? "待取得"
        : `${r.profitPositiveYears}/5年盈利`}
      <small>
        {r.profitMissing > 0 ? `缺失${r.profitMissing}年` : "五年利润已取得"}
      </small>
    </>
  );
}
export function WatchlistTable({ book, setBook, quotes, open, remove }: any) {
  const [filters, setFilters] = useState<Row>(defaultFilters),
    [saved, setSaved] = useState("");
  const { order, change, restore } = useOrder(),
    packets = useResearchData();
  const base = useMemo(
    () =>
      book.securities
        .filter((s: Row) => book.watch.some((w: Row) => w.id === s.id))
        .map((s: Row) => ({
          ...buildSecurityRow(s, quotes[s.id], packets[s.id], filters.window),
          groupList: book.watch
            .filter((w: Row) => w.id === s.id)
            .map((w: Row) => w.group),
          groupText: book.watch
            .filter((w: Row) => w.id === s.id)
            .map((w: Row) => w.group)
            .join("、"),
        })),
    [book, quotes, packets, filters.window],
  );
  const rows = sortRows(
    filterSecurities(base, filters),
    order.key,
    order.direction,
  );
  const columns = [
    ["name", "公司 / 代码"],
    ["market", "市场"],
    ["price", "当前价格"],
    ["change", "日涨跌"],
    ["historyLow", "区间最低价"],
    ["distanceLow", "距区间低点%"],
    ["industry", "行业"],
    ["ownership", "归属属性"],
    ["groupText", "分组"],
    ["profitPositiveYears", "近五年盈利"],
    ["profit", "最新财年归母利润"],
    ["pe", "PE(TTM)"],
    ["quoteTime", "报价时间"],
    ["dataState", "资料状态"],
  ];
  const update = (id: string, key: string, value: any) =>
    setBook((b: Row) => ({
      ...b,
      securities: b.securities.map((s: Row) =>
        s.id === id ? { ...s, [key]: value } : s,
      ),
    }));
  return (
    <section className="live-panel">
      <h2>自选证券</h2>
      <FilterBar
        value={filters}
        onChange={setFilters}
        rows={base}
        groups={book.groups}
        label="自选"
      />
      <div className="live-actions wrap">
        <input
          aria-label="筛选视图名称"
          value={saved}
          maxLength={40}
          onChange={(e) => setSaved(e.target.value)}
          placeholder="保存视图名称"
        />
        <button
          className="button"
          disabled={!saved.trim() || !isValidTableFilters(filters)}
          onClick={() => {
            setBook((b: Row) => ({
              ...b,
              views: [
                ...b.views.filter((v: Row) => v.name !== saved.trim()),
                {
                  name: saved.trim(),
                  search: filters.search,
                  industry: filters.industry,
                  group: filters.group,
                  low: filters.low20,
                  filters,
                  order,
                },
              ],
            }));
            setSaved("");
          }}
        >
          保存视图
        </button>
        {book.views.map((v: Row) => (
          <button
            className="button"
            key={v.name}
            onClick={() => {
              setFilters(
                isValidTableFilters(v.filters)
                  ? { ...defaultFilters(), ...v.filters }
                  : {
                      ...defaultFilters(),
                      search: v.search,
                      industry: v.industry === "全部行业" ? "all" : v.industry,
                      group: v.group === "全部分组" ? "all" : v.group,
                      low20: v.low,
                    },
              );
              if (v.order) restore(v.order);
            }}
          >
            {v.name}
          </button>
        ))}
      </div>
      <p role="status">
        显示 {rows.length} / {base.length} 只 ·
        点击列标题升序/降序；点击证券名称打开研究弹窗。
      </p>
      <div className="table-scroll security-table">
        <table>
          <SortHead columns={columns} order={order} change={change} />
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
                <td>
                  {r.market}
                  <small>{r.type === "etf" ? "ETF" : "股票"}</small>
                </td>
                <td>
                  {n(r.price, r.currency === "HKD" || r.type === "etf" ? 3 : 2)}
                </td>
                <td
                  className={
                    r.change == null ? "muted" : r.change >= 0 ? "up" : "down"
                  }
                >
                  {percent(r.change)}
                </td>
                <td>
                  {n(r.historyLow)}
                  <small>{r.historyLowDate || "—"}</small>
                </td>
                <td>
                  <Distance row={r} />
                </td>
                <td>
                  <input
                    aria-label={`${r.name}行业`}
                    value={r.industry || "待分类"}
                    maxLength={40}
                    onChange={(e) => update(r.id, "industry", e.target.value)}
                  />
                </td>
                <td>
                  <select
                    aria-label={`${r.name}属性`}
                    value={r.ownership || "待核实"}
                    onChange={(e) => update(r.id, "ownership", e.target.value)}
                  >
                    {["待核实", "央企", "地方国企", "红筹", "其他"].map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </select>
                  <input
                    aria-label={`${r.name}属性依据`}
                    placeholder="依据链接 / 备注"
                    value={r.ownershipEvidence || ""}
                    onChange={(e) =>
                      update(r.id, "ownershipEvidence", e.target.value)
                    }
                  />
                </td>
                <td>{r.groupText}</td>
                <td>
                  <CompanyProfit row={r} />
                </td>
                <td>
                  {money(r.profit)}
                  <small>
                    {r.profitYear}FY · {r.profitCurrency || "币种待核实"}
                  </small>
                </td>
                <td>{r.type === "stock" ? n(r.pe) : "不适用"}</td>
                <td>
                  {quotes[r.id]?.sourceTime
                    ? new Date(quotes[r.id].sourceTime).toLocaleString("zh-CN")
                    : quotes[r.id]?.sourceTimeRaw || "—"}
                </td>
                <td>
                  {r.dataState}
                  <small>
                    {r.historyFrom || "—"} 至 {r.historyTo || "—"}
                  </small>
                </td>
                <td>
                  <button className="text-button" onClick={() => open(r.id)}>
                    研究
                  </button>
                  <button className="text-button" onClick={() => remove(r.id)}>
                    删除自选
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!rows.length && (
        <p className="live-empty">
          暂无符合条件的证券。资料仍在加载时，公司盈利及低点筛选只使用已取得的数据。
        </p>
      )}
    </section>
  );
}
export function HoldingsTable({ positions, book, quotes, open }: any) {
  const [filters, setFilters] = useState<Row>(defaultFilters),
    { order, change } = useOrder(),
    packets = useResearchData();
  const base = positions.map((p: Row) => {
    const s = book.securities.find((s: Row) => s.id === p.id);
    const row = buildSecurityRow(
      s,
      quotes[p.id],
      packets[p.id],
      filters.window,
    );
    const quantity = Number(p.quantity),
      cost = Number(p.cost),
      value =
        row.price != null
          ? new Decimal(p.quantity).mul(String(row.price))
          : null,
      floating = value ? value.minus(p.cost) : null;
    return {
      ...row,
      quantity,
      cost,
      average:
        quantity > 0 ? new Decimal(p.cost).div(p.quantity).toNumber() : null,
      value: value?.toNumber() ?? null,
      floating: floating?.toNumber() ?? null,
      floatingRate:
        floating && cost > 0 ? floating.div(p.cost).mul(100).toNumber() : null,
      realized: Number(p.realized),
      complete: p.complete,
    };
  });
  const rows = sortRows(
      filterSecurities(base, filters),
      order.key,
      order.direction,
    ),
    columns = [
      ["name", "证券 / 代码"],
      ["industry", "行业"],
      ["market", "市场"],
      ["price", "当前价格"],
      ["change", "日涨跌幅"],
      ["historyLow", "区间最低价"],
      ["distanceLow", "距区间低点%"],
      ["quantity", "数量"],
      ["cost", "剩余成本"],
      ["average", "平均成本"],
      ["value", "市值"],
      ["floating", "持仓浮盈亏"],
      ["floatingRate", "浮盈亏率"],
      ["realized", "已实现收益"],
      ["profitPositiveYears", "公司近五年盈利"],
    ];
  return (
    <>
      <FilterBar
        value={filters}
        onChange={setFilters}
        rows={base}
        holding
        label="持仓"
      />
      <p role="status">
        显示 {rows.length} / {base.length}{" "}
        个账户持仓记录；筛选不会修改真实台账。金额按原币，成本为移动平均法。
      </p>
      <div className="table-scroll security-table">
        <table>
          <SortHead columns={columns} order={order} change={change} />
          <tbody>
            {rows.map((r: Row) => (
              <tr key={r.id}>
                <td>
                  <button
                    className="text-button"
                    aria-label={`查看${r.name}（${r.code}）研究`}
                    onClick={() => open(r.id)}
                  >
                    {r.name}
                  </button>
                  <small>
                    {r.code} · {r.currency}
                  </small>
                </td>
                <td>{r.industry || "待分类"}</td>
                <td>{r.market}</td>
                <td>
                  {n(r.price, r.currency === "HKD" || r.type === "etf" ? 3 : 2)}
                </td>
                <td className={r.change == null ? 'muted' : r.change >= 0 ? 'up' : 'down'}>
                  {percent(r.change)}
                </td>
                <td>
                  {n(r.historyLow)}
                  <small>{r.historyLowDate || "—"}</small>
                </td>
                <td>
                  <Distance row={r} />
                </td>
                <td>{n(r.quantity, 4)}</td>
                <td>{n(r.cost)}</td>
                <td>{n(r.average, 4)}</td>
                <td>{n(r.value)}</td>
                <td
                  className={
                    r.floating == null
                      ? "muted"
                      : r.floating >= 0
                        ? "up"
                        : "down"
                  }
                >
                  {n(r.floating)}
                </td>
                <td>{percent(r.floatingRate)}</td>
                <td>
                  {n(r.realized)}
                  {!r.complete && <small>费用待补</small>}
                </td>
                <td>
                  <CompanyProfit row={r} />
                </td>
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
    </>
  );
}

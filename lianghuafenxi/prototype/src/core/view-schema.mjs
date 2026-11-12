export const createTableFilters = () => ({
  search: "",
  minPrice: "",
  maxPrice: "",
  industry: "all",
  group: "all",
  market: "all",
  type: "all",
  ownership: "all",
  profit: "all",
  distance: "all",
  data: "all",
  pnl: "all",
  window: "3",
  low20: false,
});
const enums = {
  market: ["all", "A股", "港股"],
  type: ["all", "stock", "etf"],
  ownership: ["all", "待核实", "央企", "地方国企", "红筹", "其他"],
  profit: [
    "all",
    "positive",
    "loss",
    "zero",
    "five-positive",
    "missing",
    "incomplete",
    "na",
  ],
  distance: ["all", "below-low", "within5", "within15", "above15", "missing"],
  data: ["all", "loaded", "missing", "quote-missing"],
  pnl: ["all", "profit", "loss", "flat", "missing"],
  window: ["52w", "2", "3"],
};
export function isValidTableFilters(v) {
  if (!v || typeof v !== "object" || Array.isArray(v)) return false;
  const shape = createTableFilters();
  if (
    Object.keys(v).some((k) => !Object.hasOwn(shape, k)) ||
    Object.keys(shape).some((k) => typeof v[k] !== typeof shape[k])
  )
    return false;
  if (Object.entries(enums).some(([k, values]) => !values.includes(v[k])))
    return false;
  if (["search", "industry", "group"].some((k) => v[k].length > 200))
    return false;
  for (const k of ["minPrice", "maxPrice"])
    if (
      v[k].trim() !== "" &&
      (!Number.isFinite(Number(v[k])) || Number(v[k]) < 0)
    )
      return false;
  return (
    v.minPrice.trim() === "" ||
    v.maxPrice.trim() === "" ||
    Number(v.minPrice) <= Number(v.maxPrice)
  );
}
const sortKeys = new Set([
  "name",
  "market",
  "price",
  "change",
  "historyLow",
  "distanceLow",
  "industry",
  "ownership",
  "groupText",
  "profitPositiveYears",
  "profit",
  "pe",
  "quoteTime",
  "dataState",
  "quantity",
  "cost",
  "average",
  "value",
  "floating",
  "floatingRate",
  "realized",
  "position",
  "researchLabel",
]);
export const isValidTableOrder = (v) =>
  !!v &&
  typeof v === "object" &&
  !Array.isArray(v) &&
  sortKeys.has(v.key) &&
  ["asc", "desc"].includes(v.direction);

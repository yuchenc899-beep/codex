import test from "node:test";
import assert from "node:assert/strict";
test("银行按归母字段读取，不以含少数股东的净利润替代", () => {
  const payload = {
    result: {
      data: {
        report_list: {
          20251231: {
            data: [
              {
                item_field: "NETPROFIT",
                item_title: "净利润",
                item_value: "27751000000",
              },
              {
                item_field: "NETPARECOMPPROF",
                item_title: "归属于母公司的净利润",
                item_value: "27200000000",
              },
              { item_title: "营业收入", item_value: "91914000000" },
            ],
          },
        },
      },
    },
  };
  assert.equal(
    parseSinaFinance(payload, "2026-11-11")[0].profit,
    "27200000000",
  );
});
import {
  symbolFor,
  parseQuotes,
  parseDaily,
  parseSinaFinance,
  handleRequest,
} from "../server/gateway.mjs";
test("财报来源空字符串是缺失，明确零利润保留为零", () => {
  const result = parseSinaFinance(
    {
      result: {
        data: {
          report_list: {
            20251231: {
              data: [
                { item_title: "归属于母公司所有者的净利润", item_value: "" },
                { item_title: "营业收入", item_value: "  " },
              ],
            },
            20241231: {
              data: [
                { item_title: "归属于母公司所有者的净利润", item_value: "0" },
              ],
            },
          },
        },
      },
    },
    "2026-11-11",
  );
  assert.equal(result[0].profit, null);
  assert.equal(result[0].revenue, null);
  assert.equal(result[1].profit, "0");
});
test("部分命中缓存时，等待另一证券响应期间过期的报价仍返回带来源时间的快照，不返回null", async () => {
  const original = Date.now;
  let now = original();
  Date.now = () => now;
  const post = (ids) =>
    new Request("http://localhost/api/v1/quotes/batch", {
      method: "POST",
      body: JSON.stringify({ instrument_ids: ids }),
    });
  const fetcher = async () => {
    now += 2000;
    const p = Array(50).fill("");
    p[3] = "10";
    p[1] = "测试";
    return new Response(
      `v_sh600997="${p.join("~")}";v_sh600998="${p.join("~")}";`,
    );
  };
  try {
    await handleRequest(post(["XSHG:600997"]), fetcher);
    now += 4000;
    const r = await handleRequest(
      post(["XSHG:600997", "XSHG:600998"]),
      fetcher,
    );
    const p = await r.json();
    assert.deepEqual(
      p.data.items.map((q) => q?.id),
      ["XSHG:600997", "XSHG:600998"],
    );
  } finally {
    Date.now = original;
  }
});
test("港股斜线时间按港股时区解析，美股未知时区不猜测", () => {
  const p = Array(50).fill("");
  p[3] = "10";
  p[30] = "2026/11/11 10:00:00";
  assert.equal(
    parseQuotes(`v_hk00762="${p.join("~")}";`, ["XHKG:00762"])[0].sourceTime,
    "2026-11-11T02:00:00.000Z",
  );
  p[30] = "2026-11-10 17:15:00";
  assert.equal(
    parseQuotes(`v_usIXIC="${p.join("~")}";`, ["INDEX:IXIC"])[0].sourceTime,
    null,
  );
});
test("非法JSON和不存在的日历日期在请求源端前拒绝", async () => {
  let calls = 0;
  const f = async () => {
    calls++;
    throw Error("unexpected");
  };
  const a = await handleRequest(
    new Request("http://localhost/api/v1/quotes/batch", {
      method: "POST",
      body: "{",
    }),
    f,
  );
  const b = await handleRequest(
    new Request(
      "http://localhost/api/v1/history/XSHG:600905?from=2026-02-30&to=2026-03-05",
    ),
    f,
  );
  assert.equal(a.status, 400);
  assert.equal(b.status, 400);
  assert.equal(calls, 0);
});
test("证券ID转换白名单，拒绝URL注入和畸形代码", () => {
  assert.equal(symbolFor("XSHG:600905"), "sh600905");
  assert.equal(symbolFor("XHKG:00762"), "hk00762");
  assert.equal(symbolFor("INDEX:IXIC"), "usIXIC");
  assert.throws(() => symbolFor("https://evil.test"));
  assert.throws(() => symbolFor("XSHG:600905,usAAPL"));
});
test("报价无效0与源端时点分别保留，不用接收时间伪造源时间", () => {
  const a = Array(60).fill("");
  Object.assign(a, {
    0: "1",
    1: "测试证券",
    2: "600905",
    3: "4.32",
    4: "4.30",
    5: "4.31",
    6: "123",
    30: "20261111103000",
    31: "0.02",
    32: "0.47",
    33: "4.35",
    34: "4.28",
  });
  const q = parseQuotes(
    `v_sh600905="${a.join("~")}";`,
    ["XSHG:600905"],
    "2026-11-11T02:30:01Z",
  );
  assert.equal(q[0].last, "4.32");
  assert.equal(q[0].sourceTime, "2026-11-11T02:30:00.000Z");
  a[3] = "0";
  assert.equal(
    parseQuotes(`v_sh600905="${a.join("~")}";`, ["XSHG:600905"])[0].last,
    null,
  );
});
test("历史OHLC校验，剔除无效零值并标记覆盖", () => {
  const r = parseDaily({
    data: {
      klines: ["2026-11-10,10,12,13,9,100,1200", "2026-11-11,0,0,0,0,0,0"],
    },
  });
  assert.equal(r.bars.length, 1);
  assert.equal(r.rejected, 1);
  assert.equal(r.bars[0].close, 12);
});
test("网关参数错误不进行外部请求，私人接口默认关闭", async () => {
  let calls = 0;
  const fetcher = async () => {
    calls++;
    throw Error("unexpected");
  };
  let r = await handleRequest(
    new Request("http://localhost/api/v1/quotes/batch", {
      method: "POST",
      body: JSON.stringify({ instrument_ids: ["https://evil.test"] }),
    }),
    fetcher,
  );
  assert.equal(r.status, 400);
  assert.equal(calls, 0);
  r = await handleRequest(
    new Request("http://localhost/api/v1/accounts"),
    fetcher,
  );
  assert.equal(r.status, 403);
});
test("证券搜索解码来源Unicode转义，显示中文公司名", async () => {
  const r = await handleRequest(
    new Request("http://localhost/api/v1/instruments?q=600905"),
    async () =>
      new Response(
        String.raw`v_hint="sh~600905~\u4e09\u5ce1\u80fd\u6e90~sxny~GP-A";`,
      ),
  );
  const v = await r.json();
  assert.equal(v.data.items[0].name, "三峡能源");
});

import hashlib
import json
import re
from decimal import Decimal


def security_id(code, market):
    if market == "港股":
        return f"HK:{code.zfill(5)}"
    exchange = "BJ" if code.startswith(("4", "8", "92")) else (
        "SH" if code.startswith(("5", "6")) else "SZ"
    )
    return f"{exchange}:{code}"


def amount(cell):
    value = cell.replace(",", "").strip()
    return str(Decimal(value)) if re.fullmatch(r"-?\d+(\.\d+)?", value) else None


def parse_archive(markdown):
    dates = re.search(r"自选 (\d{4}-\d{2}-\d{2}) 报价.*持仓 (\d{4}-\d{2}-\d{2}) 快照", markdown)
    if not dates:
        raise ValueError("清单缺少自选报价和持仓快照日期")
    archive = {"watchlist_as_of": dates[1], "positions_as_of": dates[2],
               "positions": [], "watchlist": []}
    section = None
    for line in markdown.splitlines():
        if line.startswith("## 一、"):
            section = "positions"
        elif line.startswith("## "):
            section = None
        elif heading := re.match(r"^### \d+\. (A股|港股|ETF)", line):
            section = heading[1]
        if not section or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        code_index = 1 if section == "positions" else 0
        if len(cells) <= code_index or not re.fullmatch(r"\d{4,6}", cells[code_index]):
            continue
        if section == "positions":
            if len(cells) < 10:
                raise ValueError("持仓记录缺少必要字段")
            name, code, market = cells[:3]
            archive["positions"].append({
                "id": security_id(code, market), "name": name, "market": market,
                "currency": "HKD" if market == "港股" else "CNY",
                "quantity": int(cells[3]), "cost": amount(cells[5]),
                "price": amount(cells[6]), "value_cny": amount(cells[7]),
                "pnl_cny": amount(cells[8]), "note": cells[10] if len(cells) > 10 else "",
            })
        else:
            code, name, industry, price = cells[:4]
            archive["watchlist"].append({
                "id": security_id(code, section), "name": name, "market": section,
                "currency": "HKD" if section == "港股" else "CNY",
                "industry": industry, "price": amount(price),
                "day_change": cells[4], "year_change": cells[6],
                "pe_ttm": cells[7],
            })
    if not archive["positions"] or not archive["watchlist"]:
        raise ValueError("清单没有可导入的持仓或自选记录")
    return archive


def import_archive(db, path):
    content = path.read_bytes()
    archive = parse_archive(content.decode("utf-8-sig"))
    archive["source"] = path.name
    with db:
        db.execute("""CREATE TABLE IF NOT EXISTS archives (
            id INTEGER PRIMARY KEY, digest TEXT NOT NULL UNIQUE, payload TEXT NOT NULL
        )""")
        db.execute("INSERT OR IGNORE INTO archives(digest, payload) VALUES (?, ?)", (
            hashlib.sha256(content).hexdigest(), json.dumps(archive, ensure_ascii=False)
        ))


def read_archive(db):
    row = db.execute("SELECT payload FROM archives ORDER BY id DESC LIMIT 1").fetchone()
    return json.loads(row[0]) if row else None

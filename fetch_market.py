"""Prices for the index, stocks and commodities via Yahoo Finance (yfinance).
Every ticker is fetched independently: one failure never breaks the whole run."""
import csv
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

from . import config

log = logging.getLogger("market")
MANUAL_CSV = Path(__file__).resolve().parent.parent / "site" / "data" / "manual_prices.csv"
HISTORY_POINTS = 60
IST = timezone(timedelta(hours=5, minutes=30))


def _summarise(closes, dates=None):
    closes = [float(c) for c in closes]
    if len(closes) < 2:
        raise ValueError("not enough history")
    last, prev = closes[-1], closes[-2]

    def pct_vs(k):
        base = closes[-1 - k] if len(closes) > k else closes[0]
        return round((last / base - 1) * 100, 2) if base else None

    out = {
        "price": round(last, 2),
        "prev_close": round(prev, 2),
        "change": round(last - prev, 2),
        "change_pct": round((last / prev - 1) * 100, 2),
        "chg_1w_pct": pct_vs(5),
        "chg_1m_pct": pct_vs(21),
        "high_52w": round(max(closes[-252:]), 2),
        "low_52w": round(min(closes[-252:]), 2),
        "history": [round(c, 2) for c in closes[-HISTORY_POINTS:]],
    }
    if dates:
        out["dates"] = dates[-HISTORY_POINTS:]
        out["as_of"] = dates[-1]
    return out


def _yahoo(symbol):
    import yfinance as yf  # imported lazily so --demo works without it
    df = yf.Ticker(symbol).history(period="1y", interval="1d", auto_adjust=False)
    df = df.dropna(subset=["Close"])
    dates = [d.strftime("%Y-%m-%d") for d in df.index]
    out = _summarise(df["Close"].tolist(), dates)
    # Before the NSE close (15:30 IST) the newest daily bar is partial, so label it as live, not a close.
    now = datetime.now(IST)
    out["live"] = bool(symbol.endswith((".NS", "^CNXFMCG", "^NSEI")) or symbol.startswith("^")) \
        and dates[-1] == now.strftime("%Y-%m-%d") and (now.hour, now.minute) < (15, 30)
    return out


def _manual(key):
    """Reads data/manual_prices.csv with columns: date,key,price  (ISO dates)."""
    if not MANUAL_CSV.exists():
        raise ValueError("no manual_prices.csv")
    rows = []
    with MANUAL_CSV.open() as f:
        for r in csv.DictReader(f):
            if r.get("key") == key and r.get("price"):
                rows.append((r["date"], float(r["price"])))
    rows.sort()
    if len(rows) < 2:
        raise ValueError(f"need at least 2 manual rows for {key}")
    return _summarise([p for _, p in rows], [d for d, _ in rows])


def fetch_index():
    out = {}
    for tag, spec in (("index", config.INDEX), ("benchmark", config.BENCHMARK)):
        try:
            out[tag] = {"name": spec["name"], "symbol": spec["symbol"], **_yahoo(spec["symbol"])}
        except Exception as e:
            log.warning("%s failed: %s", spec["symbol"], e)
            out[tag] = None
    return out


def fetch_stocks():
    res = []
    for s in config.STOCKS:
        try:
            d = _yahoo(s["symbol"])
            res.append({"symbol": s["symbol"], "name": s["name"], "group": s["group"], **d})
        except Exception as e:
            log.warning("%s failed: %s", s["symbol"], e)
    return res


def fetch_commodities():
    res = []
    for c in config.COMMODITIES:
        data, source = None, None
        for sym in c["symbols"]:
            try:
                data, source = _yahoo(sym), f"Yahoo Finance ({sym})"
                break
            except Exception as e:
                log.warning("%s (%s) failed: %s", c["key"], sym, e)
        if data is None:
            try:
                data, source = _manual(c["key"]), "Manual entry"
            except Exception as e:
                log.info("%s unavailable: %s", c["key"], e)
        item = {"key": c["key"], "name": c["name"], "unit": c["unit"], "exposure": c["exposure"]}
        if data:
            item.update(data, source=source, available=True)
        else:
            item.update(available=False, source="No source configured")
        res.append(item)
    return res

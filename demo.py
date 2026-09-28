"""Synthetic data so you can preview the site with no internet. NOT real prices."""
import random
from datetime import datetime, timedelta, timezone

from . import config
from .fetch_market import _summarise


def _walk(start, vol, n=120, seed=0):
    rnd = random.Random(seed)
    xs, v = [], start
    for _ in range(n):
        v *= 1 + rnd.gauss(0.0002, vol)
        xs.append(v)
    return xs


def _dates(n=120):
    d, out = datetime.now(timezone.utc).date(), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= timedelta(days=1)
    return out[::-1]


def build():
    dates = _dates()
    idx = {"name": config.INDEX["name"], "symbol": config.INDEX["symbol"], **_summarise(_walk(54000, .008, seed=1), dates)}
    bench = {"name": config.BENCHMARK["name"], "symbol": config.BENCHMARK["symbol"], **_summarise(_walk(25000, .007, seed=2), dates)}
    stocks = []
    for i, s in enumerate(config.STOCKS):
        vol = .012 if s["group"] == "FMCG" else .025
        stocks.append({"symbol": s["symbol"], "name": s["name"], "group": s["group"],
                       **_summarise(_walk(random.Random(i).uniform(150, 2800), vol, seed=10 + i), dates)})
    comms = []
    starts = {"brent": 72, "wti": 68, "sugar": 17, "coffee": 310, "palm": 4300, "soyoil": 48, "wheat": 540,
              "cocoa": 8200, "cotton": 68, "milk": 17.5, "usdinr": 86, "hdpe": None}
    for i, c in enumerate(config.COMMODITIES):
        item = {"key": c["key"], "name": c["name"], "unit": c["unit"], "exposure": c["exposure"]}
        if starts[c["key"]]:
            item.update(_summarise(_walk(starts[c["key"]], .015, seed=50 + i), dates), source="Demo data", available=True)
        else:
            item.update(available=False, source="No source configured")
        comms.append(item)
    now = datetime.now(timezone.utc)
    news = [
        {"title": "Demo headline: FMCG volume growth improves as rural demand recovers", "link": "#", "source": "Demo", "tags": ["FMCG sector"]},
        {"title": "Demo headline: Swiggy expands Instamart dark stores to 20 more cities", "link": "#", "source": "Demo", "tags": ["Swiggy", "Quick commerce"]},
        {"title": "Demo headline: Palm oil prices firm on weaker output outlook", "link": "#", "source": "Demo", "tags": ["Commodities"]},
        {"title": "Demo headline: Nykaa says beauty category growth stays in double digits", "link": "#", "source": "Demo", "tags": ["Nykaa (FSN E-Commerce)"]},
        {"title": "Demo headline: Eternal's Blinkit crosses new order milestone", "link": "#", "source": "Demo", "tags": ["Eternal (Zomato)", "Quick commerce"]},
    ]
    for i, n in enumerate(news):
        n["published"] = (now - timedelta(hours=2 * i + 1)).isoformat(timespec="minutes")
    return {"index": idx, "benchmark": bench, "stocks": stocks, "commodities": comms, "news": news}

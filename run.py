"""Daily entry point:  python -m engine.run   (add --demo to use synthetic data)"""
import argparse
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

from . import report

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "site" / "data"
IST = timezone(timedelta(hours=5, minutes=30))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="synthetic data, no network")
    ap.add_argument("--no-llm", action="store_true", help="skip the optional Claude-written report")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if args.demo:
        from . import demo
        data = demo.build()
        data["demo"] = True
    else:
        from . import fetch_market, fetch_news
        data = fetch_market.fetch_index()
        data["stocks"] = fetch_market.fetch_stocks()
        data["commodities"] = fetch_market.fetch_commodities()
        data["news"] = fetch_news.fetch_news()

    if args.no_llm:
        data["report"] = report.rule_based(data)
    else:
        data["report"] = report.build(data)

    now = datetime.now(IST)
    as_of = (data.get("index") or {}).get("as_of") or now.date().isoformat()
    data["as_of"] = as_of
    data["generated_at"] = now.isoformat(timespec="minutes")
    data["snapshot"] = f"Data available up to {now.strftime('%H:%M')} IST"
    data["health"] = {
        "stocks_ok": len(data["stocks"]),
        "commodities_ok": sum(1 for c in data["commodities"] if c.get("available")),
        "commodities_total": len(data["commodities"]),
        "news_items": len(data["news"]),
    }

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "archive").mkdir(exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    (DATA / "latest.json").write_text(payload, encoding="utf-8")
    if not args.demo:
        (DATA / "archive" / f"{as_of}.json").write_text(payload, encoding="utf-8")
        dates = sorted(p.stem for p in (DATA / "archive").glob("*.json") if p.stem != "index")
        (DATA / "archive" / "index.json").write_text(json.dumps(dates[::-1]), encoding="utf-8")
    logging.info("Wrote %s  (%s)", DATA / "latest.json", data["health"])


if __name__ == "__main__":
    main()

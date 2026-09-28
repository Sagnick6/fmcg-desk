"""Builds the pre-generated daily report.
1) Always: a rule-based note computed purely from the data (deterministic, no hallucination).
2) Optional: if ANTHROPIC_API_KEY is set, Claude rewrites it as an analyst note, strictly from the supplied data."""
import json
import logging
import os

log = logging.getLogger("report")
COMMODITY_ALERT_PCT = 2.0


def _sign(x):
    return "up" if x >= 0 else "down"


def rule_based(data):
    idx, bench = data.get("index"), data.get("benchmark")
    stocks, comms, news = data["stocks"], data["commodities"], data["news"]
    sections = []

    # 1. Index
    if idx:
        verb = "was trading" if idx.get("live") else "closed"
        txt = (f"Nifty FMCG {verb} {_sign(idx['change_pct'])} {abs(idx['change_pct']):.2f}% at {idx['price']:,.2f} "
               f"(1-week {idx['chg_1w_pct']:+.1f}%, 1-month {idx['chg_1m_pct']:+.1f}%).")
        if bench:
            rel = idx["change_pct"] - bench["change_pct"]
            txt += (f" The Nifty 50 was {_sign(bench['change_pct'])} {abs(bench['change_pct']):.2f}%, so staples "
                    f"{'outperformed' if rel >= 0 else 'lagged'} the market by {abs(rel):.2f} percentage points.")
        sections.append({"title": "Index", "body": txt})
        headline = (f"Nifty FMCG {idx['change_pct']:+.2f}% at {idx['price']:,.0f}")
    else:
        headline = "Daily desk note"
        sections.append({"title": "Index", "body": "Nifty FMCG data was unavailable in this run."})

    # 2. Movers
    def movers(group):
        g = sorted([s for s in stocks if s["group"] == group], key=lambda s: s["change_pct"], reverse=True)
        return g
    parts = []
    for group, label in (("FMCG", "Staples"), ("Internet", "Internet names")):
        g = movers(group)
        if len(g) >= 2:
            up = sum(1 for s in g if s["change_pct"] > 0)
            best, worst = g[0], g[-1]
            parts.append(f"{label}: {up} of {len(g)} advanced. Best was {best['name']} ({best['change_pct']:+.2f}%), "
                         f"weakest {worst['name']} ({worst['change_pct']:+.2f}%).")
    if parts:
        sections.append({"title": "Stocks", "body": " ".join(parts)})

    # 3. Input costs
    avail = [c for c in comms if c.get("available")]
    alerts = [c for c in avail if abs(c["change_pct"]) >= COMMODITY_ALERT_PCT]
    if alerts:
        lines = []
        for c in sorted(alerts, key=lambda c: -abs(c["change_pct"])):
            direction = "rose" if c["change_pct"] > 0 else "fell"
            read = "a cost headwind" if c["change_pct"] > 0 and c["key"] != "usdinr" else "a cost tailwind"
            if c["key"] == "usdinr":
                read = "pressure on imported inputs" if c["change_pct"] > 0 else "relief on imported inputs"
            lines.append(f"{c['name']} {direction} {abs(c['change_pct']):.1f}% to {c['price']:,.2f} {c['unit']} ({read} for {c['exposure']}).")
        body = " ".join(lines)
    elif avail:
        body = "No tracked input moved more than 2% on the day."
    else:
        body = "Commodity data was unavailable in this run."
    missing = [c["name"] for c in comms if not c.get("available")]
    if missing:
        body += f" Not available today: {', '.join(missing)}."
    sections.append({"title": "Input costs", "body": body})

    # 4. News
    tagged = [n for n in news if n["tags"]][:6]
    if tagged:
        body = " ".join(f"{n['title']} ({n['source']})." if not n['title'].endswith('.') else f"{n['title']} ({n['source']})"
                        for n in tagged[:5])
        sections.append({"title": "In the news", "body": body})

    return {"headline": headline, "sections": sections, "generated_by": "rules"}


def _llm_prompt(data, base):
    slim = {
        "index": data.get("index") and {k: data["index"][k] for k in ("name", "price", "change_pct", "chg_1w_pct", "chg_1m_pct")},
        "benchmark": data.get("benchmark") and {k: data["benchmark"][k] for k in ("name", "price", "change_pct")},
        "stocks": [{k: s[k] for k in ("name", "group", "price", "change_pct", "chg_1w_pct", "chg_1m_pct")} for s in data["stocks"]],
        "commodities": [{k: c[k] for k in ("name", "unit", "price", "change_pct", "chg_1w_pct", "exposure")}
                        for c in data["commodities"] if c.get("available")],
        "headlines": [{"title": n["title"], "source": n["source"], "tags": n["tags"]} for n in data["news"][:40]],
    }
    return (
        "You are an equity research analyst covering Indian consumer staples and internet/consumer-tech.\n"
        "Write today's desk note from ONLY the JSON below. Do not add numbers, events or causes that are not in it. "
        "If a cause for a move is not in the headlines, say the cause is not evident from today's data.\n"
        "Format: 4 short sections with '## ' headings: Market, Stocks, Input costs, News read-through. "
        "Plain prose, under 350 words total, no bullet points, no investment recommendations.\n\n"
        f"DATA:\n{json.dumps(slim, ensure_ascii=False)}"
    )


def llm_report(data, base):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    import requests
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": model, "max_tokens": 1200, "messages": [{"role": "user", "content": _llm_prompt(data, base)}]},
        timeout=90,
    )
    r.raise_for_status()
    text = "".join(b.get("text", "") for b in r.json()["content"] if b.get("type") == "text").strip()
    sections, cur = [], None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = {"title": line[3:].strip(), "body": ""}
            sections.append(cur)
        elif cur is not None and line.strip():
            cur["body"] += (" " if cur["body"] else "") + line.strip()
    if not sections:
        raise ValueError("LLM returned no sections")
    return {"headline": base["headline"], "sections": sections, "generated_by": f"{model} (from rule-based data)"}


def build(data):
    base = rule_based(data)
    try:
        return llm_report(data, base) or base
    except Exception as e:
        log.warning("LLM report failed, using rule-based: %s", e)
        return base

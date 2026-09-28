# Staples & Screens: daily desk for Indian FMCG and internet stocks

A Python engine collects prices and headlines once or twice a day, writes one JSON file, and a static page renders it.
There is no server to run or pay for.

```
engine/            data collection + report writer (Python)
site/index.html    the website (reads data/latest.json)
site/data/         latest.json, archive/<date>.json, manual_prices.csv
.github/workflows/daily.yml   the scheduler (GitHub Actions + GitHub Pages)
```

## Try it locally
```bash
pip install -r requirements.txt
python -m engine.run --demo      # synthetic data, no internet needed
python -m engine.run             # real data
cd site && python -m http.server # open http://localhost:8000
```

## Put it online (free)
1. Create a GitHub repo and push this folder.
2. Settings > Pages > Source: **GitHub Actions**.
3. Optional: Settings > Secrets > add `ANTHROPIC_API_KEY` so Claude rewrites the report as an analyst note.
   Without it you get the rule-based report, which uses only the numbers and headlines.
4. Actions tab > *Daily update* > Run workflow. After that it runs Mon-Fri at 09:30 IST and shows everything available up to that time (previous close plus live opening moves, overnight commodities, fresh news).

## What it collects
| Data | Source | Notes |
|---|---|---|
| Nifty FMCG, Nifty 50, 18 stocks | Yahoo Finance via `yfinance` | Delayed, unofficial. Fine for a dashboard, not for trading. |
| Brent, WTI, sugar, coffee, wheat, cocoa, cotton, soybean oil, milk, USD/INR | Yahoo Finance futures | Front-month contract, so a roll can show as a jump. |
| Palm oil | Yahoo `FCPO=F`, then `manual_prices.csv` | Yahoo's Bursa coverage is unreliable. Check it on the first run. |
| HDPE / plastic | `manual_prices.csv` only | No free daily feed exists. See below. |
| News | Google News RSS + ET, Moneycontrol, Business Standard, Mint RSS | Deduplicated, tagged by company and theme, last 36 hours. |

### HDPE and any other missing series
Add rows to `site/data/manual_prices.csv` (at least two dates per key):
```
date,key,price
2026-09-25,hdpe,101.5
2026-09-26,hdpe,102.0
```
For automation, write a small function in `engine/fetch_market.py` for whichever source you subscribe to
(ICIS, Platts, ChemAnalyst, an exchange page) and call it in place of `_manual`.

## Customise
Everything is in `engine/config.py`: add a ticker, add a commodity, change news queries, change how far back news goes.

## Things to know
- Scrapers break. Yahoo and RSS layouts change. Each ticker and feed fails on its own; the footer shows how many succeeded
  in the last run, and the workflow logs show which ones failed.
- Yahoo prices are for personal use. If this becomes a public or commercial product, switch to a licensed data vendor.
- NSE holidays produce no new bar, so the page simply shows the previous close.

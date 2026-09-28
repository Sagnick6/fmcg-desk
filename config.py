"""Everything you might want to customise lives here: tickers, commodities, news queries."""

INDEX = {"symbol": "^CNXFMCG", "name": "Nifty FMCG"}
BENCHMARK = {"symbol": "^NSEI", "name": "Nifty 50"}

# group: "FMCG" or "Internet". aliases are used to tag news headlines.
STOCKS = [
    # ---- FMCG / Consumer staples
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever", "group": "FMCG", "aliases": ["hindustan unilever", "hul"]},
    {"symbol": "ITC.NS", "name": "ITC", "group": "FMCG", "aliases": ["itc"]},
    {"symbol": "NESTLEIND.NS", "name": "Nestle India", "group": "FMCG", "aliases": ["nestle india", "nestlé india"]},
    {"symbol": "BRITANNIA.NS", "name": "Britannia", "group": "FMCG", "aliases": ["britannia"]},
    {"symbol": "TATACONSUM.NS", "name": "Tata Consumer", "group": "FMCG", "aliases": ["tata consumer"]},
    {"symbol": "DABUR.NS", "name": "Dabur", "group": "FMCG", "aliases": ["dabur"]},
    {"symbol": "GODREJCP.NS", "name": "Godrej Consumer", "group": "FMCG", "aliases": ["godrej consumer", "gcpl"]},
    {"symbol": "MARICO.NS", "name": "Marico", "group": "FMCG", "aliases": ["marico"]},
    {"symbol": "COLPAL.NS", "name": "Colgate-Palmolive India", "group": "FMCG", "aliases": ["colgate"]},
    {"symbol": "VBL.NS", "name": "Varun Beverages", "group": "FMCG", "aliases": ["varun beverages"]},
    {"symbol": "EMAMILTD.NS", "name": "Emami", "group": "FMCG", "aliases": ["emami"]},
    # ---- Internet / new-age consumer
    {"symbol": "ETERNAL.NS", "name": "Eternal (Zomato)", "group": "Internet", "aliases": ["eternal", "zomato", "blinkit"]},
    {"symbol": "SWIGGY.NS", "name": "Swiggy", "group": "Internet", "aliases": ["swiggy", "instamart"]},
    {"symbol": "NYKAA.NS", "name": "Nykaa (FSN E-Commerce)", "group": "Internet", "aliases": ["nykaa", "fsn e-commerce"]},
    {"symbol": "PAYTM.NS", "name": "Paytm", "group": "Internet", "aliases": ["paytm", "one97"]},
    {"symbol": "POLICYBZR.NS", "name": "PB Fintech", "group": "Internet", "aliases": ["pb fintech", "policybazaar"]},
    {"symbol": "NAUKRI.NS", "name": "Info Edge", "group": "Internet", "aliases": ["info edge", "naukri"]},
    {"symbol": "BRAINBEES.NS", "name": "FirstCry (Brainbees)", "group": "Internet", "aliases": ["firstcry", "brainbees"]},
    # Add more, e.g. {"symbol": "LENSKART.NS", ...}. Check the ticker on finance.yahoo.com first.
]

# symbols: tried in order. If all fail, the engine falls back to data/manual_prices.csv (key matches).
# exposure: which listed names are sensitive to this input; used by the auto-written report.
COMMODITIES = [
    {"key": "brent", "name": "Brent crude", "symbols": ["BZ=F"], "unit": "USD/bbl",
     "exposure": "packaging, freight and polymer costs across FMCG; delivery cost for quick commerce"},
    {"key": "wti", "name": "WTI crude", "symbols": ["CL=F"], "unit": "USD/bbl",
     "exposure": "global crude benchmark"},
    {"key": "sugar", "name": "Sugar #11", "symbols": ["SB=F"], "unit": "US c/lb",
     "exposure": "Britannia, Nestle India, Tata Consumer, Varun Beverages"},
    {"key": "coffee", "name": "Coffee (Arabica)", "symbols": ["KC=F"], "unit": "US c/lb",
     "exposure": "Nestle India, Tata Consumer (Tata Coffee)"},
    {"key": "palm", "name": "Palm oil (Bursa)", "symbols": ["FCPO=F"], "unit": "MYR/t",
     "exposure": "HUL, Britannia, Nestle India, Godrej Consumer, ITC (soaps, biscuits, noodles)"},
    {"key": "soyoil", "name": "Soybean oil", "symbols": ["ZL=F"], "unit": "US c/lb",
     "exposure": "edible oils, Marico"},
    {"key": "wheat", "name": "Wheat", "symbols": ["ZW=F"], "unit": "US c/bu",
     "exposure": "Britannia, ITC (Aashirvaad, Sunfeast), Nestle India"},
    {"key": "cocoa", "name": "Cocoa", "symbols": ["CC=F"], "unit": "USD/t",
     "exposure": "Nestle India, Britannia, confectionery"},
    {"key": "cotton", "name": "Cotton", "symbols": ["CT=F"], "unit": "US c/lb",
     "exposure": "personal-care and hygiene products"},
    {"key": "milk", "name": "Class III milk", "symbols": ["DC=F"], "unit": "USD/cwt",
     "exposure": "Nestle India, Britannia (dairy); global dairy cost proxy"},
    {"key": "usdinr", "name": "USD/INR", "symbols": ["INR=X"], "unit": "INR",
     "exposure": "imported inputs (palm, crude-linked packaging) get costlier when INR weakens"},
    # No reliable free daily feed for HDPE. Fill data/manual_prices.csv (see README) or wire a source in fetch_market.py.
    {"key": "hdpe", "name": "HDPE (plastic)", "symbols": [], "unit": "INR/kg",
     "exposure": "packaging across FMCG (bottles, sachets, films)"},
]

NEWS_HOURS = 36   # keep headlines from the last N hours
NEWS_MAX = 90

# Google News RSS queries (one search each). Company queries are built from STOCKS automatically.
SECTOR_QUERIES = [
    "India FMCG demand", "India FMCG volume growth", "quick commerce India",
    "India rural consumption FMCG", "India food inflation", "GST FMCG India",
    "palm oil price India", "sugar price India", "coffee prices", "Brent crude price",
    "HDPE polymer prices India", "Nifty FMCG",
]

# Direct publisher feeds (filtered by KEYWORDS below because they cover everything).
DIRECT_FEEDS = [
    ("Economic Times", "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms"),
    ("Moneycontrol", "https://www.moneycontrol.com/rss/business.xml"),
    ("Business Standard", "https://www.business-standard.com/rss/companies-101.xml"),
    ("Livemint", "https://www.livemint.com/rss/companies"),
]
KEYWORDS = ["fmcg", "consumer", "quick commerce", "palm oil", "sugar", "coffee", "brent", "crude",
            "packaging", "edible oil", "rural demand", "food delivery", "e-commerce"]

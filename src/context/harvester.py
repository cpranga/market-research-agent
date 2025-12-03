"""
Context harvester for external data (news, etc.).
Currently supports Finnhub news API.
"""
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict
import requests
import yfinance as yf
from dateutil import parser as dateparser

from core.config import Config
from core.db import execute
from core.logging import info, warning, error, debug


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_news_item(item: Dict) -> Dict:
    # Finnhub returns epoch seconds in "datetime"
    ts = datetime.fromtimestamp(item.get("datetime", 0), tz=timezone.utc)
    title = item.get("headline", "")
    summary = item.get("summary", "")
    url = item.get("url", "")
    source = item.get("source", "")
    category = item.get("category", "")
    hash_value = _hash_text("{}|{}|{}".format(title, summary, url))
    return {
        "symbol": None,
        "published_at": ts,
        "title": title,
        "summary": summary,
        "hash": hash_value,
        "source": source or category or "finnhub",
        "inserted_at": datetime.now(timezone.utc),
    }


def fetch_news() -> List[Dict]:
    """
    Fetch general market news from Finnhub.
    """
    if not Config.FINNHUB_API_KEY:
        raise RuntimeError("FINNHUB_API_KEY is not configured")
    params = {
        "token": Config.FINNHUB_API_KEY,
        "category": Config.NEWS_CATEGORY or "general",
    }
    resp = requests.get("https://finnhub.io/api/v1/news", params=params, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError("Finnhub news returned {}: {}".format(resp.status_code, resp.text[:200]))
    try:
        data = resp.json()
    except ValueError as exc:
        raise RuntimeError("Invalid JSON from Finnhub news: {}".format(exc))
    return [_normalize_news_item(item) for item in data]


def fetch_company_news(symbol: str, start: datetime, end: datetime) -> List[Dict]:
    """
    Fetch symbol-specific news from Finnhub between dates (inclusive).
    """
    if not Config.FINNHUB_API_KEY:
        raise RuntimeError("FINNHUB_API_KEY is not configured")
    params = {
        "token": Config.FINNHUB_API_KEY,
        "symbol": symbol,
        "from": start.date().isoformat(),
        "to": end.date().isoformat(),
    }
    resp = requests.get("https://finnhub.io/api/v1/company-news", params=params, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError("Finnhub company news returned {}: {}".format(resp.status_code, resp.text[:200]))
    try:
        data = resp.json()
    except ValueError as exc:
        raise RuntimeError("Invalid JSON from Finnhub company news: {}".format(exc))
    items = []
    for item in data:
        normalized = _normalize_news_item(item)
        # attach symbol from related if provided, otherwise use requested symbol
        related = item.get("related")
        normalized["symbol"] = related or symbol
        items.append(normalized)
    return items


async def store_news(items: List[Dict]) -> int:
    """
    Insert news rows with upsert on hash to avoid duplicates.
    """
    if not items:
        return 0
    written = 0
    for item in items:
        try:
            await execute(
                """
                INSERT INTO context_news (symbol, published_at, title, summary, hash, source, inserted_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (hash) DO NOTHING
                """,
                (
                    item["symbol"],
                    item["published_at"],
                    item["title"],
                    item["summary"],
                    item["hash"],
                    item["source"],
                    item["inserted_at"],
                )
            )
            written += 1
        except Exception as exc:
            warning("Failed to upsert news item {}: {}".format(item.get("hash"), exc))
    return written


async def harvest_news():
    """
    Fetch and persist news if enabled.
    """
    if not Config.ENABLE_NEWS_HARVEST:
        debug("News harvest disabled by config.")
        return 0
    try:
        items = fetch_news()
        written_general = await store_news(items)
        # Fetch company news for each symbol over lookback window
        lookback = timedelta(days=Config.NEWS_LOOKBACK_DAYS)
        start = datetime.now(timezone.utc) - lookback
        end = datetime.now(timezone.utc)
        written_company = 0
        for sym in Config.SYMBOLS:
            try:
                company_items = fetch_company_news(sym, start, end)
                written_company += await store_news(company_items)
            except Exception as exc:
                warning("Company news harvest failed for {}: {}".format(sym, exc))

        total = written_general + written_company
        info("Harvested {} news items.".format(total))
        return total
    except Exception as exc:
        error("News harvest failed: {}".format(exc))
        return 0


# -----------------------------
# Company profile & financials
# -----------------------------
async def store_company_profile(profile: Dict):
    if not profile:
        return
    ipo_raw = profile.get("ipo_date")
    ipo_date = None
    if ipo_raw:
        try:
            ipo_date = dateparser.parse(str(ipo_raw)).date()
        except Exception:
            ipo_date = None
    await execute(
        """
        INSERT INTO context_company (symbol, name, industry, exchange, market_cap, ipo_date, currency, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
        ON CONFLICT (symbol) DO UPDATE SET
            name = EXCLUDED.name,
            industry = EXCLUDED.industry,
            exchange = EXCLUDED.exchange,
            market_cap = EXCLUDED.market_cap,
            ipo_date = EXCLUDED.ipo_date,
            currency = EXCLUDED.currency,
            updated_at = NOW()
        """,
        (
            profile.get("symbol"),
            profile.get("name"),
            profile.get("industry"),
            profile.get("exchange"),
            profile.get("market_cap"),
            ipo_date,
            profile.get("currency"),
        )
    )


async def store_financials(fin: Dict):
    if not fin:
        return
    await execute(
        """
        INSERT INTO context_financials (symbol, as_of, beta, high_52w, low_52w, avg_vol_10d, sales_per_share, net_margin)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (symbol, as_of) DO NOTHING
        """,
        (
            fin.get("symbol"),
            fin.get("as_of"),
            fin.get("beta"),
            fin.get("high_52w"),
            fin.get("low_52w"),
            fin.get("avg_vol_10d"),
            fin.get("sales_per_share"),
            fin.get("net_margin"),
        )
    )


def fetch_profile_finnhub(symbol: str) -> Dict:
    if not Config.FINNHUB_API_KEY:
        raise RuntimeError("FINNHUB_API_KEY is not configured")
    params = {
        "token": Config.FINNHUB_API_KEY,
        "symbol": symbol,
    }
    resp = requests.get("https://finnhub.io/api/v1/stock/profile2", params=params, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError("Finnhub profile returned {}: {}".format(resp.status_code, resp.text[:200]))
    data = resp.json()
    if not data or not data.get("ticker"):
        raise RuntimeError("Finnhub profile missing data for {}".format(symbol))
    return {
        "symbol": data.get("ticker"),
        "name": data.get("name"),
        "industry": data.get("finnhubIndustry"),
        "exchange": data.get("exchange"),
        "market_cap": data.get("marketCapitalization"),
        "ipo_date": data.get("ipo"),
        "currency": data.get("currency"),
    }


def fetch_profile_yf(symbol: str) -> Dict:
    ticker = yf.Ticker(symbol)
    info_obj = ticker.info or {}
    return {
        "symbol": symbol,
        "name": info_obj.get("shortName") or info_obj.get("longName"),
        "industry": info_obj.get("industry"),
        "exchange": info_obj.get("exchange"),
        "market_cap": info_obj.get("marketCap"),
        "ipo_date": info_obj.get("ipoYear"),
        "currency": info_obj.get("currency"),
    }


def fetch_financials_finnhub(symbol: str) -> Dict:
    if not Config.FINNHUB_API_KEY:
        raise RuntimeError("FINNHUB_API_KEY is not configured")
    params = {
        "token": Config.FINNHUB_API_KEY,
        "symbol": symbol,
        "metric": "all",
    }
    resp = requests.get("https://finnhub.io/api/v1/stock/metric", params=params, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError("Finnhub metric returned {}: {}".format(resp.status_code, resp.text[:200]))
    data = resp.json()
    metric = data.get("metric", {}) if isinstance(data, dict) else {}
    return {
        "symbol": symbol,
        "as_of": datetime.now(timezone.utc),
        "beta": metric.get("beta"),
        "high_52w": metric.get("52WeekHigh"),
        "low_52w": metric.get("52WeekLow"),
        "avg_vol_10d": metric.get("10DayAverageTradingVolume"),
        "sales_per_share": metric.get("salesPerShareTTM") or metric.get("salesPerShare"),
        "net_margin": metric.get("netMargin"),
    }


def fetch_financials_yf(symbol: str) -> Dict:
    ticker = yf.Ticker(symbol)
    info_obj = ticker.info or {}
    return {
        "symbol": symbol,
        "as_of": datetime.now(timezone.utc),
        "beta": info_obj.get("beta"),
        "high_52w": info_obj.get("fiftyTwoWeekHigh"),
        "low_52w": info_obj.get("fiftyTwoWeekLow"),
        "avg_vol_10d": info_obj.get("averageDailyVolume10Day"),
        "sales_per_share": info_obj.get("revenuePerShare"),
        "net_margin": info_obj.get("profitMargins"),
    }


async def harvest_company_profiles():
    if not Config.ENABLE_COMPANY_HARVEST:
        debug("Company profile harvest disabled by config.")
        return 0
    written = 0
    for sym in Config.SYMBOLS:
        profile = None
        try:
            profile = fetch_profile_finnhub(sym)
        except Exception as exc:
            warning("Finnhub profile failed for {}: {}. Falling back to yfinance.".format(sym, exc))
            try:
                profile = fetch_profile_yf(sym)
            except Exception as exc2:
                error("Profile fetch failed for {} via yfinance: {}".format(sym, exc2))
        if profile:
            await store_company_profile(profile)
            written += 1
    info("Harvested {} company profiles.".format(written))
    return written


async def harvest_financials():
    if not Config.ENABLE_FINANCIALS_HARVEST:
        debug("Financials harvest disabled by config.")
        return 0
    written = 0
    for sym in Config.SYMBOLS:
        fin = None
        try:
            fin = fetch_financials_finnhub(sym)
        except Exception as exc:
            warning("Finnhub financials failed for {}: {}. Falling back to yfinance.".format(sym, exc))
            try:
                fin = fetch_financials_yf(sym)
            except Exception as exc2:
                error("Financials fetch failed for {} via yfinance: {}".format(sym, exc2))
        if fin:
            await store_financials(fin)
            written += 1
    info("Harvested {} financials snapshots.".format(written))
    return written

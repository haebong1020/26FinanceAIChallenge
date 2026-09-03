"""Fetch and normalize basic financial data for a US-listed ticker."""

from collections.abc import Callable, Mapping
import re
from typing import Any

import pandas as pd
import yfinance as yf


TICKER_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,9}$")


class FinancialDataError(ValueError):
    """Raised when financial data cannot be retrieved for a ticker."""


def _normalize_ticker(ticker: str) -> str:
    """Normalize and validate a ticker symbol."""
    normalized = ticker.strip().upper()
    if not normalized or not TICKER_PATTERN.fullmatch(normalized):
        raise FinancialDataError(
            "Please enter a valid ticker using letters, numbers, '.' or '-'."
        )
    return normalized


def _first_value(data: Mapping[str, Any], *keys: str) -> Any:
    """Return the first non-null value found for the supplied keys."""
    for key in keys:
        value = data.get(key)
        if value is not None:
            return value
    return None


def get_financial_data(
    ticker: str,
    ticker_factory: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    """Return normalized market and financial data for a ticker."""
    normalized_ticker = _normalize_ticker(ticker)
    factory = ticker_factory or yf.Ticker

    try:
        stock = factory(normalized_ticker)
        info = stock.info
    except Exception as exc:
        raise FinancialDataError(
            f"Could not retrieve financial data for {normalized_ticker}. "
            "Please try again later."
        ) from exc

    if not isinstance(info, Mapping) or not info:
        raise FinancialDataError(
            f"No financial data was found for {normalized_ticker}. "
            "Please check the ticker and try again."
        )

    company_name = _first_value(info, "longName", "shortName")
    current_price = _first_value(
        info, "currentPrice", "regularMarketPrice", "previousClose"
    )

    if company_name is None and current_price is None and info.get("marketCap") is None:
        raise FinancialDataError(
            f"No financial data was found for {normalized_ticker}. "
            "Please check the ticker and try again."
        )

    return {
        "ticker": normalized_ticker,
        "company_name": company_name,
        "company_profile": {"sector": info.get("sector")},
        "market_data": {
            "current_price": current_price,
            "market_cap": info.get("marketCap"),
        },
        "valuation": {
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
        },
        "growth": {"revenue_growth": info.get("revenueGrowth")},
        "profitability": {"profit_margin": info.get("profitMargins")},
        "financial_health": {"debt_to_equity": info.get("debtToEquity")},
    }


def ticker_exists(ticker: str) -> bool:
    """Return whether Yahoo Finance exposes recent prices for a ticker."""
    normalized_ticker = _normalize_ticker(ticker)
    try:
        history = yf.download(
            tickers=[normalized_ticker],
            period="5d",
            auto_adjust=True,
            progress=False,
            timeout=8,
        )
    except Exception:
        return False
    return isinstance(history, pd.DataFrame) and not history.empty


def get_historical_prices(
    tickers: list[str],
    period: str = "1y",
    downloader: Callable[..., pd.DataFrame] | None = None,
) -> pd.DataFrame:
    """Return adjusted closing prices for multiple tickers."""
    normalized_tickers = [_normalize_ticker(ticker) for ticker in tickers]
    if len(normalized_tickers) < 2:
        raise FinancialDataError("At least two tickers are required for correlation.")

    download = downloader or yf.download
    try:
        history = download(
            tickers=normalized_tickers,
            period=period,
            auto_adjust=True,
            progress=False,
            timeout=15,
        )
    except Exception as exc:
        raise FinancialDataError(
            "Could not retrieve historical prices. Please try again later."
        ) from exc

    if not isinstance(history, pd.DataFrame) or history.empty:
        raise FinancialDataError("No historical prices were found for this portfolio.")

    if isinstance(history.columns, pd.MultiIndex):
        try:
            prices = history["Close"]
        except KeyError as exc:
            raise FinancialDataError("Historical closing prices were not available.") from exc
    elif "Close" in history.columns and len(normalized_tickers) == 1:
        prices = history[["Close"]].rename(columns={"Close": normalized_tickers[0]})
    else:
        raise FinancialDataError("Historical closing prices were not available.")

    prices = prices.reindex(columns=normalized_tickers).dropna(how="all")
    if prices.empty or prices.count().min() < 2:
        raise FinancialDataError("Not enough price history was available for correlation.")
    return prices

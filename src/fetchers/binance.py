import requests
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone


BASE_URL = "https://fapi.binance.com"


def get_premium_index(symbol: str = "BTCUSDT") -> Optional[Dict]:
    """获取资金费率与标记价格相关数据。"""
    try:
        url = f"{BASE_URL}/fapi/v1/premiumIndex"
        params = {"symbol": symbol}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data
    except Exception as e:
        print(f"获取 premiumIndex 失败 [{symbol}]: {e}")
        return None


def get_open_interest(symbol: str = "BTCUSDT") -> Optional[float]:
    """获取当前未平仓合约数量（张）。"""
    try:
        url = f"{BASE_URL}/fapi/v1/openInterest"
        params = {"symbol": symbol}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("openInterest", 0))
    except Exception as e:
        print(f"获取 openInterest 失败 [{symbol}]: {e}")
        return None


def get_ticker_price(symbol: str = "BTCUSDT") -> Optional[float]:
    """获取最新价格。"""
    try:
        url = f"{BASE_URL}/fapi/v1/ticker/price"
        params = {"symbol": symbol}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("price", 0))
    except Exception as e:
        print(f"获取价格失败 [{symbol}]: {e}")
        return None


def get_klines(symbol: str, interval: str = "1h", limit: int = 5) -> Optional[list]:
    """获取K线，用于计算价格变化。"""
    try:
        url = f"{BASE_URL}/fapi/v1/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"获取K线失败 [{symbol}]: {e}")
        return None


def fetch_symbol_data(symbol: str) -> Optional[Dict]:
    """
    聚合获取单个交易对的关键数据。
    返回结构:
    {
        "symbol": str,
        "funding_rate": float,          # 当前资金费率（小数）
        "next_funding_time": int,
        "mark_price": float,
        "open_interest": float,         # 张数
        "price": float,
        "price_change_1h": float,       # 小数
        "price_change_4h": float,
        "timestamp": str
    }
    """
    premium = get_premium_index(symbol)
    oi = get_open_interest(symbol)
    price = get_ticker_price(symbol)
    klines_1h = get_klines(symbol, "1h", 5)
    klines_4h = get_klines(symbol, "4h", 3)

    if not premium or oi is None or price is None:
        return None

    funding_rate = float(premium.get("lastFundingRate", 0))
    mark_price = float(premium.get("markPrice", price))
    next_funding = int(premium.get("nextFundingTime", 0))

    # 计算价格变化
    price_change_1h = 0.0
    price_change_4h = 0.0

    if klines_1h and len(klines_1h) >= 2:
        # kline: [open_time, open, high, low, close, ...]
        close_now = float(klines_1h[-1][4])
        close_1h_ago = float(klines_1h[-2][4])
        if close_1h_ago > 0:
            price_change_1h = (close_now - close_1h_ago) / close_1h_ago

    if klines_4h and len(klines_4h) >= 2:
        close_now = float(klines_4h[-1][4])
        close_4h_ago = float(klines_4h[-2][4])
        if close_4h_ago > 0:
            price_change_4h = (close_now - close_4h_ago) / close_4h_ago

    return {
        "symbol": symbol,
        "funding_rate": funding_rate,
        "next_funding_time": next_funding,
        "mark_price": mark_price,
        "open_interest": oi,
        "price": price,
        "price_change_1h": price_change_1h,
        "price_change_4h": price_change_4h,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

import requests
from typing import Dict, Optional
from datetime import datetime, timezone


BASE_URL = "https://api.bybit.com"


def get_ticker(symbol: str = "BTCUSDT") -> Optional[Dict]:
    """获取 Bybit linear 永续的 ticker（含资金费率、OI、价格等）。"""
    try:
        url = f"{BASE_URL}/v5/market/tickers"
        params = {
            "category": "linear",
            "symbol": symbol,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("retCode") != 0:
            print(f"Bybit ticker 错误 [{symbol}]: {data.get('retMsg')}")
            return None
        items = data.get("result", {}).get("list", [])
        if not items:
            return None
        return items[0]
    except Exception as e:
        print(f"获取 Bybit ticker 失败 [{symbol}]: {e}")
        return None


def get_klines(symbol: str, interval: str = "60", limit: int = 5) -> Optional[list]:
    """获取 K 线。interval: 60=1h, 240=4h。"""
    try:
        url = f"{BASE_URL}/v5/market/kline"
        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("retCode") != 0:
            print(f"Bybit kline 错误 [{symbol}]: {data.get('retMsg')}")
            return None
        # 返回格式: [[start, open, high, low, close, volume, turnover], ...] 时间倒序
        return data.get("result", {}).get("list", [])
    except Exception as e:
        print(f"获取 Bybit kline 失败 [{symbol}]: {e}")
        return None


def fetch_symbol_data(symbol: str) -> Optional[Dict]:
    """
    聚合获取单个交易对的关键数据（Bybit）。
    返回结构与原 Binance 版本保持一致，方便规则引擎直接使用。
    """
    ticker = get_ticker(symbol)
    if not ticker:
        return None

    try:
        funding_rate = float(ticker.get("fundingRate", 0) or 0)
        mark_price = float(ticker.get("markPrice", 0) or 0)
        last_price = float(ticker.get("lastPrice", 0) or mark_price)
        open_interest = float(ticker.get("openInterest", 0) or 0)
        next_funding = int(ticker.get("nextFundingTime", 0) or 0)
    except (TypeError, ValueError) as e:
        print(f"解析 ticker 数值失败 [{symbol}]: {e}")
        return None

    # 价格变化（用 K 线计算）
    price_change_1h = 0.0
    price_change_4h = 0.0

    klines_1h = get_klines(symbol, interval="60", limit=3)
    if klines_1h and len(klines_1h) >= 2:
        # Bybit kline 是倒序，[0] 是最新
        # 格式: [startTime, open, high, low, close, ...]
        try:
            close_now = float(klines_1h[0][4])
            close_1h_ago = float(klines_1h[1][4])
            if close_1h_ago > 0:
                price_change_1h = (close_now - close_1h_ago) / close_1h_ago
        except (IndexError, ValueError, TypeError):
            pass

    klines_4h = get_klines(symbol, interval="240", limit=3)
    if klines_4h and len(klines_4h) >= 2:
        try:
            close_now = float(klines_4h[0][4])
            close_4h_ago = float(klines_4h[1][4])
            if close_4h_ago > 0:
                price_change_4h = (close_now - close_4h_ago) / close_4h_ago
        except (IndexError, ValueError, TypeError):
            pass

    return {
        "symbol": symbol,
        "funding_rate": funding_rate,
        "next_funding_time": next_funding,
        "mark_price": mark_price,
        "open_interest": open_interest,
        "price": last_price,
        "price_change_1h": price_change_1h,
        "price_change_4h": price_change_4h,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

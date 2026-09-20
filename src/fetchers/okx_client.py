import requests
from typing import Dict, Any, Optional, List

BASE_URL = "https://www.okx.com"

HEADERS = {
    "User-Agent": "Critical-Funding-OI-Monitor/1.0",
    "Accept": "application/json",
}

def _get(path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != "0":
        raise RuntimeError(f"OKX API error: {data.get('msg')} | {data}")
    return data

def get_funding_rate(inst_id: str) -> Dict[str, Any]:
    """获取当前资金费率"""
    data = _get("/api/v5/public/funding-rate", {"instId": inst_id})
    return data["data"][0] if data.get("data") else {}

def get_open_interest(inst_id: str) -> Dict[str, Any]:
    """获取持仓量"""
    data = _get("/api/v5/public/open-interest", {"instId": inst_id})
    return data["data"][0] if data.get("data") else {}

def get_ticker(inst_id: str) -> Dict[str, Any]:
    """获取最新价格等信息"""
    data = _get("/api/v5/market/ticker", {"instId": inst_id})
    return data["data"][0] if data.get("data") else {}

def get_candles(inst_id: str, bar: str = "1H", limit: int = 5) -> List[List]:
    """获取K线数据"""
    data = _get("/api/v5/market/candles", {
        "instId": inst_id,
        "bar": bar,
        "limit": str(limit)
    })
    return data.get("data", [])

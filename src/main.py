#!/usr/bin/env python3
"""
Critical Funding & OI Monitor - OKX 版本
监控 BTC-USDT-SWAP / ETH-USDT-SWAP 的资金费率、持仓量、价格
"""

import time
from datetime import datetime, timezone
from typing import Dict, Any

from src.okx_client import (
    get_funding_rate,
    get_open_interest,
    get_ticker,
    get_candles,
)
from src.notifier import send_bark
from src.state import load_state, save_state

# 监控交易对
SYMBOLS = ["BTC-USDT-SWAP", "ETH-USDT-SWAP"]

# 告警阈值（可按需调整）
FUNDING_RATE_ALERT = 0.0015      # 单次资金费率绝对值 ≥ 0.15% 告警
OI_CHANGE_ALERT = 0.08           # 持仓量变化 ≥ 8% 告警（相对上次）


def fetch_symbol_data(inst_id: str) -> Dict[str, Any]:
    """拉取单个交易对全部数据"""
    result = {"instId": inst_id, "success": False, "error": None}

    try:
        funding = get_funding_rate(inst_id)
        oi = get_open_interest(inst_id)
        ticker = get_ticker(inst_id)
        candles_1h = get_candles(inst_id, bar="1H", limit=5)
        candles_4h = get_candles(inst_id, bar="4H", limit=3)

        result.update({
            "success": True,
            "fundingRate": float(funding.get("fundingRate", 0)),
            "nextFundingTime": funding.get("nextFundingTime"),
            "oi": float(oi.get("oi", 0)),
            "oiUsd": float(oi.get("oiUsd", 0)) if oi.get("oiUsd") else None,
            "last": float(ticker.get("last", 0)),
            "candles_1h": candles_1h,
            "candles_4h": candles_4h,
            "ts": int(time.time() * 1000),
        })
    except Exception as e:
        result["error"] = str(e)
        print(f"获取 {inst_id} 数据失败: {e}")

    return result


def check_alerts(symbol_data: Dict[str, Any], prev_state: Dict[str, Any]) -> list:
    """检查是否需要告警"""
    alerts = []
    inst_id = symbol_data["instId"]

    if not symbol_data.get("success"):
        return alerts

    # 1. 资金费率极值
    fr = symbol_data["fundingRate"]
    if abs(fr) >= FUNDING_RATE_ALERT:
        direction = "多头付费" if fr > 0 else "空头付费"
        alerts.append(
            f"{inst_id} 资金费率异常: {fr*100:.4f}% ({direction})"
        )

    # 2. 持仓量大幅变化
    prev = prev_state.get(inst_id, {})
    prev_oi = prev.get("oi")
    curr_oi = symbol_data.get("oi")

    if prev_oi and curr_oi and prev_oi > 0:
        change = (curr_oi - prev_oi) / prev_oi
        if abs(change) >= OI_CHANGE_ALERT:
            direction = "增加" if change > 0 else "减少"
            alerts.append(
                f"{inst_id} 持仓量{direction}: {change*100:.2f}% "
                f"(当前 OI: {curr_oi:,.0f})"
            )

    return alerts


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] 开始监控 {SYMBOLS}")

    state = load_state()
    all_alerts = []
    new_state = {}

    for inst_id in SYMBOLS:
        data = fetch_symbol_data(inst_id)

        if data["success"]:
            print(
                f"{inst_id}: "
                f"价格={data['last']:.2f} | "
                f"资金费率={data['fundingRate']*100:.4f}% | "
                f"OI={data['oi']:,.0f}"
            )
            alerts = check_alerts(data, state)
            all_alerts.extend(alerts)

            # 只保存必要字段到 state
            new_state[inst_id] = {
                "oi": data["oi"],
                "fundingRate": data["fundingRate"],
                "last": data["last"],
                "ts": data["ts"],
            }
        else:
            print(f"{inst_id}: 数据获取失败, 跳过")

    # 发送告警
    if all_alerts:
        title = "【OKX 资金费率/OI 告警】"
        content = "\n".join(all_alerts)
        print("触发告警:\n" + content)
        send_bark(title, content)
    else:
        print("无异常告警")

    # 保存状态
    save_state(new_state)
    print("监控完成，状态已保存。")


if __name__ == "__main__":
    main()

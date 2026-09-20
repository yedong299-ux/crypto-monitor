#!/usr/bin/env python3
"""
加密货币资金费率 + OI 监控主程序
运行方式: python -m src.main
"""

import os
import sys
import yaml
from datetime import datetime, timezone
from typing import Dict, Any

# 确保能找到包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fetchers.binance import fetch_symbol_data
from src.rules.derivatives import judge_funding_oi, format_alert_message
from src.notifier import send_bark
from src.state import load_state, save_state, is_in_cooldown, mark_alert


def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def calculate_oi_change(current_oi: float, previous_oi: float) -> float:
    if previous_oi is None or previous_oi <= 0:
        return 0.0
    return (current_oi - previous_oi) / previous_oi


def run_monitor():
    config = load_config()
    state = load_state()
    cooldown = config.get("cooldown_minutes", 60)
    only_high = config.get("only_high_confidence", True)
    group = config.get("bark_group", "crypto-funding-oi")

    symbols = config.get("symbols", ["BTCUSDT", "ETHUSDT"])
    last_data = state.get("last_data", {})

    print(f"[{datetime.now(timezone.utc).isoformat()}] 开始监控 {symbols}")

    for symbol in symbols:
        data = fetch_symbol_data(symbol)
        if not data:
            print(f"  {symbol}: 数据获取失败，跳过")
            continue

        # 计算 OI 变化（与上次运行对比）
        prev = last_data.get(symbol, {})
        prev_oi = prev.get("open_interest")
        oi_change_1h = calculate_oi_change(data["open_interest"], prev_oi)
        # 简单处理：没有历史 4h 数据时用 1h 近似，实际生产可存更多历史
        oi_change_4h = oi_change_1h  # 占位，后续可扩展为真正的 4h 对比

        # 更新状态中的最新数据
        last_data[symbol] = {
            "open_interest": data["open_interest"],
            "price": data["price"],
            "funding_rate": data["funding_rate"],
            "timestamp": data["timestamp"],
        }

        judgment = judge_funding_oi(
            funding_8h=data["funding_rate"],
            oi_change_1h=oi_change_1h,
            oi_change_4h=oi_change_4h,
            price_change_1h=data["price_change_1h"],
            price_change_4h=data["price_change_4h"],
            config=config,
        )

        if not judgment:
            print(f"  {symbol}: 无触发信号 (funding={data['funding_rate']*100:.4f}%)")
            continue

        # 置信度过滤
        if only_high and judgment["confidence"] not in ("高", "中高"):
            print(f"  {symbol}: 信号置信度不足，跳过")
            continue

        alert_key = f"{symbol}_{judgment['side']}"
        if is_in_cooldown(state, alert_key, cooldown):
            print(f"  {symbol}: 仍在冷却期，跳过推送")
            continue

        # 生成通知
        title = f"{judgment['direction']} | {symbol}"
        body = format_alert_message(
            symbol=symbol,
            data=data,
            judgment=judgment,
            oi_change_1h=oi_change_1h,
            oi_change_4h=oi_change_4h,
        )

        success = send_bark(
            title=title,
            body=body,
            group=group,
            level="timeSensitive" if judgment["confidence"] == "高" else "active",
            sound="alarm" if judgment["confidence"] == "高" else None,
        )

        if success:
            mark_alert(state, alert_key)
            print(f"  {symbol}: 已推送 [{judgment['direction']}]")
        else:
            print(f"  {symbol}: 推送失败")

    # 保存状态
    state["last_data"] = last_data
    save_state(state)
    print("监控完成，状态已保存。")


if __name__ == "__main__":
    run_monitor()

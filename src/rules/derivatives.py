from typing import Dict, List, Optional, Any
from datetime import datetime, timezone


def judge_funding_oi(
    funding_8h: float,
    oi_change_1h: float,
    oi_change_4h: float,
    price_change_1h: float,
    price_change_4h: float,
    config: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    资金费率 + OI 量化判断引擎。

    返回示例:
    {
        "direction": "高概率短期回调",
        "bias": "多头过热，易引发平仓 cascade",
        "confidence": "高",
        "score": 4.5,
        "reasons": [...],
        "timeframe": "1-6小时",
        "side": "long_squeeze"   # 或 short_squeeze
    }
    """
    funding_cfg = config.get("funding", {})
    oi_cfg = config.get("oi", {})
    price_cfg = config.get("price", {})

    score_long = 0.0
    score_short = 0.0
    reasons_long: List[str] = []
    reasons_short: List[str] = []

    # ========== 多头挤压（Long Squeeze）打分 ==========
    extreme_long = funding_cfg.get("extreme_long", 0.0008)
    overheat_long = funding_cfg.get("overheat_long", 0.0005)

    if funding_8h >= extreme_long:
        score_long += 2.0
        reasons_long.append(f"资金费率极端正值 ≥ {extreme_long*100:.2f}%")
    elif funding_8h >= overheat_long:
        score_long += 1.0
        reasons_long.append(f"资金费率过热 ≥ {overheat_long*100:.2f}%")

    strong_1h = oi_cfg.get("change_1h_strong", 0.05)
    sig_1h = oi_cfg.get("change_1h_significant", 0.03)
    strong_4h = oi_cfg.get("change_4h_strong", 0.08)
    sig_4h = oi_cfg.get("change_4h_significant", 0.05)

    if oi_change_1h >= strong_1h or oi_change_4h >= strong_4h:
        score_long += 1.0
        reasons_long.append("OI 快速大幅堆积")
    elif oi_change_1h >= sig_1h or oi_change_4h >= sig_4h:
        score_long += 0.5
        reasons_long.append("OI 明显增加")

    p1h = price_cfg.get("change_1h", 0.015)
    p4h = price_cfg.get("change_4h", 0.03)

    if price_change_1h >= p1h or price_change_4h >= p4h:
        score_long += 1.0
        reasons_long.append("价格加速上涨确认过热")

    # ========== 空头挤压（Short Squeeze）打分 ==========
    extreme_short = funding_cfg.get("extreme_short", -0.0006)
    overheat_short = funding_cfg.get("overheat_short", -0.0004)

    if funding_8h <= extreme_short:
        score_short += 2.0
        reasons_short.append(f"资金费率极端负值 ≤ {extreme_short*100:.2f}%")
    elif funding_8h <= overheat_short:
        score_short += 1.0
        reasons_short.append(f"资金费率过热（空） ≤ {overheat_short*100:.2f}%")

    # 空头加仓同样看 OI 上升
    if oi_change_1h >= strong_1h or oi_change_4h >= strong_4h:
        score_short += 1.0
        reasons_short.append("OI 快速大幅堆积（空头加仓）")
    elif oi_change_1h >= sig_1h or oi_change_4h >= sig_4h:
        score_short += 0.5
        reasons_short.append("OI 明显增加（空头加仓）")

    # 价格下跌确认空头拥挤
    if price_change_1h <= -p1h or price_change_4h <= -p4h:
        score_short += 1.0
        reasons_short.append("价格加速下跌确认空头拥挤")

    # ========== 输出判断 ==========
    result = None

    if score_long >= 4.0:
        result = {
            "direction": "高概率短期回调",
            "bias": "多头过热，易引发连环平仓",
            "confidence": "高",
            "score": round(score_long, 1),
            "reasons": reasons_long,
            "timeframe": "1-6小时",
            "side": "long_squeeze",
        }
    elif score_long >= 3.0:
        result = {
            "direction": "中高概率短期回调/震荡加剧",
            "bias": "多头偏拥挤，需警惕回调",
            "confidence": "中高",
            "score": round(score_long, 1),
            "reasons": reasons_long,
            "timeframe": "1-8小时",
            "side": "long_squeeze",
        }
    elif score_short >= 4.0:
        result = {
            "direction": "高概率逼空",
            "bias": "空头过热，反弹/挤压概率较高",
            "confidence": "高",
            "score": round(score_short, 1),
            "reasons": reasons_short,
            "timeframe": "1-6小时",
            "side": "short_squeeze",
        }
    elif score_short >= 3.0:
        result = {
            "direction": "中高概率逼空/反弹",
            "bias": "空头偏拥挤，关注向上挤压",
            "confidence": "中高",
            "score": round(score_short, 1),
            "reasons": reasons_short,
            "timeframe": "1-8小时",
            "side": "short_squeeze",
        }

    return result


def format_alert_message(
    symbol: str,
    data: Dict[str, Any],
    judgment: Dict[str, Any],
    oi_change_1h: float,
    oi_change_4h: float,
) -> str:
    """生成详细的 Bark 通知正文。"""
    funding_pct = data["funding_rate"] * 100
    price = data["price"]
    p1h = data["price_change_1h"] * 100
    p4h = data["price_change_4h"] * 100
    oi = data["open_interest"]

    lines = [
        f"【{judgment['direction']}】{symbol}",
        f"置信度: {judgment['confidence']} | 得分: {judgment['score']}",
        f"时间框架: {judgment['timeframe']}",
        "",
        f"当前价格: ${price:,.2f}",
        f"1h涨跌: {p1h:+.2f}% | 4h涨跌: {p4h:+.2f}%",
        f"资金费率(8h): {funding_pct:+.4f}%",
        f"OI变化: 1h {oi_change_1h*100:+.2f}% | 4h {oi_change_4h*100:+.2f}%",
        f"当前OI: {oi:,.0f} 张",
        "",
        f"判断: {judgment['bias']}",
        "理由:",
    ]
    for r in judgment["reasons"]:
        lines.append(f"  • {r}")

    lines.append("")
    lines.append("仅供参考，不构成投资建议。")

    return "\n".join(lines)

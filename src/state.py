import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional


STATE_FILE = "state.json"


def load_state() -> Dict[str, Any]:
    if not os.path.exists(STATE_FILE):
        return {"last_alerts": {}, "last_data": {}}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_alerts": {}, "last_data": {}}


def save_state(state: Dict[str, Any]) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def is_in_cooldown(state: Dict[str, Any], key: str, cooldown_minutes: int) -> bool:
    """检查某个信号是否在冷却期内。"""
    last = state.get("last_alerts", {}).get(key)
    if not last:
        return False
    try:
        last_time = datetime.fromisoformat(last)
        now = datetime.now(timezone.utc)
        return (now - last_time) < timedelta(minutes=cooldown_minutes)
    except Exception:
        return False


def mark_alert(state: Dict[str, Any], key: str) -> None:
    """记录本次告警时间。"""
    if "last_alerts" not in state:
        state["last_alerts"] = {}
    state["last_alerts"][key] = datetime.now(timezone.utc).isoformat()

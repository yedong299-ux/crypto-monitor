import os
import requests
from typing import Optional

def send_bark(title: str, content: str, key: Optional[str] = None) -> bool:
    """发送 Bark 推送通知"""
    key = key or os.getenv("BARK_KEY")
    if not key:
        print("未配置 BARK_KEY，跳过推送")
        return False

    url = f"https://api.day.app/{key}/{title}/{content}"
    try:
        resp = requests.get(url, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"Bark 推送失败: {e}")
        return False

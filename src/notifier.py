import os
import requests
from typing import Optional
from urllib.parse import quote


def send_bark(
    title: str,
    body: str,
    group: str = "crypto",
    level: str = "active",
    sound: Optional[str] = None,
    url: Optional[str] = None,
) -> bool:
    """
    通过 Bark 发送推送通知。
    成功返回 True，失败返回 False。
    """
    key = os.environ.get("BARK_KEY")
    if not key:
        print("错误: 环境变量 BARK_KEY 未设置")
        return False

    # Bark 支持 title/body 方式，内容需 URL 编码
    encoded_title = quote(title)
    encoded_body = quote(body)

    base = f"https://api.day.app/{key}/{encoded_title}/{encoded_body}"

    params = {
        "group": group,
        "level": level,
    }
    if sound:
        params["sound"] = sound
    if url:
        params["url"] = url

    try:
        resp = requests.get(base, params=params, timeout=10)
        if resp.status_code == 200:
            print(f"Bark 推送成功: {title}")
            return True
        else:
            print(f"Bark 推送失败: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"Bark 推送异常: {e}")
        return False

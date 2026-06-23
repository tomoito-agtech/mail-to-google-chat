"""
发送到谷歌chat
"""
import requests
from core.models import GoogleChatConfig

def send_google_chat_message(webhook_url:GoogleChatConfig,message:str) -> None:
    url = webhook_url.webhook_url
    text = {'text': message}
    response = requests.post(url, json=text)

    # 如果 HTTP 请求失败，就主动抛出异常。
    # 如果请求成功，就什么都不做。
    response.raise_for_status()
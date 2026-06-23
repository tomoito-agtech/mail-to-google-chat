"""
程序入口，负责 print 输出
"""
import configparser

# 导包
from core.config import get_mail_config,get_google_chat_config,get_zen_sql_config
from mail.mail_receiver import fetch_recent_mails
from chat.chat_notifier import send_google_chat_message
from zen.sql_repository import ZenSqlRepository


def build_google_chat_message(mail,received_account:str):
    """
    往 google chat 发送信息
    """
    return(
        f"受信日時: {mail.received_dt}\n"
        f"受信アカウント: {received_account}\n"
        f"件名: {mail.subject}"
    )

def main() :
    try:
        # 1. 从 .env 读取各种配置
        mail_config = get_mail_config()
        google_chat_config = get_google_chat_config()
        zen_sql_config = get_zen_sql_config()

        # 2. 创建 Zen SQL 操作用的对象
        zen_repository = ZenSqlRepository(zen_sql_config)

        # 3. 获取最近 10 分钟收到的邮件
        target_minutes = 10
        mails = fetch_recent_mails(mail_config,minutes=target_minutes)

        if not mails:
            print(f"直近{target_minutes}分間のメールはありません。")
            return

        for mail in mails:
            # 创建 Google Chat 通知内容
            google_chat_message = build_google_chat_message(mail=mail,received_account=mail_config.user)

            # 发送到 Google Chat
            send_google_chat_message(webhook_url=google_chat_config,message=google_chat_message)

            # 用 SQLAlchemy 保存到 zen数据库
            zen_repository.save_mail(mail=mail,received_account=mail_config.user)

            print("=" * 100)
            print("Google Chat 通知完成")
            print("Actian Zen SQL 保存完成")
            print(google_chat_message)

    except Exception as error:
        print(f"エラーが発生しました: {error}")

if __name__ == '__main__':
    main()
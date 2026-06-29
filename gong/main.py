"""
程序入口，负责整体流程控制和 print 输出
"""

from core.config import (
    get_mail_config,
    get_google_chat_config,
    get_zen_sql_config,
    get_btrieve_config,
)
from mail.mail_receiver import fetch_recent_mails
from chat.chat_notifier import send_google_chat_message
from zen.sql_repository import ZenSqlRepository
from zen.btrieve_repository import BtrieveRepository


# 获取最近多少分钟内收到的邮件
TARGET_MINUTES = 10


def build_google_chat_message(mail, received_account: str) -> str:
    """
    生成 Google Chat 通知内容
    """
    return (
        f"受信日時: {mail.received_dt}\n"
        f"受信アカウント: {received_account}\n"
        f"件名: {mail.subject}"
    )

def main():
    try:
        # 1. 从 .env 读取各种配置
        mail_config = get_mail_config()
        google_chat_config = get_google_chat_config()
        zen_sql_config = get_zen_sql_config()
        btrieve_config = get_btrieve_config()

        # 2. 创建 Zen SQL 和 Btrieve 操作用的对象
        zen_repository = ZenSqlRepository(zen_sql_config)
        btrieve_repository = BtrieveRepository(btrieve_config)

        # 3. 获取最近指定分钟内收到的邮件
        mails = fetch_recent_mails(
            config=mail_config,
            minutes=TARGET_MINUTES,
        )

        if not mails:
            print(f"直近{TARGET_MINUTES}分間のメールはありません。")
            return

        # 4. 逐封处理邮件
        for mail in mails:
            google_chat_message = build_google_chat_message(
                mail=mail,
                received_account=mail_config.user,
            )

            # 发送到 Google Chat
            send_google_chat_message(
                webhook_url=google_chat_config,
                message=google_chat_message,
            )

            # 用 SQLAlchemy 保存到 Zen 数据库
            zen_repository.save_mail(
                mail=mail,
                received_account=mail_config.user,
            )

            # 用 Btrieve API 保存到 Zen 数据库
            btrieve_repository.save_mail(
                mail=mail,
                received_account=mail_config.user,
            )

            print("=" * 100)
            print("Google Chat 通知完成")
            print("Actian Zen SQL 保存完成")
            print("Actian Zen Btrieve 保存完成")
            print(google_chat_message)

    except Exception as error:
        print(f"エラーが発生しました: {error}")


if __name__ == "__main__":
    main()
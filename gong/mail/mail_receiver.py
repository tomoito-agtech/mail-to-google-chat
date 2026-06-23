"""
负责接受邮件，串联整个邮件接收流程。

"""

# 导包
import imaplib
from datetime import datetime, timedelta, timezone
from email import message_from_bytes
from typing import List

from core.config import MailConfig
from core.models import ReceivedMail
from mail.mail_parser import decode_subject, get_body
from mail.mail_fetcher import format_imap_date, fetch_internal_date_from_server, fetch_raw_email



# 接收最近指定分钟内的邮件
def fetch_recent_mails(config: MailConfig, minutes: int = 10) -> List[ReceivedMail]:
    """
    接收最近指定分钟数以内的邮件。

    :param config: 邮箱连接信息
    :param minutes: 最近多少分钟内收到的邮件
    :return: recent_mails列表
    """
    recent_mails = []

    # 计算判断基准时间：当前 UTC 时间 - minutes 分钟
    target_datetime = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    # 把判断基准时间转换成 IMAP 搜索用的日期格式
    since_date = format_imap_date(target_datetime)


    # 使用 IMAP / 143 / 非 SSL 连接邮件服务器
    with imaplib.IMAP4(config.host, config.port) as mail:
        # 使用 .env 中读取到的账号和密码登录邮箱
        mail.login(config.user, config.password)

        # 选择收件箱INBOX
        status, _ = mail.select("INBOX")
        # 如果 INBOX 选择失败，就停止程序
        if status != "OK":
            raise RuntimeError("INBOXを選択できませんでした。")

        # 先用 SINCE 按日期粗略搜索邮件
        status, data = mail.search(None, "SINCE", since_date)
        # 如果搜索失败，就停止程序
        if status != "OK":
            raise RuntimeError("メール検索に失敗しました。")

        # 从搜索结果中取出邮件 ID 列表
        mail_ids = data[0].split()

        # 逐封处理邮件
        for mail_id in mail_ids:
            # 取得服务器接收时间 UCI格式
            received_datetime = fetch_internal_date_from_server(mail, mail_id)
            if received_datetime is None:
                continue

            # 如果这封邮件早于 target_datetime (比要求时间过早)，说明不是最近 minutes 分钟内的邮件，跳过
            if received_datetime < target_datetime:
                continue

            # 取得原始邮件内容
            raw_email = fetch_raw_email(mail, mail_id)
            if raw_email is None:
                continue

            # 把原始邮件 bytes 转成 Python 的 email message 对象
            message = message_from_bytes(raw_email)

            # 解析标题
            subject = decode_subject(message.get("Subject"))

            # 解析正文
            body = get_body(message)

            # 保存结果
            recent_mails.append(
                ReceivedMail(
                    received_dt=received_datetime,
                    subject=subject,
                    body=body,
                )
            )

    return recent_mails
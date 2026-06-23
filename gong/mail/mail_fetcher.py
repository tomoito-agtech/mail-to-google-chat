"""
通过 IMAP 协议从邮件服务器里读取数据，
1. 把 Python 的 datetime 转换成 IMAP 搜索用的日期格式
2. 拿到服务器里 INTERNALDATE后面的时间，并转换成UTC时间
3. 根据邮件 ID 拿到邮件原始内容的bytes
"""

import re
from datetime import datetime, timezone

#  把 Python 的 datetime 转成 IMAP 搜索用的日期格式。
def format_imap_date(target_datetime: datetime) -> str:
    """
    把 Python 的 datetime 转成 IMAP 搜索用的日期格式。
    IMAP 的 SINCE 条件需要这种格式：03-Jun-2026

    :param target_datetime:  Python 的 datetime。
    :return: IMAP 可以识别的日期字符串。
    """

    # IMAP 的月份必须是英文缩写，手动准备月份列表
    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    # 从 datetime 拿到年月日
    year = target_datetime.year
    month = months[target_datetime.month - 1] # IMAP 的月份必须是英文缩写，所以这里手动准备月份列表
    day = target_datetime.day

    # 组装成 IMAP 需要的格式，例如 03-Jun-2026
    return f"{day:02d}-{month}-{year}"




"""
拿到 INTERNALDATE后面的时间，并转换成UTC时间
"""

#  通过 IMAP 协议，向邮件服务器请求指定邮件的 INTERNALDATE。
def fetch_internal_date_from_server(mail, mail_id: bytes) -> datetime | None:
    """
    根据邮件 ID，向邮件服务器取得 INTERNALDATE。
    这里只取 INTERNALDATE 的内容，不取邮件正文。

    INTERNALDATE 是邮件服务器记录的“邮件进入邮箱的时间”。
    用它来判断是否是最近 10 分钟内收到的邮件。

    格式：
        INTERNALDATE "05-Jun-2026 11:25:30 +0900"

    :param mail: 已经登录成功并选择 INBOX 的 IMAP 连接对象。
    :param mail_id: mail.search() 的搜索结果的  邮件 ID
    :return: UTC datetime | None
    """

    # 通过 IMAP 协议，向邮件服务器请求这封邮件的 INTERNALDATE
    status, fetch_data = mail.fetch(mail_id, "(INTERNALDATE)")

    # 如果服务器返回失败，就返回 None
    if status != "OK":
        return None

    # 通过 自定义的extract_internal_date函数，将 INTERNALDATE 里的时间字符串取提取出来，并返回
    return extract_internal_date(fetch_data)

# 从 IMAP 返回的数据里找到找到 INTERNALDATE "..."，然后把里面的 "..."时间字符串取出来。
def extract_internal_date(fetch_data) -> datetime | None:
    """
    取出 INTERNALDATE 里的字符串。
    fetch_internal_date_from_sever函数的延续，
    将提取的 INTERNALDATE 字符串返回给fetch_internal_date_from_sever函数

    :param fetch_data: mail.fetch() 返回的数据
    :return: datetime
    """

    # fetch_data 是 IMAP 服务器返回的数据列表，遍历 IMAP 返回的数据
    for item in fetch_data:

        # 如果返回数据是 tuple，真正的信息在 item[0]
        if isinstance(item, tuple):
            target = item[0]
        # 如果 item 不是 tuple，就直接使用 item 本身
        else:
            target = item

        # 如果 target 不是 bytes，说明不是我们要解析的数据，跳过
        if not isinstance(target, bytes):
            continue

        # 从 bytes 里查找 INTERNALDATE "..." 这一段
        match = re.search(rb'INTERNALDATE "([^"]+)"', target)
        # 如果没有找到 INTERNALDATE，就继续看下一项
        if not match:
            continue

        # 取出 INTERNALDATE 里面的时间字符串，并从 bytes 转成 str
        date_text = match.group(1).decode("ascii")
        # 通过 自定义parse_internal_date函数，将 INTERNALDATE 里的时间字符串转成Python 的 datetime，并返回
        return parse_internal_date(date_text)

    # 没有找到 INTERNALDATE，就返回 None
    return None

#  把字符串时间转换成 Python datetime，再统一转换成 UTC 时间
def parse_internal_date(date_text: str) -> datetime | None:
    """
    把 INTERNALDATE 字符串转换成 Python 的 datetime。

    extract_internal_date的延续，
    把 INTERNALDATE 里的时间字符串返回给extract_internal_date函数

    邮件时间必须变成 datetime，才能和 target_datetime 比较。

    :param date_text: INTERNALDATE 后面的时间字符串 "05-Jun-2026 11:25:30 +0900"
    :return: datetime
    """

    try:
        # 把 INTERNALDATE 字符串转换成带时区的 datetime
        mail_datetime = datetime.strptime(date_text, "%d-%b-%Y %H:%M:%S %z")
    except ValueError:
        # 如果时间格式不符合预期，就返回 None
        return None

    # 统一转换成 UTC 时间，方便后面和 target_datetime 比较
    return mail_datetime.astimezone(timezone.utc)




"""
拿到邮件原始内容的bytes
"""

# 通过 IMAP 协议，向邮件服务器请求指定邮件的原始内容
def fetch_raw_email(mail, mail_id: bytes) -> bytes | None:
    """
    根据邮件 ID，通过 IMAP 协议，向邮件服务器取得邮件原始内容。

    :param mail:   已经登录成功并选择 INBOX 的 IMAP 连接对象。
    :param mail_id:  邮件 ID， mail.search() 的搜索结果。
    :return: 返回邮件原始 bytes | None
    """

    # 通过 IMAP 协议，向邮件服务器请求这封邮件的原始内容
    status, fetch_data = mail.fetch(mail_id, "(BODY.PEEK[])")

    if status != "OK":
        return None

    # 通过自定义函数 extract_raw_email 返回的数据中提取邮件原始 bytes 内容
    return extract_raw_email(fetch_data)

# 从 IMAP fetch 返回的数据中取出原始邮件内容
def extract_raw_email(fetch_data) -> bytes | None:
    """
    从 IMAP fetch 返回的数据中取出邮件原始内容。
    fetch_raw_email的延续
    把 邮件原始 bytes 内容 返回给 fetch_raw_email函数

    邮件原始内容是 bytes 类型。
    后面会用 message_from_bytes() 把它转换成邮件对象。
    """

    # 遍历 IMAP 返回的数据
    for item in fetch_data:
        # 如果 item 是 tuple，并且 item[1] 是 bytes，
        if isinstance(item, tuple) and isinstance(item[1], bytes):
            # 返回邮件原始 bytes 内容
            return item[1]

    return None







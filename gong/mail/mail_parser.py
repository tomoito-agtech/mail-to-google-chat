"""
解析 邮件标题Subject / 邮件内容Body
它只负责处理已经取得的邮件对象。

1. 把邮件标题 Subject 解码成人能看懂的文字
2. 把邮件正文 Body 从 bytes 转成字符串
3. 从邮件对象中提取正文内容
"""

from email.header import decode_header


# 全局通用解码函数，把邮件正文的 bytes 数据转换成字符串的方法。
def decode_payload(payload: bytes, charset: str | None) -> str:
    """
    把 bytes 数据转换成字符串。

    :param payload:  邮件原始 bytes 数据
    :param charset:  数据指定的文字编码
    :return: 解码后的字符串。
    """
    try:
        # 使用邮件提供的 charset 解码；如果 charset 为空，就使用 utf-8
        return payload.decode(charset or "utf-8", errors="replace")
    except LookupError:
        # 如果 charset 是 Python 不认识的编码，就退回使用 utf-8 解码
        return payload.decode("utf-8", errors="replace")



# 解码邮件标题 Subject
def decode_subject(Subject: str | None) -> str:
    """
    解码邮件标题等 MIME 编码文字。
    把不是普通文字的标题还原成人能看懂的文字。

    邮件标题里可能包含日语、中文等非 ASCII 字符会被 MIME 编码，
    不解码，终端里看到的标题可能是一串乱码。

    :param Subject: 邮件标题 Subject。 可能是普通字符串，也可能是 MIME 编码后的字符串。
    :return:  解码后的邮件标题字符串。
    """

    # 如果标题不存在，返回空字符串，避免后面处理 None 报错
    if Subject is None:
        return ""

    # 准备一个空字符串，用来保存最终解码后的标题
    result = ""

    # 拆开邮件标题，每个部分包含 内容part 和 编码encoding，遍历后拿到 内容part 和 编码encoding
    for part, encoding in decode_header(Subject):
        if isinstance(part, bytes):
            # 使用全局通用解码函数
            result += decode_payload(part, encoding)
        else:
            # 如果 part 已经是字符串，就直接拼接到结果里
            result += part

    return result



# 从邮件对象里提取正文 Body
def get_body(body_message) -> str:
    """
    从邮件对象中提取正文。

    如果邮件是 multipart，就遍历每一个 part。优先提取 text/plain。
    如果没有 text/plain，就使用 text/html。附件不处理。


    :param body_message: message_from_bytes(raw_email) 转换出来的邮件对象，由receiver调用传入
    :return: 邮件正文字符串。
    """

    # 如果邮件是 multipart，说明正文、HTML、附件等被分成多个 part
    if body_message.is_multipart():
        # 暂时保存 HTML 正文；只有没有 text/plain 时才使用
        html_body = ""

        # 遍历邮件里的每一个 part
        for part in body_message.walk():
            # 取得当前 part 的类型，例如 text/plain 或 text/html
            content_type = part.get_content_type()
            # 取得当前 part 的 Content-Disposition，用来判断是否是附件
            content_disposition = str(part.get("Content-Disposition"))

            # 如果当前 part 是附件，就跳过
            if "attachment" in content_disposition:
                continue

            # 取得当前 part 的原始 bytes 内容
            payload = part.get_payload(decode=True)
            # 如果当前 part 没有内容，就跳过
            if not payload:
                continue

            # 取得当前 part 的文字编码
            charset = part.get_content_charset()

            # 如果当前 part 是普通文本正文，使用解码函数后直接返回
            if content_type == "text/plain":
                return decode_payload(payload, charset)

            # 如果当前 part 是 HTML 正文，使用解码函数后放入html_body 空字符串里面最后一起返回
            if content_type == "text/html" and not html_body:
                html_body = decode_payload(payload, charset)

        return html_body

    # 如果邮件不是 multipart，说明正文直接在 message 本身里
    payload = body_message.get_payload(decode=True)
    # 取得正文的文字编码
    charset = body_message.get_content_charset()

    # 判断是不是正文，是的话使用解码函数后直接返回
    if payload:
        return decode_payload(payload, charset)

    # 没有的话返回空字符串
    return ""

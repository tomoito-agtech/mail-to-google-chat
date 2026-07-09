"""
使用 Btrieve API 保存邮件数据。
"""
from datetime import datetime, timezone
from pathlib import Path

import btrievePython as btrv

from core.models import BtrieveConfig, ReceivedMail


class BtrieveRepository:
    """
    使用 Btrieve API 保存邮件数据。
    字段位置根据 DDF 的 record 布局手动设置。
    """

    # record 固定区：DDF 显示レコード長为 545，所以 0～544 是固定区，545以后是可变长区
    FIXED_RECORD_SIZE = 545

    # id：DDF position=0, size=4, type=Auto Increment
    ID_POS = 0
    ID_SIZE = 4

    # TIMESTAMP：DDF 中 received_dt / created_at 的 size 都是 8
    TIMESTAMP_SIZE = 8

    # received_dt：DDF position=5, size=8, type=Timestamp
    # 允许 NULL，所以 position 前 1 byte，也就是 4，是 NULL 标志
    RECEIVED_DT_NULL_POS = 4
    RECEIVED_DT_POS = 5

    # received_account：DDF position=14, size=256, type=Zstring / VARCHAR(255)
    # 允许 NULL，所以 13 是 NULL 标志，14 开始是实际文字区域
    ACCOUNT_NULL_POS = 13
    ACCOUNT_POS = 14
    ACCOUNT_SIZE = 256

    # subject：DDF position=271, size=256, type=Zstring / VARCHAR(255)
    # 允许 NULL，所以 270 是 NULL 标志，271 开始是实际文字区域
    SUBJECT_NULL_POS = 270
    SUBJECT_POS = 271
    SUBJECT_SIZE = 256

    # body：DDF position=528, size=8, type=Clob / LONGVARCHAR
    # 527 是 NULL 标志；528～535(8size) 保存正文长度和正文起点；545以后才是正文
    # 528～531：4 个字节，保存“正文长度”这个数字，532～535：4 个字节，保存“正文开始位置”这个数字(在record的第532个位置，写入一个数字。这个数字告诉 Zen：真正的正文从哪里开始。)
    BODY_NULL_POS = 527
    BODY_TEXT_LENGTH_VALUE_POS = 528
    BODY_TEXT_START_VALUE_POS = 532 #在532这个位置写如545这个数字。因为Btrieve 读 LONGVARCHAR 的时候，不会自己猜正文在哪里。需要在固定区里看到一个说明数字
    BODY_TEXT_POS = FIXED_RECORD_SIZE
    BODY_MAX_SIZE = 5000

    # created_at：DDF position=537, size=8, type=Timestamp
    # 允许 NULL，所以 536 是 NULL 标志，537 开始是实际时间数据
    CREATED_AT_NULL_POS = 536
    CREATED_AT_POS = 537

    # 字符编码：先用 UTF-8，后面如果日文乱码再改这里
    TEXT_ENCODING = "cp932"

    def __init__(self, config: BtrieveConfig):
        self.file_path = Path(config.file_path)

    def save_mail(self, mail: ReceivedMail, received_account: str) -> None:
        """
        使用 Btrieve API 保存一封邮件。
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Btrieve 文件不存在: {self.file_path}")

        client = btrv.BtrieveClient()
        btrieve_file = btrv.BtrieveFile()
        opened = False

        try:
            # 打开 MKD 文件
            status = client.FileOpen(
                btrieve_file,
                str(self.file_path),
                None,
                btrv.Btrieve.OPEN_MODE_NORMAL,
            )
            self._check_status(status, "Btrieve 文件打开失败")

            opened = True

            # 把邮件对象转换成 Btrieve API 需要的一整条 record
            record = self._build_record(
                mail=mail,
                received_account=received_account,
                created_at=datetime.now(),
            )

            # 写入一条 record
            status = btrieve_file.RecordCreate(record)
            self._check_status(status, "Btrieve record 保存失败")

        finally:
            # 打开过文件的话，最后一定要关闭
            if opened:
                close_status = client.FileClose(btrieve_file)
                self._check_status(close_status, "Btrieve 文件关闭失败")

    def _build_record(
        self,
        mail: ReceivedMail,
        received_account: str,
        created_at: datetime,
    ) -> bytes:
        """
        把 ReceivedMail 转成 Btrieve API 需要的 bytes record。
        """
        fixed_record = bytearray(self.FIXED_RECORD_SIZE)

        # id 是 IDENTITY / Auto Increment 字段。
        # 这里写 0，让 Zen 自动分配 id。
        self._put_uint(
            fixed_record,
            self.ID_POS,
            0,
            self.ID_SIZE,
        )

        # received_dt 不为空
        fixed_record[self.RECEIVED_DT_NULL_POS] = 0

        # 写入 received_dt
        self._put_timestamp(
            fixed_record,
            self.RECEIVED_DT_POS,
            mail.received_dt,
        )

        # received_account 不为空
        fixed_record[self.ACCOUNT_NULL_POS] = 0

        # 写入 received_account
        self._put_zstring(
            fixed_record,
            self.ACCOUNT_POS,
            self.ACCOUNT_SIZE,
            received_account,
        )

        # subject 不为空
        fixed_record[self.SUBJECT_NULL_POS] = 0

        # 写入 subject
        self._put_zstring(
            fixed_record,
            self.SUBJECT_POS,
            self.SUBJECT_SIZE,
            mail.subject,
        )

        # body 正文转成 bytes
        body_bytes = self._encode_text_limit(
            mail.body,
            self.BODY_MAX_SIZE,
        )

        # body 不为空
        fixed_record[self.BODY_NULL_POS] = 0

        # 在 body 说明区写入：body 正文的 bytes 长度
        self._put_uint(
            fixed_record,
            self.BODY_TEXT_LENGTH_VALUE_POS,
            len(body_bytes),
            4,
        )

        # 在 body 说明区写入：body 正文真正开始的位置
        self._put_uint(
            fixed_record,
            self.BODY_TEXT_START_VALUE_POS,
            self.BODY_TEXT_POS,
            4,
        )

        # created_at 不为空
        fixed_record[self.CREATED_AT_NULL_POS] = 0

        # 写入 created_at
        self._put_timestamp(
            fixed_record,
            self.CREATED_AT_POS,
            created_at,
        )

        # 最终 record =
        # 固定部分 545 bytes + body 正文 bytes
        return bytes(fixed_record) + body_bytes

    def _put_zstring(
        self,
        record: bytearray,
        pos: int,
        size: int,
        value: str,
    ) -> None:
        """
        写入 Zstring。

        VARCHAR(255) 在 DDF 里是 Zstring 256 bytes。
        最后 1 byte 用来放 0 结尾。
        """
        text_bytes = self._encode_text_limit(value, size - 1)

        # 先把这个字段区域全部清空
        record[pos: pos + size] = b"\x00" * size

        # 再写入实际文字
        record[pos: pos + len(text_bytes)] = text_bytes

    def _put_timestamp(
        self,
        record: bytearray,
        pos: int,
        value: datetime,
    ) -> None:
        """
        写入 Zen TIMESTAMP。
        """
        timestamp_bytes = self._datetime_to_btrieve_timestamp(value)
        record[pos: pos + self.TIMESTAMP_SIZE] = timestamp_bytes

    def _put_uint(
        self,
        record: bytearray,
        pos: int,
        value: int,
        size: int,
    ) -> None:
        """
        写入无符号整数。
        """
        record[pos: pos + size] = value.to_bytes(
            size,
            byteorder="little",
            signed=False,
        )

    def _encode_text_limit(self, value: str, max_size: int) -> bytes:
        """
        字符串转 bytes，并限制最大长度。

        中文 / 日文不能直接按 bytes 截断，
        否则可能把一个字符切坏。
        """
        if value is None:
            value = ""

        encoded = value.encode(self.TEXT_ENCODING)

        if len(encoded) <= max_size:
            return encoded

        encoded = encoded[:max_size]

        while True:
            try:
                encoded.decode(self.TEXT_ENCODING)
                return encoded
            except UnicodeDecodeError:
                encoded = encoded[:-1]

    def _datetime_to_btrieve_timestamp(self, value: datetime) -> bytes:
        """
        datetime 转成 Zen TIMESTAMP 的 8 bytes。
        """
        if value.tzinfo is None:
            # 没有 timezone 的 datetime，按本机本地时间处理
            value = value.astimezone()

        utc_value = value.astimezone(timezone.utc)
        base = datetime(1, 1, 1, tzinfo=timezone.utc)

        delta = utc_value - base

        timestamp_value = (
            (delta.days * 24 * 60 * 60 + delta.seconds) * 10_000_000
            + delta.microseconds * 10
        )

        return timestamp_value.to_bytes(
            self.TIMESTAMP_SIZE,
            byteorder="little",
            signed=False,
        )

    def _check_status(self, status: int, message: str) -> None:
        """
        检查 Btrieve API 返回状态。
        """
        if status != btrv.Btrieve.STATUS_CODE_NO_ERROR:
            raise RuntimeError(
                f"{message}: {btrv.Btrieve_StatusCodeToString(status)}"
            )
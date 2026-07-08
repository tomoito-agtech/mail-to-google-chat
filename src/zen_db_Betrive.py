import btrievePython
import struct


def insert_betrive(mail_id: int, unix_micro: int, account: str, subject: str):
    # ==========================================
    # 1. オフセット設定
    # ==========================================
    FIXID_RECORD_SIZE = 165  # ★ 画像の通り165バイトに修正

    # ID（画像：位置0, サイズ4, ヌルなし）
    ID_POS = 0  # ★ 0番目から直接スタート！NULLフラグは無し
    ID_SIZE = 4

    # MailTime（画像：位置5, サイズ8, ヌルあり）
    RECEIVED_MT_NULL_POS = 4  # 本体が5番目からなので、その手前の4番目がNULLフラグ
    MT_POS = 5
    MT_SIZE = 8

    # Account（画像：位置14, サイズ50, ヌルあり）
    Account_NULL_POS = 13  # 本体が14番目からなので、その手前の13番目がNULLフラグ
    Account_POS = 14
    Account_SIZE = 50

    # Subject（画像：位置65, サイズ100, ヌルあり）
    Subject_NULL_POS = 64  # 本体が65番目からなので、その手前の64番目がNULLフラグ
    Subject_POS = 65
    Subject_SIZE = 100

    # ==========================================
    # 2. ファイルを開く
    # ==========================================
    btrieveClient = btrievePython.BtrieveClient()
    btrieveFile = btrievePython.BtrieveFile()

    rc = btrieveClient.FileOpen(
        btrieveFile,
        r"C:\ProgramData\Actian\Zen\mailrecord\record000.MKD",
        None,
        btrievePython.Btrieve.OPEN_MODE_NORMAL
    )

    if rc != 0:
        print(f"File open 失敗 (Status: {rc})")
        return

    try:
        # ==========================================
        # 3. 165バイトの空の箱を作る
        # ==========================================
        record = bytearray(FIXID_RECORD_SIZE)

        # ------------------------------------------
        # 【ID の書き込み】
        # ------------------------------------------
        # 0番目から直接、4バイトの整数を書き込み（NULLフラグなし）
        struct.pack_into("<i", record, ID_POS, mail_id)

        # ------------------------------------------
        # 【MailTime の書き込み】
        # ------------------------------------------
        record[RECEIVED_MT_NULL_POS] = 0  # 値あり

        # 正しいタイムスタンプを計算して8バイトで固める
        ts_obj = btrievePython.Btrieve_UnixEpochMicrosecondsToTimestamp(unix_micro)
        ts_bytes = struct.pack("<Q", ts_obj)
        record[MT_POS: MT_POS + MT_SIZE] = ts_bytes

        # ------------------------------------------
        # 【Account の書き込み】
        # ------------------------------------------
        record[Account_NULL_POS] = 0  # 値あり
        record[Account_POS: Account_POS + Account_SIZE] = account.encode("shift_jis").ljust(Account_SIZE, b"\x00")

        # ------------------------------------------
        # 【Subject の書き込み】
        # ------------------------------------------
        record[Subject_NULL_POS] = 0  # 値あり
        record[Subject_POS: Subject_POS + Subject_SIZE] = subject.encode("shift_jis").ljust(Subject_SIZE, b"\x00")

        # ==========================================
        # 4. Btrieveへ登録
        # ==========================================
        status = btrieveFile.RecordCreate(record)
        print("RecordCreate status =", status)

        if status == 0:
            print("データベースへのデータ登録に成功しました！")
        else:
            print(f"登録失敗 (Status: {status})")

    finally:
        btrieveClient.FileClose(btrieveFile)
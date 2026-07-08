import imaplib
import os
import email
from email.header import decode_header
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from email.utils import parsedate_to_datetime
import requests

from zen_db_SQL import insert_user



# .envファイルを読み込み
load_dotenv()

CPI_IMAP_SERVER = os.getenv("CPI_IMAP_SERVER")
CPI_EMAIL_USER = os.getenv("CPI_EMAIL")
CPI_PASSWORD = os.getenv("CPI_PASSWORD")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

UID_FILE = "last_uid.txt"


if CPI_IMAP_SERVER:
    CPI_IMAP_SERVER = CPI_IMAP_SERVER.strip()
if CPI_EMAIL_USER:
    CPI_EMAIL_USER = CPI_EMAIL_USER.strip()
if CPI_PASSWORD:
    CPI_PASSWORD = CPI_PASSWORD.strip()

def decode_str(b, encoding):
    if isinstance(b, bytes):
        return b.decode(encoding or "utf-8", errors="ignore")
    return b

def get_email_body(msg):
    #メールが複数パートか判定　真はtrue
    if msg.is_multipart():
        #メールオブジェクトのパーツを順番に見る
        for part in msg.walk():
            #パーツの種類を取得
            content_type = part.get_content_type()
            #添付ファイルか確認
            content_disposition = str(part.get("Content-Disposition"))
            #本文だけを取得
            if content_type == "text/plain" and "attachment" not in content_disposition:
                #文字コードを取得
                charset = part.get_content_charset()
                #本文をデコード
                return decode_str(part.get_payload(decode=True), charset)
    else:
        charset = msg.get_content_charset()
        return decode_str(msg.get_payload(decode=True), charset)
    return ""

def main ():
    # 日本時間
    JST = timezone(timedelta(hours=9))

    #最後に読み込んだUIDを読み込み
    conect = imaplib.IMAP4(CPI_IMAP_SERVER)
    conect.login(CPI_EMAIL_USER, CPI_PASSWORD)
    conect.select("INBOX")

    #UIDファイルが存在しない場合
    if not os.path.exists(UID_FILE):

        #全UIDを取得する
        stastus,data = conect.uid('search', None, 'ALL')

        uid_list = data[0].split()

        if uid_list:
            latest_uid = uid_list[-1].decode()

            with open(UID_FILE,'w') as f:
                f.write(latest_uid)

            print(f"初回起動:最新UID{latest_uid}を保存しました")

        else:
                print("メールは存在しません")
        conect.logout()
        exit()

    with open(UID_FILE,"r") as f:
        last_uid = int(f.read().strip())
    print(last_uid)

    conect = imaplib.IMAP4(CPI_IMAP_SERVER)

    try:
        print("サーバーの接続に成功")
        conect.login(CPI_EMAIL_USER, CPI_PASSWORD)
        print("ログインに成功しました")
        conect.select("INBOX")
        print("メールボックスの選択に成功しました")
        #未読メールを取得　　status=ステータス、data=データリスト メールIDが返ってくる
        #.uidに渡す引数を設定
        search_condition= f'UID {last_uid +1}:*'
        #指定したuidの数値以上のメールを取得
        status, data = conect.uid('search', None, search_condition)

        if data[0]:
            #data[b1][b2][b3]といった形にmsg_idsに代入しなおす
            print("新着メールあり")
            msg_ids = data[0].split()
            print(f"未読メールが{len(msg_ids)}通見つかりました順番に取得します。")

            for msg_id in msg_ids[:3]:
                #対象のメールIDのメールデータ(bytes型)を丸ごとダウンロード 取得する情報を指定 bytes型で取得
                status,msg_data = conect.fetch(msg_id,"(RFC822)")


                for response_part in msg_data:
                    # response_partはタプルが続いた後最後にメールの終わりを示すバイト列が入っているため判定
                    if isinstance(response_part,tuple):
                        #タプルの[1]の要素にメール内容が入っているのは固定
                        raw_message = response_part[1]
                        #バイト型の一列のデータを、本文や件名、添付ファイルなどにわけ、メールオブジェクトとして返す
                        msg = email.message_from_bytes(raw_message)
                        #メールヘッダにかかれている文字で表現された文字を、Datetimeオブジェクトに変換する
                        mail_date = parsedate_to_datetime(msg["Date"])
                        # JSTに変換
                        mail_date = mail_date.astimezone(JST)
                        formatdate = mail_date.strftime('%Y-%m-%d %H:%M:%S')

                        #subject（件名）を取得する
                        subject_header = decode_header(msg["subject"])[0]
                        # 本文(件名)[0]と文字コード[1] デコードをかける
                        subject =decode_str(subject_header[0],subject_header[1])

                        body = get_email_body(msg)

                        print("-" * 50)
                        print(f"【メールID】: {msg_id.decode('utf-8')}")
                        print(f"【件名】: {subject}")
                        print(f"【受信日時(JST)】: {formatdate}")
                        print(f"【本文】:\n{body}")
                        print("-" * 50)

                        print(formatdate)
                        print(type(formatdate))
                        #WEBHOOKを使用し、chatに出力
                        message = {
                            "text":f"受信日時:{formatdate} \n"
                                   f"受信アカウント: {CPI_EMAIL_USER}\n"
                                   f"件名: {subject}"
                        }

                        response=requests.post(
                            WEBHOOK_URL,
                            json=message
                        )
                        print(response.status_code)
                        print(response.text)

                        #データベースにメール情報を登録(SQL)
                        insert_user(formatdate,CPI_EMAIL_USER,subject)

        if msg_ids:
            # 今回処理した最大3通のうち、最後の要素のUIDをデコード
            last_processed_uid = msg_ids[:3][-1].decode('utf-8')

            with open(UID_FILE, "w") as f:
                f.write(last_processed_uid)
            print(f"【システム】次回の重複防止のため、最後に処理したUID {last_processed_uid} を保存しました。")

        else:
            print('新着メールなし')
            conect.logout()
            return

    except Exception as e:
        print(f"【デバッグ】エラーが発生しました{e}")

if __name__ == "__main__":
    main()
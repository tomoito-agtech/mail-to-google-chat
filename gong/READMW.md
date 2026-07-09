# メール受信・Google Chat通知・Actian Zen保存プログラム

## 概要

直近10分間に受信したメールを取得し、Google Chatへ通知したうえで、Actian Zen データベースへ保存する Python プログラムです。

本プログラムでは、Actian Zen への保存確認のため、以下の2種類の方法でメール情報を保存します。

```text
1. SQLAlchemy 経由で保存
2. Btrieve API 経由で保存
```

そのため、同一メールが2件登録される場合があります。
これは、SQLAlchemy と Btrieve API の両方で保存処理が動作していることを確認するための仕様です。

メール接続情報、Google Chat の Webhook URL、Actian Zen 接続情報、Btrieve ファイルパスは `.env` ファイルで管理し、パスワードなどの機密情報をコード内に直接記述しないようにしています。

## 主な機能

```text
・IMAP サーバーへ接続し、直近10分間に受信したメールを取得する
・メールの受信日時、件名、本文を解析する
・Google Chat へ受信通知を送信する
・SQLAlchemy 経由で Actian Zen にメール情報を保存する
・Btrieve API 経由で Actian Zen にメール情報を保存する
```

## 使用技術

```text
Python
IMAP
python-dotenv
requests
SQLAlchemy
sqlalchemy-zen
btrievePython
Actian Zen
Btrieve API
Google Chat Webhook
```

## ファイル構成

```text
gong/
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── core/
│   ├── __init__.py
│   ├── config.py
│   └── models.py
├── mail/
│   ├── __init__.py
│   ├── mail_receiver.py
│   ├── mail_fetcher.py
│   └── mail_parser.py
├── chat/
│   ├── __init__.py
│   └── chat_notifier.py
├── zen/
│   ├── __init__.py
│   ├── sql_repository.py
│   └── btrieve_repository.py
└── sql/
    └── create_received_mails.sql
```

各ファイルの役割は以下の通りです。

```text
main.py
    プログラムの入口です。
    メール取得、Google Chat通知、Actian Zen保存処理を順番に実行します。

core/config.py
    .env ファイルから各種設定情報を読み込みます。

core/models.py
    メール設定、受信メール、Google Chat設定、Zen接続設定などのデータ構造を定義します。

mail/mail_receiver.py
    IMAP サーバーへ接続し、直近10分間のメールを取得します。

mail/mail_fetcher.py
    メールの受信日時や原始データを IMAP サーバーから取得します。
    INTERNALDATE の解析には imaplib.Internaldate2tuple を使用します。

mail/mail_parser.py
    メールの件名と本文を解析します。

chat/chat_notifier.py
    Google Chat Webhook を使用して通知メッセージを送信します。

zen/sql_repository.py
    SQLAlchemy を使用して Actian Zen にメール情報を保存します。

zen/btrieve_repository.py
    Btrieve API を使用して Actian Zen の MKD ファイルへメール情報を保存します。

sql/create_received_mails.sql
    received_mails テーブル作成用の SQL です。

requirements.txt
    実行に必要な Python パッケージを記載しています。

.env.example
    .env ファイルの作成例です。
    実際のパスワード、Webhook URL、ファイルパスは記載していません。

.gitignore
    .env や仮想環境フォルダなど、GitHub にアップロードしないファイルを指定しています。
```

## 実行環境

```text
Python 3.10 以上
Actian Zen が利用できる環境
Btrieve API が利用できる環境
```

## セットアップ方法

### 1. 仮想環境を作成する

Windows の場合：

```bash
python -m venv venv
venv\Scripts\activate
```

macOS / Linux の場合：

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. 必要なパッケージをインストールする

```bash
pip install -r requirements.txt
```

### 3. `.env` ファイルを作成する

`.env.example` をコピーして `.env` を作成します。

Windows の場合：

```bash
copy .env.example .env
```

macOS / Linux の場合：

```bash
cp .env.example .env
```

作成した `.env` に、実際の接続情報を記入します。

```env
MAIL_HOST=your_mail_host
MAIL_PORT=143
MAIL_USER=your_mail_address
MAIL_PASSWORD=your_mail_password

GOOGLE_CHAT_WEBHOOK_URL=your_google_chat_webhook_url

ZEN_DATABASE_URL=your_zen_database_url

BTRIEVE_FILE_PATH=your_btrieve_mkd_file_path
```

※ `.env` にはパスワード、Webhook URL、実際のファイルパスなどの機密情報を記載するため、GitHub にはアップロードしません。

## 実行方法

以下のコマンドで実行します。

```bash
python main.py
```

## Google Chat 通知内容

Google Chat には以下の内容を通知します。

```text
受信日時
受信アカウント
件名
```

通知例：

```text
受信日時: 2026-06-29 11:22:57+09:00
受信アカウント: user@example.com
件名: テストメール
```

## Actian Zen への保存内容

`received_mails` テーブルに以下の内容を保存します。

```text
received_dt       メール受信日時
received_account  受信アカウント
subject           件名
body              本文
created_at        データ保存日時
```

本プログラムでは、保存確認のために以下の2種類の方法で保存しています。

```text
SQLAlchemy 経由
Btrieve API 経由
```

そのため、同一メールが2件登録される場合があります。

## Btrieve API 保存時の注意点

Btrieve API では SQL のようにカラム名を指定して保存するのではなく、DDF の record レイアウトに基づいて record bytes を作成して保存します。

本プログラムでは、DDF の情報に基づき、以下の内容を手動で設定しています。

```text
NULL 標志
TIMESTAMP
Zstring
LONGVARCHAR / Clob
body の正文长度
body の正文开始位置
```

また、Btrieve API では文字列を bytes として保存するため、現在の Zen / DDF の文字コードに合わせて `cp932` を使用しています。

## 出力例

メールが取得できた場合：

```text
====================================================================================================
Google Chat 通知完成
Actian Zen SQL 保存完成
Actian Zen Btrieve 保存完成
受信日時: 2026-06-29 11:22:57+09:00
受信アカウント: user@example.com
件名: テストメール
```

直近10分間に受信したメールがない場合：

```text
直近10分間のメールはありません。
```

## 注意事項

```text
・パスワードなどの機密情報は .env に記載します。
・.env は Git 管理対象外にします。
・Google Chat Webhook URL は GitHub にアップロードしません。
・Btrieve の実ファイルパスは GitHub にアップロードしません。
・Btrieve API で保存する場合、DDF の record レイアウトと文字コードに注意が必要です。
・本プログラムでは、SQLAlchemy と Btrieve API の両方で保存するため、同一メールが2件保存される場合があります。
```

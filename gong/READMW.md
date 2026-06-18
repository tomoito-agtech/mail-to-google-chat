# メール受信プログラム

## 概要

直近10分間に受信したメールを取得し、件名と本文をターミナルに `print` 出力する Python プログラムです。

メール接続情報は `.env` ファイルで管理し、パスワードなどの機密情報をコード内に直接記述しないようにしています。

## 使用技術

* Python
* IMAP
* python-dotenv

## ファイル構成

```text
1_mail/
├── main.py
├── config.py
├── models.py
├── mail_receiver.py
├── mail_fetcher.py
├── mail_parser.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

各ファイルの役割は以下の通りです。

```text
main.py
    プログラムの入口。メール取得処理を呼び出し、件名と本文を print 出力します。

config.py
    .env ファイルからメール接続情報を読み込みます。

models.py
    受信メールのデータ構造を定義します。

mail_receiver.py
    IMAP サーバーへ接続し、直近10分間のメールを取得します。

mail_fetcher.py
    メールの受信日時や原始データを IMAP サーバーから取得します。

mail_parser.py
    メールの件名と本文を解析します。

requirements.txt
    実行に必要な Python パッケージを記載しています。

.env.example
    .env ファイルの作成例です。実際のパスワードは記載していません。

.gitignore
    .env や仮想環境フォルダなど、GitHub にアップロードしないファイルを指定しています。
```

## 実行環境

Python 3.10 以上を想定しています。

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

作成した `.env` に、実際のメール接続情報を記入します。

```env
MAIL_HOST=your_mail_host
MAIL_PORT=143
MAIL_USER=your_mail_address
MAIL_PASSWORD=your_password
```

※ `.env` にはパスワードなどの機密情報を記載するため、GitHub にはアップロードしません。

## 実行方法

以下のコマンドで実行します。

```bash
python main.py
```

## 出力例

```text
==========
件名: テストメール
本文:
これはテストメールです。
```

直近10分間に受信したメールがない場合は、以下のように表示されます。

```text
直近10分間のメールはありません。
```

## 注意事項

* パスワードなどの機密情報は `.env` に記載します。
* `.env` は `.gitignore` により Git 管理対象外にしています。
* 仮想環境フォルダ `venv/` は GitHub にアップロードしません。
* このプログラムでは IMAP を使用してメールを受信します。

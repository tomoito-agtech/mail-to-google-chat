# メール転送・通知プログラム

## 概要
前回受信したメール以降に、新規でメールがあればgoogle chatへ出力するプログラムです。
受信日時、受信アカウント、件名を出力し、Actian Zenに保存します。

ファイル構成
├── .gitignore              
├── requirements.txt      
└── src/                   
    ├── last_uid.txt      
    ├── mail_load_Btrive.py 
    ├── mail_load_SQL.py  
    ├── zen_db_Betrive.py
    └── zen_db_SQL.py   

##各ファイルの役割
.gitignore
    # Gitの管理から除外する設定ファイル
requirements.txt         
    # 必要な外部ライブラリの一覧
last_uid.txt         
    # 最後に読み込んだメールのUIDを記録するファイル
mail_load_Btrive.py  
    # Btriveからメールを読み込むメイン処理
mail_load_SQL.py     
    # SQLからメールを読み込むメイン処理
zen_db_Betrive.py    
    # Btrive用データベースの接続・操作処理
zen_db_SQL.py        
    # SQL用データベースの接続・操作処理
    
## 必要な環境
- Python 3.x
- 依存ライブラリ（requirements.txt を参照）

セットアップ方法
1. 仮想環境を作成する
Windows の場合：

python -m venv venv
venv\Scripts\activate
macOS / Linux の場合：

python3 -m venv venv
source venv/bin/activate
2. 必要なパッケージをインストールする
pip install -r requirements.txt
3. .env ファイルを作成する
.env.example をコピーして .env を作成します。

Windows の場合：

copy .env.example .env
macOS / Linux の場合：

cp .env.example .env
作成した .env に、実際のメール接続情報を記入します。

CPI_IMAP_SERVER=aaaaaaaaa.example.co.jp
CPI_EMAIL=aaaaaaaaa.example.co.jp
CPI_PASSWORD=aaaaaaaaa
WEBHOOK_URL = "aaaaaaaaa"
※ .env にはパスワードなどの機密情報を記載するため、GitHub にはアップロードしません。

## 起動方法
1. ターミナルを開きます。
2. 以下のコマンドを実行してプログラムを起動します。
   SQLver
     python src/mail_load_SQL.py
   
   Btrivever
     python src/mail_load_Btrive.py


## 注意事項
- 実行前に、各種設定ファイル（DBの接続情報など）が正しいか確認してください。

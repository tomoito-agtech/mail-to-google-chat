import pyodbc
def get_connection():

    conn_str =(
        "DSN=mailrecord;" #ODBCシステム　DSN の名前に対応
        "DBQ=MAILRECORD;"    #ここで使用するデータベースを指定します
    )

    return pyodbc.connect(conn_str)

def test_connection():

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        return True,row[0]
    except Exception as e:
        return False, str(e)

def insert_user(mailtime,account,subject):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO record (mailtime,account,subject)
        VALUES (?,?,?)
        """, (mailtime,account,subject))
    conn.commit()
    cursor.close()
    conn.close()

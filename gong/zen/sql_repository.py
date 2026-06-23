"""
使用SQLAlchemy连接Zen数据库
"""
from sqlalchemy import create_engine,text
from core.models import ZenSqlConfig,ReceivedMail
from datetime import datetime

class ZenSqlRepository:

    def __init__(self,config:ZenSqlConfig):
        """
        建立连接
        """
        self.engine = create_engine(config.database_url)

    def test_connection(self):
        """
        链接测试
        :return:
        """
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.fetchone()

    def save_mail(self,mail:ReceivedMail,received_account:str) -> None:
        """
        保存到数据库(用SQL)

        received_datetime  邮件接收时间
        received_account   收件账号
        subject            件名
        body               本文
        created_at         数据保存时间

        :param mail: ReceivedMail
        :param received_account: str
        :return:
        """
        sql = text("""
                   insert into "received_mails"(received_dt, received_account, subject, body, created_at)
                   values (:received_dt,:received_account,:subject, :body, :created_at)
                   """)

        with self.engine.begin() as conn:
            # 把右边字典里的数据，交给前面的 SQL 语句
            # 然后执行 SQL
            conn.execute(sql, {
                'received_dt': mail.received_dt,
                'received_account': received_account,
                'subject': mail.subject,
                'body': mail.body,
                'created_at': datetime.now()
            })


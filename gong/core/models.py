"""
实体类
"""
from dataclasses import dataclass
from datetime import datetime


# e-mail情報
@dataclass
class MailConfig:
    host: str
    port: int
    user: str
    password: str

# e-mailBody
@dataclass
class ReceivedMail:
    received_dt: datetime
    subject: str
    body: str

# googleChat
@dataclass
class GoogleChatConfig:
    webhook_url: str

# SQL
@dataclass
class ZenSqlConfig:
    database_url: str

# Btrieve
@dataclass
class BtrieveConfig:
    file_path: str
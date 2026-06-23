"""
读取 .env 配置
"""
# 导包
import os
from pathlib import Path
from dotenv import load_dotenv
from core.models import MailConfig, GoogleChatConfig,ZenSqlConfig

def _load_env() :
    """
    取得环境变量
    :return:
    """
    # 获取.env 文件路径（以当前 config.py 目录为基础）
    env_path = Path(__file__).resolve().parent.parent / ".env"
    # 读取 .env 文件，dotenv会把env内容放到os.environ里，os可直接读取
    load_dotenv(dotenv_path=env_path)

def _get_required_env(env_key: str,error_message:str) -> str:
    """
    判断env文件里面是否有值
    :param env_key:
    :param error_message:
    :return: alue
    """
    # os读取env
    value = os.getenv(env_key)
    # 判断数据是否都有
    if value is None or len(value) == 0 or value == "":
        raise ValueError(error_message)
    return value




def get_mail_config() -> MailConfig:
    """
    链接邮箱服务器的必要数据
    :return: MailConfig
    """
    # 获得环境变量
    _load_env()

    # 拿到值后判断
    host = _get_required_env(env_key="MAIL_HOST",error_message="env の MAIL_HOST が不足")
    port = _get_required_env(env_key="MAIL_PORT",error_message="env の MAIL_PORT が不足")
    user = _get_required_env(env_key="MAIL_USER",error_message="env の MAIL_USER が不足")
    password = _get_required_env(env_key="MAIL_PASSWORD",error_message="env の MAIL_PASSWORD が不足")


    # 判断ok则返回结果
    return MailConfig(
        host=host,
        port=int(port),
        user=user,
        password=password,
    )


def get_google_chat_config() -> GoogleChatConfig:
    """
    连接能到googleChat的必要数据
    :return: GoogleChatConfig
    """
    _load_env()

    webhook_url = _get_required_env(env_key="GOOGLE_CHAT_WEBHOOK_URL", error_message="env のgoogleのwebhook設定が不足")

    return GoogleChatConfig(webhook_url= webhook_url)


def get_zen_sql_config() -> ZenSqlConfig:
    """
    链接到Zen数据库的必要数据
    :return: ZenSqlConfig
    """
    _load_env()

    database_url= _get_required_env(env_key="ZEN_SQLALCHEMY_URL",error_message="env の Zen SQLAlchemy URL が不足")

    return ZenSqlConfig(database_url=database_url)
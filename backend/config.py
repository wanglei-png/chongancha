"""应用配置管理，从 .env 文件读取配置"""

from functools import lru_cache

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # 应用配置
    APP_ENV: str = "development"
    APP_DEBUG: bool = True

    # MySQL 数据库配置
    DB_HOST: str = "116.62.175.15"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "Wanglei940414!"
    DB_DATABASE: str = "pet_health"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
            f"?charset=utf8mb4"
        )

    # Redis 配置
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # 微信小程序配置
    WX_APPID: str = ""
    WX_SECRET: str = ""

    # JWT 配置
    JWT_SECRET_KEY: str = "change-me-to-a-random-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24小时

    # 大模型 API 配置
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"

    # 微信支付配置
    WX_MCH_ID: str = ""
    WX_API_KEY: str = ""
    WX_NOTIFY_URL: str = ""

    # V2.1 向量检索配置
    MILVUS_DB_PATH: str = "./milvus_pet_health.db"

    # V2.2 管理后台配置
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "changeme123"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 允许 .env 中有未定义的字段


@lru_cache()
def get_settings() -> Settings:
    """获取全局单例配置对象"""
    return Settings()


settings = get_settings()

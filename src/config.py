from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
import os


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / ".env.example")


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "DifyCRM")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "5055"))
    mysql_host: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "123456")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "dify_crm")
    public_api_base: str = os.getenv("PUBLIC_API_BASE", "http://host.docker.internal:5055")


@lru_cache
def get_settings() -> Settings:
    return Settings()

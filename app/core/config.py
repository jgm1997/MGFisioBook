from functools import lru_cache

from dotenv import load_dotenv
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    supabase_url: str
    supabase_publishable_key: str
    supabase_secret_key: str
    database_url: str
    smtp_user: str
    smtp_password: str
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587

    model_config = ConfigDict(env_file=".env", extra="allow")


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()

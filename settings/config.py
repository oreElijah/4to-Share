from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Configs(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int   
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_TIMEOUT: int = 100
    MAIL_MAX_RETRIES: int = 2
    MAIL_RETRY_DELAY_SECONDS: float = 1.5
    MAIL_ENABLED: bool = True
    MAIL_FAIL_SILENTLY: bool = True
    RESEND_API_KEY: Optional[str] = None
    RESEND_API_URL: str = "https://api.resend.com/emails"
    UPSTASH_REDIS_REST_URL: str
    UPSTASH_REDIS_REST_TOKEN: str
    DOMAIN: str 
    FRONTEND_URL: str
    UPLOAD_PATH: str
    BASE_DIR: str  
    SENTRY_DSN: str
    CACHE_EXPIRATION_TIME: int
    IMAGEKIT_PRIVATE_KEY: str
    IMAGEKIT_PUBLIC_KEY: str
    IMAGEKIT_URL_ENDPOINT: str



    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

# class ProductionConfig(GlobalConfig):
#     ...

# class DevelopmentConfig(GlobalConfig):
#     CORS_ORIGIN: str


GlobalConfig = Configs() # type: ignore

def get_config() -> Configs:
    return GlobalConfig
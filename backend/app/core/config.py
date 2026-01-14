import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str

    FRONTEND_URL: str

    USER : str
    PASSWORD : str
    DB_NAME : str

    # Kakao
    KAKAO_CLIENT_ID: str
    KAKAO_CLIENT_SECRET: str
    KAKAO_REDIRECT_URI: str
    KAKAO_AUTH_URL: str
    KAKAO_TOKEN_URL: str
    KAKAO_USER_INFO_URL: str

    # Naver
    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: str
    NAVER_REDIRECT_URI: str
    NAVER_AUTH_URL: str
    NAVER_TOKEN_URL: str
    NAVER_USER_INFO_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # LLM API
    GEMINI_API_KEY : str
    TAVILY_API_KEY : str  

    class Config:
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(current_file_dir)
        backend_dir = os.path.dirname(app_dir)

        env_file = os.path.join(backend_dir, ".env")
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
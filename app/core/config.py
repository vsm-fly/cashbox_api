from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"

    ACCESS_TOKEN_MINUTES: int = 30
    # Preferred name used by services
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    # Backward-compatible alias (if someone already uses REFRESH_TOKEN_DAYS)
    REFRESH_TOKEN_DAYS: int | None = None

    JOBS_DIR: str = "./var/jobs"

    @property
    def refresh_days(self) -> int:
        return int(self.REFRESH_TOKEN_DAYS or self.REFRESH_TOKEN_EXPIRE_DAYS)


settings = Settings()

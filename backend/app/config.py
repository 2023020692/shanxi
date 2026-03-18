from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://shanxi:shanxi123@db:5432/shanxi_gis"
    redis_url: str = "redis://redis:6379/0"
    data_dir: str = "/app/data"
    secret_key: str = "change-me-in-production"
    titiler_url: str = "http://titiler:8080"

    @property
    def raw_dir(self) -> Path:
        return Path(self.data_dir) / "raw"

    @property
    def processed_dir(self) -> Path:
        return Path(self.data_dir) / "processed"

    @property
    def reports_dir(self) -> Path:
        return Path(self.data_dir) / "reports"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

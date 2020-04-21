from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    api_host: str = Field(..., env='API_HOST')

from pydantic import BaseSettings, Field
from functools import lru_cache


class WsSettings(BaseSettings):
    api_host: str = Field(..., env='API_HOST')


@lru_cache()
def get_settings(env_file):
    return WsSettings(_env_file=env_file)

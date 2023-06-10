import enum
from typing import Any, Dict, Optional, Union
import json

from pydantic import BaseSettings, PostgresDsn, validator


class EnvEnum(enum.Enum):
    development = 'development'
    production = 'production'
    test = 'test'
    local = 'local'
    stage = 'stage'


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"

    ASYNC_SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    SYNC_SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("ASYNC_SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_async_db_connection(
            cls,
            v: Optional[str],
            values: Dict[str, Any]
    ) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    @validator("SYNC_SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_sync_db_connection(
            cls,
            v: Optional[str],
            values: Dict[str, Any]
    ) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    REDIS_PORT: str
    REDIS_HOST: str
    REDIS_DB_BOT: str = "REDIS_DB_BOT"

    BLOCK_CYPHER_API_URL: str
    BLOCK_CYPHER_API: str

    BLOCK_CHAIR_API_URL: str

    API_ERC20_NETWORK: str
    ERC20_NETWORK_TYPE: str = "ETH_GOERLI"

    CRYPTOCOMPARY_API: str

    BITCOIN_PRIVATE_KEY: str
    BITCOIN_PUBLIC_KEY: str
    BITCOIN_ADDRESS: str

    ERC20_PRIVATE_KEY: str
    ERC20_PUBLIC_KEY: str
    ERC20_ADDRESS: str

    USDT_ADDRESS_CONTRACT: str
    USDT_ABI_CONTRACT: str

    TOKEN_TOKEN_ERC20: str

    BITCOIN_CHECK_TASK_SECONDS: int = 60 * 10
    BLOCK_CHAIR_NETWORK: str = "bitcoin"

    @validator("USDT_ABI_CONTRACT")
    def usdt_abi_contract_to_dict(
            cls,
            v: Union[str, dict],
            values: Dict[str, Any]
    ) -> Any:
        if isinstance(v, dict):
            return v

        return json.loads(v)

    class Config:
        case_sensitive = True


settings = Settings()

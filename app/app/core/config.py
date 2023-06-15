from typing import Any, Dict, Optional
from pydantic import (
    BaseSettings,
    PostgresDsn,
    validator,
    RedisDsn
)
from loguru import logger


class Settings(BaseSettings):
    SECRET_KEY: str

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str

    BASE_URL: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str

    REDIS_PORT: str
    REDIS_HOST: str

    SYNC_SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    ASYNC_SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    REDIS_URI: Optional[RedisDsn] = None

    # contract token in system
    USDT_ERC20_ADDRESS_CONTRACT: str
    USDT_ERC20_ABI_CONTRACT: str

    # system wallets
    BITCOIN_ADDRESS: str
    BITCOIN_PUBLIC_KEY: str
    BITCOIN_PRIVATE_KEY: str

    ERC20_ADDRESS: str
    ERC20_PUBLIC_KEY: str
    ERC20_PRIVATE_KEY: str

    # access data
    ALCHEMY_API_URL: str
    ALCHEMY_API_KEY: str

    WEBHOOK_ALCHEMY_TOKEN: str
    WEBHOOK_ALCHEMY_URL: str

    CHECK_RATES_URL_TOKENS: str # позволяет получить стоимость криптовалюты

    ETHERSCAN_API_URL: str
    ETHERSCAN_API_TOKEN: str
    ERC20_NETWORK_TYPE: str = "ETH_GOERLI"

    BLOCK_CYPHER_API_URL: str
    BLOCK_CYPHER_API_TOKEN: str
    BLOCK_CYPHER_API_URL_NETWORK: str

    BLOCKCHAIR_API_URL: str
    BLOCK_CHAIR_NETWORK: str

    @validator("SYNC_SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_sync_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
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

    @validator("ASYNC_SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_async_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
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

    @validator("REDIS_URI", pre=True)
    def assembled_redis_uri(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return RedisDsn.build(
            scheme="redis",
            host=values.get("REDIS_HOST"),
            port=values.get("REDIS_PORT"),
            path="/0"
        )

    ERC20_ADDRESS: str
    ERC20_PRIVATE_KEY: str

    BITCOIN_ADDRESS: str
    BITCOIN_PRIVATE_KEY: str

    class Config:
        case_sensitive = True


settings = Settings()

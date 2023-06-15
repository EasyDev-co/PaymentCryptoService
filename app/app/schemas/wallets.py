from uuid import UUID

from datetime import datetime

from pydantic import BaseModel, validator
from dependency_injector.wiring import Provide

from app.models.wallets import NetworkType, CryptocurrencyType


class WalletOut(BaseModel):
    address: str
    network: NetworkType

    class Config:
        orm_mode = True


class WalletCryptocurrencyOut(BaseModel):
    id: UUID
    wallet: WalletOut
    cryptocurrency: CryptocurrencyType
    balance: float

    @validator("balance", allow_reuse=True)
    def validate_min_cryptocurrency(cls, v, values, ):
        from app.main import app
        crypto_service = Provide[app.container.crypto_service].provider()
        return crypto_service(values['wallet'].network, values['cryptocurrency']).from_minimal_part(v)

    class Config:
        orm_mode = True


class CryptoTransactionHistory(BaseModel):
    id: UUID
    type: str
    count: float
    wallet_type: str
    created_at: datetime


class WalletGetData(BaseModel):
    wallet: WalletCryptocurrencyOut
    history: list[CryptoTransactionHistory]

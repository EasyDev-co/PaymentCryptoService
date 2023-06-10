from pydantic import BaseModel, Field, validator
from typing import Union

class Wallet(BaseModel):
    address: bytes
    private_key: bytes


class DynamicFeeTransaction(BaseModel):
    nonce: int
    gasPrice: int


class DynamicFeeTransactionETH(DynamicFeeTransaction):
    to: str
    value: int
    gas: int


class DynamicFeeTransactionERC20(DynamicFeeTransaction):
    chainId: int


class GasPrice(BaseModel):
    safe_gas_price: int
    propose_gas_price: int
    fast_gas_price: int


class AlchemyNotifySchemeRawСontract(BaseModel):
    value: Union[str, int] = Field(..., alias="rawValue")
    address: str =  None

    @validator("value")
    def validate_value(cls, v, **kwargs):
        return int(v, base=16)


class AlchemyNotifyScheme(BaseModel):
    sender_address: str = Field(..., alias="fromAddress")
    destination_address: str = Field(..., alias="toAddress")
    hash: str
    value: float = None
    asset: str = None

    @property
    def coin_name(self):
        return self.asset

    contract: AlchemyNotifySchemeRawСontract = Field(..., alias="rawContract")


class AllWebhooksList(BaseModel):
    id: str
    network: str
    is_active: str


class AllWebhooks(BaseModel):
    data: list[AllWebhooksList]


class WebhookAddedAndRemoved(BaseModel):
    webhook_id: str
    added_address: list
    removed_address: list
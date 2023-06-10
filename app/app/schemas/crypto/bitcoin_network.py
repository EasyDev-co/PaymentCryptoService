from pydantic import BaseModel


class BitcoinWallet(BaseModel):
    address: bytes
    private_key: bytes
    public_key: bytes
    wif: bytes


class AddressBalance(BaseModel):
    address: int


class TXInput(BaseModel):
    prev_hash: str
    output_index: int
    script: str
    output_value: int
    sequence: int
    addresses: list[str]
    script_type: str
    age: int


class TXOutput(BaseModel):
    value: int
    script: str
    spent_by: str
    addresses: list[str]
    script_type: str


class TX(BaseModel):
    block_height: int
    hash: str
    addresses: list[str]
    total: int
    fees: int
    size: int
    vsize: int
    preference: str
    relayed_by: str
    confirmed: str
    received: str
    ver: int
    lock_time: int
    double_spend: bool
    vin_sz: int
    vout_sz: int
    confirmations: int
    inputs: list[TXInput]
    outputs: list[TXOutput]


# Та же самая транзакция, но ещё вместе с tosign
# tosign - сообщение, которое нужно использовать при создании сигнатуры
class TXSceleton(BaseModel):
    tx: TX
    tosign: list[str]


class ConfirmedTransaction(BaseModel):
    hash: str
    status: str


class UnconfirmedTransaction(BaseModel):
    hash: str
    status: str

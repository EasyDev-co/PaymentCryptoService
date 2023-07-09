from uuid import uuid4
import enum

from app.models.types.decimals_int import NumericInt
from app.db.base_class import Base

from sqlalchemy import Column, Enum, ForeignKey, BigInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class NetworkType(enum.Enum):
    bitcoin_network = "bitcoin_network"
    erc20 = "erc20"
    trc20 = "trc20"


class CryptocurrencyType(str, enum.Enum):
    bitcoin = "bitcoin"
    ethereum = "ethereum"
    usdt = "usdt"
    usdt_trc20 = "usdt_trc20"
    trx = "trx"


def get_normal_name(type) -> str:
    if type == CryptocurrencyType.bitcoin:
        return "BTC"
    elif type == CryptocurrencyType.ethereum:
        return "ETH"
    elif type == CryptocurrencyType.usdt:
        return "USDT"
    elif type == CryptocurrencyType.usdt_trc20:
        return "USDT"
    elif type == CryptocurrencyType.trx:
        return "TRX"


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    network = Column(Enum(NetworkType))
    address = Column(String)
    public_key = Column(String)
    private_key = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    user = relationship("Users")

    def __str__(self) -> str:
         return self.address


class CryptocurrencyWallet(Base):
    __tablename__ = "tokenwallets"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    cryptocurrency = Column(Enum(CryptocurrencyType))
    balance = Column(NumericInt(precision=30, scale=0), default=0)  # integer because we take indivisible part
    actual_wallet_balance = Column(BigInteger, default=0)

    wallet = relationship("Wallet")
    user = relationship("Users")

    def __str__(self) -> str:
        return str(self.cryptocurrency) +\
               " " + str(self.user.username)\
               if self.user.username else ""

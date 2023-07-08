import datetime
import enum

from uuid import uuid4

from app.models.types.decimals_int import NumericInt

from app.db.base_class import Base
from app.models.wallets import NetworkType, CryptocurrencyType
from app.core.config import settings

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class CryptoTransaction(Base):
    __tablename__ = "cryptocurrencytransactions"

    class TransactionType(enum.Enum):
        out_system = "out"  # вывод денег из главного кошелька
        in_system = "in_system"  # ввод денег в главный кошелек
        in_wallet = "in_wallet"  # ввод денег в кошелек пользователя
        comission = "comission"  # ввод комисии на кошелек пользователя

    class StatusCryptoTransaction(enum.Enum):
        not_send = "not_send"
        pending = "pending"
        success = "success"
        fail = "fail"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)

    network = Column(Enum(NetworkType))
    cryptocurrency = Column(Enum(CryptocurrencyType))
    count = Column(NumericInt(precision=30, scale=0), default=0)
    receive_address = Column(String, nullable=True)
    status = Column(Enum(StatusCryptoTransaction), default=StatusCryptoTransaction.not_send)
    type = Column(Enum(TransactionType), default=TransactionType.out_system)
    wallet_crypto_id = Column(UUID(as_uuid=True), ForeignKey("tokenwallets.id"))
    transaction_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    start_on_transaction_id = Column(UUID(as_uuid=True), ForeignKey("cryptocurrencytransactions.id"), nullable=True)
    gas_price = Column(Numeric(precision=30, scale=0), default=0)
    text = Column(String, default="")
    comission = Column(NumericInt(precision=30, scale=0), nullable=True)  # нужна для рассчета комиссии

    start_on_transaction = relationship("CryptoTransaction", uselist=False, lazy='joined')
    wallet_crypto = relationship("CryptocurrencyWallet")

    @property
    def private_key(self):
        if self.type in [self.TransactionType.out_system, self.TransactionType.comission]:
            if self.network == NetworkType.erc20:
                return settings.ERC20_PRIVATE_KEY
            elif self.network == NetworkType.bitcoin_network:
                return settings.BITCOIN_PRIVATE_KEY
            elif self.network == NetworkType.trc20:
                return settings.TRC20_PRIVATE_KEY
        elif self.type == self.TransactionType.in_system:
            return self.wallet_crypto.wallet.private_key

    @property
    def public_key(self):
        if self.type in [self.TransactionType.out_system, self.TransactionType.comission]:
            if self.network == NetworkType.erc20:
                return settings.ERC20_PUBLIC_KEY
            elif self.network == NetworkType.bitcoin_network:
                return settings.BITCOIN_PUBLIC_KEY
            elif self.network == NetworkType.trc20:
                return settings.TRC20_PUBLIC_KEY
        elif self.type == self.TransactionType.in_system:
            return self.wallet_crypto.wallet.public_key

    @property
    def sender_address(self):
        if self.type in [self.TransactionType.out_system, self.TransactionType.comission]:
            if self.network == NetworkType.erc20:
                return settings.ERC20_ADDRESS
            elif self.network == NetworkType.bitcoin_network:
                return settings.BITCOIN_ADDRESS
            elif self.network == NetworkType.trc20:
                return settings.TRC20_ADDRESS
        elif self.type == self.TransactionType.in_system:
            return self.wallet_crypto.wallet.address

    @property
    def transaction_price(self):
        if self.start_on_transaction:
            if self.start_on_transaction.type == self.TransactionType.comission:
                return self.start_on_transaction.gas_price

    @property
    def use_transaction_price(self):
        if self.type == self.TransactionType.out_system:
            return False
        return True

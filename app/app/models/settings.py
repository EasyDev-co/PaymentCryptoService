import enum

from uuid import uuid4

from app.db.base_class import Base
from app.models.wallets import CryptocurrencyType

from sqlalchemy import Column, Integer, Enum, Float
from sqlalchemy.dialects.postgresql import UUID


class TaskType(enum.Enum):
    not_working = "not_working"
    pending = "pending"
    stoping = "stoping"


class Settings(Base):
    __tablename__ = 'settings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    minimum_ethereum_in = Column(Float, default=0)
    minimum_usdt_in = Column(Float, default=0)
    minimum_bitcoin_in = Column(Float, default=0)
    minimum_usdt_trc_in = Column(Float, default=0)

    usdt_comission_out_count = Column(Float, default=0)
    eth_comission_out_count = Column(Float, default=0)
    btc_comission_out_count = Column(Float, default=0)
    usdt_trc_comission_out_count = Column(Float, default=0)

    usdt_comission_out_percent = Column(Integer, default=0)
    eth_comission_out_percent = Column(Integer, default=0)
    btc_comission_out_percent = Column(Integer, default=0)
    usdt_trc_comission_out_percent = Column(Integer, default=0)

    erc20_gas_estimate = Column(Integer, nullable=True)
    usdt_trc_fee_limit = Column(Integer, nullable=True)

    transaction_active = Column(Enum(TaskType), default=TaskType.not_working)
    transaction_check_active = Column(Enum(TaskType), default=TaskType.not_working)
    transaction_bitcoin_wallet_check = Column(Enum(TaskType), default=TaskType.not_working)
    transaction_trc20_check = Column(Enum(TaskType), default=TaskType.not_working)

    def get_commision_for_out(self, cryptocurrency: CryptocurrencyType):
        if cryptocurrency == CryptocurrencyType.bitcoin:
            return self.btc_comission_out_percent
        elif cryptocurrency == CryptocurrencyType.ethereum:
            return self.eth_comission_out_percent
        elif cryptocurrency == CryptocurrencyType.usdt:
            return self.usdt_comission_out_percent
        elif cryptocurrency == CryptocurrencyType.usdt_trc20:
            return self.usdt_trc_comission_out_percent

    def get_comission_out_count(self, cryptocurrency: CryptocurrencyType):
        if cryptocurrency == CryptocurrencyType.bitcoin:
            return self.btc_comission_out_count
        elif cryptocurrency == CryptocurrencyType.ethereum:
            return self.eth_comission_out_count
        elif cryptocurrency == CryptocurrencyType.usdt:
            return self.usdt_comission_out_count
        elif cryptocurrency == CryptocurrencyType.usdt_trc20:
            return self.usdt_trc_comission_out_count
        
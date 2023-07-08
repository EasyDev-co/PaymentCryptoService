from enum import Enum
from typing import NamedTuple, Optional


class StatusTransaction(Enum):
    pending = "pending"
    success = "success"
    failed = "failed"


class Wallet(NamedTuple):
    public_key: str
    private_key: str
    address: str


class CryptocurrencyInterface:
    """
        Интерфейс любого сервиса криптовалют
    """

    async def create_wallet(self) -> Wallet:
        raise NotImplementedError

    async def get_middle_cost_transaction(self) -> int:
        raise NotImplementedError

    async def send_transaction(
            self,
            *,
            public_key: str,
            private_key: str,
            count: int,
            destination_address: str,
            sender_address: str,
            transaction_price: Optional[int] = None,
            use_transaction_price: bool = True
    ) -> str:
        raise NotImplementedError

    async def check_transaction(self, transaction_id: str) -> StatusTransaction:
        raise NotImplementedError

    def from_minimal_part(self, count: int) -> float:
        raise NotImplementedError

    def to_minimal_part(self, count: float) -> int:
        raise NotImplementedError

import enum
import httpx

from urllib.parse import urljoin

from loguru import logger
from app.core.config import settings
from app.models.wallets import CryptocurrencyType
from app.services.crypto.base import Wallet, StatusTransaction

from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.exceptions import TransactionNotFound, TransactionError

from .base import CryptocurrencyInterface


class TRC20TransactionStatus(enum.Enum):
    failed = "FAILED"
    success = "SUCCESS"


class TRXService(CryptocurrencyInterface):

    def __init__(self, tronscan_url: str) -> None:
        self.tronscan_url = tronscan_url
        self.client = Tron()

    async def create_wallet(self) -> Wallet:
        wallets = self.client.generate_address()
        return Wallet(
            address=wallets.get('base58check_address'),
            public_key=wallets.get('public_key'),
            private_key=wallets.get('private_key')
        )

    async def send_transaction(
            self,
            private_key: str,
            count: int,
            destination_address: str,
            sender_address: str,
            transaction_price: int | None = None,
            use_transaction_price: bool = True,
            *_args, **_kwargs

    ):
        logger.info(f"SENDER: {sender_address}")
        logger.info(f"RECIPIENT: {destination_address}")
        logger.info(f"AMOUNT: {count}")
        try:
            private_key = PrivateKey(bytes.fromhex(private_key))
            transaction = self.client.trx.transfer(
                    from_=sender_address,
                    to=destination_address,
                    amount=count
                )
            signed_txn = transaction.build().sign(private_key)
            result = signed_txn.broadcast()

            logger.info(f"TXID: {result.txid}")
            return result.txid
        except Exception as _exc:
            logger.error(f"Error: {_exc}")
            raise Exception

    @staticmethod
    def from_minimal_part(amount: int, **kwargs) -> float:
        return amount / 1_000_000

    @staticmethod
    def to_minimal_part(amount: float, **kwargs) -> float:
        return amount * 1_000_000

    async def check_transaction(self, transaction_id: str):
        try:
            trx = self.client.get_transaction(txn_id=transaction_id)
            result = trx.get('ret')[0].get('contractRet')
        except TransactionNotFound:
            return StatusTransaction.pending
        if result == TRC20TransactionStatus.failed:
            return StatusTransaction.failed
        else:
            return StatusTransaction.success

    async def get_middle_cost_transaction(self) -> int:
        pass

    async def check_balance(self, address: str):
        url = urljoin(
            base=self.tronscan_url,
            url=f"/api/account?address={address}&includeToken=true"
        )
        headers = {"accept": "application/json"}
        response = httpx.get(url, headers=headers)
        data = response.json()

        if 'error' in data:
            logger.error(f"Error: {data['error']}")
            return 0.0
        else:
            usdt_balance = 0.0
            for token in data['trc20token_balances']:
                if token['tokenName'] == 'Tether USD':
                    usdt_balance = round(float(token['balance']) * pow(10, -token['tokenDecimal']), 6)
                    return usdt_balance
            return usdt_balance


class USDTTrc20Service(TRXService):

    def __init__(
            self,
            usdt_trc20_contract_address: str,
            tronscan_url: str
    ) -> None:
        super().__init__(tronscan_url)
        try:
            self.usdt_contract_address = self.client.get_contract(
                usdt_trc20_contract_address
            )
        except Exception as _exc:
            logger.error(f"Error: {_exc}")

    async def send_transaction(
            self,
            private_key: str,
            count: int,
            destination_address: str,
            sender_address: str,
            transaction_price: int | None = None,
            use_transaction_price: bool = True,
            *_args, **_kwargs
    ):
        logger.info(f"SENDER: {sender_address}")
        logger.info(f"RECIPIENT: {destination_address}")
        logger.info(f"AMOUNT: {count}")
        try:
            private_key = PrivateKey(bytes.fromhex(private_key))
            txn = self.usdt_contract_address.functions.transfer(
                        destination_address,
                        count
            ).with_owner(sender_address).fee_limit(10_000_000_000).build().sign(private_key)
            result = txn.broadcast()
            logger.info(f"RESULT USDT: {result.txid}")
            return result.txid
        except Exception as _exc:
            logger.error(f"Error: {_exc}")
            raise Exception


class TRC20Network:

    def __init__(
            self,
            trx_service: TRXService,
            usdt_trc20_service: USDTTrc20Service
    ) -> None:
        self._trx_service = trx_service
        self._usdt_trc20_service = usdt_trc20_service

        self._mapping = {
            CryptocurrencyType.usdt_trc20: self._usdt_trc20_service,
            CryptocurrencyType.trx: self._trx_service

        }

    def __call__(self, token: CryptocurrencyType) -> TRXService:
        return self._mapping[token]

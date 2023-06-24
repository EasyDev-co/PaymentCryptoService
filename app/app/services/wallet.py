from loguru import logger

from typing import Callable
from uuid import UUID
from typing import Optional


from app.repository.transactions import RepositoryCryptoTransaction
from app.repository.settings import RepositorySettings
from app.repository.wallet import RepositoryWallet, RepositoryCryptoWallet
from app.repository.user import RepositoryUser

from app.workers.add_address_to_webhook import AddAddressToWebhookErc20

from app.models.wallets import NetworkType, CryptocurrencyType
from app.models.transactions import CryptoTransaction
from app.models.wallets import CryptocurrencyWallet

from app.services.crypto import CryptoService

from app.exceptions import wallet_exceptions


class WalletService:

    def __init__(
            self,
            repository_wallet: RepositoryWallet,
            repository_cryptocurrency_wallet: RepositoryCryptoWallet,
            repository_crypto_transaction: RepositoryCryptoTransaction,
            add_address_to_webhook_erc20_task: AddAddressToWebhookErc20,
            crypto_service: CryptoService,
            repository_settings: RepositorySettings,
            repository_user: RepositoryUser
    ) -> None:
        self._repository_wallet = repository_wallet
        self._repository_cryptocurrency_wallet = repository_cryptocurrency_wallet
        self._crypto_service = crypto_service
        self._repository_crypto_transaction = repository_crypto_transaction
        self._add_address_to_webhook_erc20_task = add_address_to_webhook_erc20_task
        self._repository_settings = repository_settings
        self._repository_user = repository_user

    async def _get_or_create_wallet_network(
            self,
            network: NetworkType,
            user_id: UUID,
            hook_after_create: Optional[Callable] = None
    ):
        wallet_db = self._repository_wallet.get(network=network, user_id=user_id)
        if not wallet_db:
            wallet = await self._crypto_service(network).create_wallet()
            if hook_after_create:
                hook_after_create(address=wallet.address)
            wallet_db = self._repository_wallet.create(
                obj_in={
                    "network": network,
                    "user_id": user_id,
                    "address": wallet.address,
                    "private_key": wallet.private_key,
                    "public_key": wallet.public_key,
                }
            )

        return wallet_db

    async def _get_or_create_wallet_coin(
            self,
            network: NetworkType,
            user_id: UUID,
            cryptocurrency_type: CryptocurrencyType,
            hook_after_create: Optional[Callable] = None
    ):
        wallet_network = await self._get_or_create_wallet_network(
            network=network,
            user_id=user_id,
            hook_after_create=hook_after_create
        )
        if not self._repository_cryptocurrency_wallet.get(
                wallet_id=wallet_network.id,
                cryptocurrency=cryptocurrency_type
        ):
            return self._repository_cryptocurrency_wallet.create({
                "wallet_id": wallet_network.id,
                "cryptocurrency": cryptocurrency_type,
                "user_id": user_id,
                "balance": 0
            })

    async def create_all_wallets(self, user_id: str):
        await self._get_or_create_wallet_coin(
                NetworkType.bitcoin_network,
                user_id,
                CryptocurrencyType.bitcoin
            )
        await self._get_or_create_wallet_coin(
                NetworkType.erc20,
                user_id,
                CryptocurrencyType.ethereum,
                self._add_address_to_webhook_erc20_task.delay
            )
        await self._get_or_create_wallet_coin(
                NetworkType.erc20,
                user_id,
                CryptocurrencyType.usdt,
                self._add_address_to_webhook_erc20_task.delay
            )

    async def get_wallets(self, user_id: str):
        user = self._repository_user.get(user_id=user_id)
        logger.info(f"{user.id}")
        return self._repository_cryptocurrency_wallet.list(user_id=user.id)

    async def get_wallet(self, user_id: str, wallet_id: str):
        user = self._repository_user.get(user_id=user_id)
        wallet = self._repository_cryptocurrency_wallet.get(user_id=user.id, id=wallet_id)
        crypto_transactions_and_deals = [
            {
                "id": transaction.id,
                "type": "transaction",
                "count": self._crypto_service(
                    wallet.wallet.network,
                    wallet.cryptocurrency
                ).from_minimal_part(transaction.count),
                "wallet_type": "in" if transaction.type == transaction.TransactionType.in_system else "out",
                "created_at": transaction.created_at,
                "commision": self._crypto_service(
                    wallet.wallet.network,
                    wallet.cryptocurrency
                ).from_minimal_part(transaction.comission) if transaction.comission else None
            } for transaction in self._repository_crypto_transaction.transaction_history(wallet_crypto_id=wallet.id)
        ]

        return {
            "wallet": wallet,
            "history": crypto_transactions_and_deals
        }

    async def get_wallet_by_coin_type_and_update(
            self,
            user_id: str,
            coin_type: str,
            new_balance: int
    ):
        wallet = self._repository_cryptocurrency_wallet.get(
            user_id=user_id,
            cryptocurrency=coin_type
        )
        balance = wallet.balance + new_balance
        self._repository_cryptocurrency_wallet.update(
            db_obj=wallet,
            obj_in={"balance": balance}
        )

    async def create_send_transaction(
            self,
            wallet_crypto: CryptocurrencyWallet,
            address_send: str,
            count: int
    ):
        if wallet_crypto.wallet.address == address_send:
            raise wallet_exceptions.UserErrorWallet(f"Вы не можете выполнить это действие")

        count = self._crypto_service(wallet_crypto.wallet.network, wallet_crypto.cryptocurrency).to_minimal_part(count)
        self._repository_crypto_transaction.create(
            {
                "network": wallet_crypto.wallet.network,
                "cryptocurrency": wallet_crypto.cryptocurrency,
                "count": count,
                "receive_address": address_send,
                "wallet_crypto_id": wallet_crypto.id,
                "status": CryptoTransaction.StatusCryptoTransaction.on_confirmed
            }
        )

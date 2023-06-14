from .base import Base

from app.services.crypto.btc import Bitcoin

from app.repository.wallet import RepositoryWallet, RepositoryCryptoWallet
from app.repository.transactions import RepositoryCryptoTransaction
from app.repository.settings import RepositorySettings

from app.models.wallets import NetworkType
from app.models.transactions import CryptoTransaction
from app.models.settings import TaskType

from app.core.config import settings


class CheckBitcoinWallet(Base):

    def __init__(self, bitcoin_service: Bitcoin, repository_wallet: RepositoryWallet,
                 repository_crypto_transaction: RepositoryCryptoTransaction,
                 repository_cryptocurrency_wallet: RepositoryCryptoWallet,
                 repository_settings: RepositorySettings, *args, **kwargs):
        self._bitcoin_service = bitcoin_service
        self._rep_wallet = repository_wallet
        self._rep_cryptocurrency_wallet = repository_cryptocurrency_wallet
        self._repository_crypto_transaction = repository_crypto_transaction
        self._repository_settings = repository_settings
        super().__init__(*args, **kwargs)

    async def proccess(self, *args, **kwargs):
        wallets_bitcoins = self._rep_wallet.get_list_addresses(network=NetworkType.bitcoin_network)
        wallets_to_check = []
        settings_db = self._repository_settings.get()

        if settings_db.transaction_bitcoin_wallet_check != TaskType.not_working:
            return

        self._repository_settings.update(
            db_obj=settings_db,
            obj_in={
                "transaction_bitcoin_wallet_check": TaskType.pending
            }
        )

        self.session.commit()

        for wallets_bitcoin in wallets_bitcoins:
            wallets_to_check.append(wallets_bitcoin[0])

        try:
            result = await self._bitcoin_service.check_balances(wallets_to_check)
        except Exception as e:
            self._repository_settings.update(
                db_obj=settings_db,
                obj_in={
                    "transaction_bitcoin_wallet_check": TaskType.not_working
                }
            )
            self.session.commit()
            raise e

        if result:
            for bitcoin_wallet in result.items():
                wallet = self._rep_wallet.get(address=bitcoin_wallet[0])
                wallet_cryptocurrency = self._rep_cryptocurrency_wallet.get(wallet_id=wallet.id)
                new_count = bitcoin_wallet[1]
                if new_count > 0 and \
                        self._bitcoin_service.from_minimal_part(new_count) >= settings_db.minimum_bitcoin_in:
                    if not self._repository_crypto_transaction.get(
                            status=CryptoTransaction.StatusCryptoTransaction.pending,
                            type=CryptoTransaction.TransactionType.in_system,
                            wallet_crypto_id=wallet_cryptocurrency.id):
                        self._repository_crypto_transaction.create({
                            "network": wallet_cryptocurrency.wallet.network,
                            "cryptocurrency": wallet_cryptocurrency.cryptocurrency,
                            "count": bitcoin_wallet[1],
                            "receive_address": settings.BITCOIN_ADDRESS,
                            "type": CryptoTransaction.TransactionType.in_system,
                            "wallet_crypto_id": wallet_cryptocurrency.id,
                        })
                        count = bitcoin_wallet[1]
                        # TODO Добавить баланс пользователю.
                        self.session.commit()

        self._repository_settings.update(
            db_obj=settings_db,
            obj_in={
                "transaction_bitcoin_wallet_check": TaskType.not_working
            }
        )

        self.session.commit()

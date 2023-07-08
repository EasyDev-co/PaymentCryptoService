from .base import Base

from app.services.crypto.trc20 import TRXService, USDTTrc20Service

from app.repository.wallet import RepositoryWallet, RepositoryCryptoWallet
from app.repository.transactions import RepositoryCryptoTransaction
from app.repository.settings import RepositorySettings

from app.models.wallets import NetworkType, CryptocurrencyType
from app.models.transactions import CryptoTransaction
from app.models.settings import TaskType

from app.core.config import settings

from loguru import logger


class CheckTRC20Wallets(Base):

    def __init__(
            self,
            usdt_trc20_service: USDTTrc20Service,
            repository_wallet: RepositoryWallet,
            repository_crypto_transaction: RepositoryCryptoTransaction,
            repository_cryptocurrency_wallet: RepositoryCryptoWallet,
            repository_settings: RepositorySettings,
            *args, **kwargs
    ) -> None:
        self._usdt_trc20_service = usdt_trc20_service
        self._rep_wallet = repository_wallet
        self._rep_cryptocurrency_wallet = repository_cryptocurrency_wallet
        self._repository_crypto_transaction = repository_crypto_transaction
        self._repository_settings = repository_settings
        super().__init__(*args, **kwargs)

    async def proccess(self, *args, **kwargs):
        wallets_usdt = self._rep_wallet.get_list_addresses(network=NetworkType.trc20)
        settings_db = self._repository_settings.get()

        if settings_db.transaction_trc20_check != TaskType.not_working:
            return

        self._repository_settings.update(
            db_obj=settings_db,
            obj_in={
                "transaction_trc20_check": TaskType.pending
            }
        )

        self.session.commit()

        for wallet in wallets_usdt:
            result = await self._usdt_trc20_service.check_balance(
                address=wallet[0]
            )
            if result > 0 and result >= settings_db.minimum_usdt_trc_in:
                wallet = self._rep_wallet.get(address=wallet[0])
                wallet_cryptocurrency = self._rep_cryptocurrency_wallet.get(wallet_id=wallet.id)
                if not self._repository_crypto_transaction.get(
                        status=CryptoTransaction.StatusCryptoTransaction.not_send,
                        type=CryptoTransaction.TransactionType.in_system,
                        wallet_crypto_id=wallet_cryptocurrency.id,
                        cryptocurrency=CryptocurrencyType.usdt_trc20
                ):
                    if not self._repository_crypto_transaction.get(
                        status=CryptoTransaction.StatusCryptoTransaction.pending,
                        type=CryptoTransaction.TransactionType.in_system,
                        wallet_crypto_id=wallet_cryptocurrency.id,
                        cryptocurrency=CryptocurrencyType.usdt_trc20
                ):

                        waiting_to_up_balance_transaction = self._repository_crypto_transaction.create({
                            "network": NetworkType.trc20,
                            "type": CryptoTransaction.TransactionType.in_wallet,
                            "cryptocurrency": CryptocurrencyType.usdt_trc20,
                            "count": self._usdt_trc20_service.to_minimal_part(amount=result),
                            "status": CryptoTransaction.StatusCryptoTransaction.success,
                            "receive_address": wallet.address,
                            "wallet_crypto_id": wallet_cryptocurrency.id
                        })

                        transaction_commission = self._repository_crypto_transaction.create(
                            {
                                "network": wallet_cryptocurrency.wallet.network,
                                "cryptocurrency": CryptocurrencyType.trx,
                                "count": self._usdt_trc20_service.to_minimal_part(
                                    amount=settings_db.usdt_trc_comission_out_count
                                ),
                                "receive_address": wallet.address,
                                "type": CryptoTransaction.TransactionType.comission,
                                "wallet_crypto_id": wallet_cryptocurrency.id,
                                "status": CryptoTransaction.StatusCryptoTransaction.not_send,
                                "start_on_transaction_id": waiting_to_up_balance_transaction.id
                            }
                        )
                        self._repository_crypto_transaction.create(
                            {
                                "network": wallet_cryptocurrency.wallet.network,
                                "cryptocurrency": CryptocurrencyType.usdt_trc20,
                                "count": self._usdt_trc20_service.to_minimal_part(amount=result),
                                "receive_address": settings.TRC20_ADDRESS,
                                "type": CryptoTransaction.TransactionType.in_system,
                                "wallet_crypto_id": wallet_cryptocurrency.id,
                                "status": CryptoTransaction.StatusCryptoTransaction.not_send,
                                "start_on_transaction_id": transaction_commission.id
                            }
                        )

                        self.session.commit()

        self._repository_settings.update(
            db_obj=settings_db,
            obj_in={
                "transaction_trc20_check": TaskType.not_working
            }
        )

        self.session.commit()

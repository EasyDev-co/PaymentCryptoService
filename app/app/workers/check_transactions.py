from .base import Base

from app.services.crypto.base import StatusTransaction
from app.services.crypto import CryptoService
from app.services.rate import CheckCurrentCryptoCost

from app.repository.wallet import RepositoryCryptoWallet
from app.repository.transactions import RepositoryCryptoTransaction
from app.repository.settings import RepositorySettings
from app.repository.user import RepositoryUser

from app.models.wallets import get_normal_name
from app.models.transactions import CryptoTransaction
from app.models.settings import TaskType

from app.exceptions.erc20_exceptions import TransactionUnderPriced, TransactionInPool


class SendTransaction(Base):

    def __init__(self,
                 repository_crypto_transaction: RepositoryCryptoTransaction,
                 crypto_service: CryptoService,
                 repository_crypto_wallet: RepositoryCryptoWallet,
                 settings_repository: RepositorySettings,
                 *args, **kwargs
                 ):
        self._repository_crypto_transaction = repository_crypto_transaction
        self._crypto_service = crypto_service
        self._settings_repository = settings_repository
        self._repository_crypto_wallet = repository_crypto_wallet
        super().__init__(*args, **kwargs)

    async def proccess(self, *args, **kwargs):
        settings_db = self._settings_repository.get()
        if settings_db.transaction_active != TaskType.not_working:
            return
        self._settings_repository.update(
            db_obj=settings_db,
            obj_in={
                "transaction_active": TaskType.pending
            }
        )
        self.session.commit()

        transactions = self._repository_crypto_transaction.list(
            status=CryptoTransaction.StatusCryptoTransaction.not_send)
        for transaction in transactions:
            try:
                service = self._crypto_service(transaction.network, transaction.cryptocurrency)
                if transaction.start_on_transaction_id:
                    if self._repository_crypto_transaction.get(
                            id=transaction.start_on_transaction_id).status != CryptoTransaction.StatusCryptoTransaction.success:
                        continue

                transaction_id = await service.send_transaction(
                    public_key=transaction.public_key,
                    private_key=transaction.private_key,
                    count=int(transaction.count),
                    destination_address=transaction.receive_address,
                    sender_address=transaction.sender_address,
                    transaction_price=transaction.transaction_price,
                    use_transaction_price=transaction.use_transaction_price
                )

                if not transaction_id:
                    continue

                self._repository_crypto_transaction.update(
                    db_obj=transaction,
                    obj_in={
                        "status": CryptoTransaction.StatusCryptoTransaction.pending,
                        "transaction_id": transaction_id
                    }
                )
            except (TransactionUnderPriced, TransactionInPool):
                pass
            except Exception as e:
                self._repository_crypto_transaction.update(
                    db_obj=transaction,
                    obj_in={
                        "status": CryptoTransaction.StatusCryptoTransaction.fail,
                        "text": str(e)
                    }
                )
                if transaction.type in [CryptoTransaction.TransactionType.in_wallet,
                                        CryptoTransaction.TransactionType.out_system]:
                    await bot.send_message(transaction.wallet_crypto.user.user_id,
                                           f"Транзакция {transaction.id} ошибочна.")
                    if transaction.type == CryptoTransaction.TransactionType.out_system:
                        self._repository_crypto_wallet.update(
                            db_obj=transaction.wallet_crypto,
                            obj_in={
                                "balance": transaction.wallet_crypto.balance + transaction.count + transaction.comission if transaction.comission else 0
                            }
                        )

            self.session.commit()

        self._settings_repository.update(
            db_obj=settings_db,
            obj_in={
                "transaction_active": TaskType.not_working
            }
        )
        self.session.commit()


class CheckTransaction(Base):

    def __init__(self, repository_crypto_transaction: RepositoryCryptoTransaction,
                 repository_cryptocurrency_wallet: RepositoryCryptoWallet,
                 crypto_service: CryptoService, settings_repository: RepositorySettings,
                 rate_service: CheckCurrentCryptoCost,
                 repository_user: RepositoryUser, *args, **kwargs):
        self._repository_crypto_transaction = repository_crypto_transaction
        self._rep_cryptocurrency_wallet = repository_cryptocurrency_wallet
        self._settings_repository = settings_repository
        self._rate_service = rate_service
        self._repository_user = repository_user
        self._crypto_service = crypto_service
        super().__init__(*args, **kwargs)

    async def proccess(self, *args, **kwargs):
        settings_db = self._settings_repository.get()
        if settings_db.transaction_check_active != TaskType.not_working:
            return
        self._settings_repository.update(
            db_obj=settings_db,
            obj_in={
                "transaction_check_active": TaskType.pending
            }
        )
        self.session.commit()

        transactions = self._repository_crypto_transaction.list(
            status=CryptoTransaction.StatusCryptoTransaction.pending)
        for transaction in transactions:
            service = self._crypto_service(transaction.network, transaction.cryptocurrency)
            result = await service.check_transaction(transaction.transaction_id)

            if result == StatusTransaction.success:
                self._repository_crypto_transaction.update(
                    db_obj=transaction,
                    obj_in={
                        "status": CryptoTransaction.StatusCryptoTransaction.success,
                    }
                )

                if transaction.type == transaction.TransactionType.in_system:
                    self._rep_cryptocurrency_wallet.update(
                        db_obj=transaction.wallet_crypto,
                        obj_in={
                            "balance": transaction.wallet_crypto.balance + transaction.count,
                        }
                    )
                    new_count_balance = await self._rate_service.get(
                        get_normal_name(transaction.cryptocurrency),
                        count=service.from_minimal_part(transaction.count)
                    )

            elif result == StatusTransaction.failed:
                self._repository_crypto_transaction.update(
                    db_obj=transaction,
                    obj_in={
                        "status": CryptoTransaction.StatusCryptoTransaction.fail,
                    }
                )

                if transaction.type == transaction.TransactionType.out_system:
                    self._rep_cryptocurrency_wallet.update(
                        db_obj=transaction.wallet_crypto,
                        obj_in={
                            "balance": transaction.wallet_crypto.balance + transaction.count
                        }
                    )

            self.session.commit()

        self._settings_repository.update(
            db_obj=settings_db,
            obj_in={
                "transaction_check_active": TaskType.not_working
            }
        )

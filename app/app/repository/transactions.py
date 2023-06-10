from app.models.transactions import CryptoTransaction
from .base import RepositoryBase
from sqlalchemy import or_


class RepositoryCryptoTransaction(RepositoryBase[CryptoTransaction]):

    def transaction_history(self, wallet_crypto_id):
        return self._session.query(self._model).filter(
            or_(
                self._model.type == CryptoTransaction.TransactionType.in_wallet,
                self._model.type == CryptoTransaction.TransactionType.out_system
            ), self._model.wallet_crypto_id == wallet_crypto_id
        ).all()

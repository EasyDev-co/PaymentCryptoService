from .base import RepositoryBase
from app.models.wallets import Wallet, CryptocurrencyWallet
from typing import Optional
from sqlalchemy.orm import joinedload

from loguru import logger


class RepositoryWallet(RepositoryBase[Wallet]):

    def get(self, *args, **kwargs,) -> Optional[Wallet]:
        return self._session.query(self._model).filter(*args).filter_by(**kwargs).first()

    def list(self, *args, **kwargs):
        return self._session.query(self._model).filter(*args).filter_by(**kwargs).all()

    def get_list_addresses(self, *args, **kwargs):
        return self._session.query(self._model.address).filter(*args).filter_by(**kwargs).all()


class RepositoryCryptoWallet(RepositoryBase[CryptocurrencyWallet]):

    def get(self, *args, **kwargs,) -> Optional[CryptocurrencyWallet]:
        return self._session.query(self._model).options(
            joinedload(self._model.wallet)
        ).filter(*args).filter_by(**kwargs).first()

    def list(self, *args, **kwargs) -> Optional[list[CryptocurrencyWallet]]:
        wallets = self._session.query(self._model).options(
            joinedload(self._model.wallet)
        ).filter(*args).filter_by(**kwargs).all()
        logger.info(f"WALLETS: {wallets}")
        return wallets

    def get_wallet_on_address(self, address, cryptocurrency):
        return self._session.query(self._model).options(
            joinedload(self._model.wallet)
        ).filter(self._model.cryptocurrency == cryptocurrency).join(Wallet).filter_by(address=address).first()

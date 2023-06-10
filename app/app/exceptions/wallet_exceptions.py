from .base import BaseNotFound, BaseException


class WalletDeal(Exception):
    pass


class NotFoundWallet(WalletDeal, BaseNotFound):
    pass


class UserErrorWallet(WalletDeal, BaseException):
    pass

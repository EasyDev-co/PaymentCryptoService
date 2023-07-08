from .base import (
    TransactionNotExists,
    NotEnoughBalance,
    InvalidAddressOrPrivateKey,
    ToMuchGas,
    ToLittleGas,
    TransactionError,
)


class Erc20Error(Exception):
    pass


class TransactionInPool(Erc20Error, TransactionError):
    """
    Возникает при попытке заменить
    существующую транзакцию(незаминированную)
    """
    pass


class TransactionUnderPriced(Erc20Error, ToMuchGas):
    """
    Возникакет при передаче излишнего числа газа
    """
    pass


class GasPriceIsSoLow(Erc20Error, ToLittleGas):
    """
    Возникакет пари передаче слишком малого кол-ва газа.
    """
    pass


class NonceError(Erc20Error, TransactionError):
    """
    Возникакет, когда поле nonce превышает нужное кол-во
    """
    pass


class InsufficientFundsForGas(Erc20Error, NotEnoughBalance):
    """
    Возникает,
    когда недостаточно средств на балансе,
    и мы пытаемся отрпавить транзакцию
    """
    pass

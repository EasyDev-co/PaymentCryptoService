from .base import (
    BaseException,
    BaseNotFound,
    NotEnoughBalance,
    TransactionNotExists,
    InvalidAddressOrPrivateKey,
    ToLittleGas,
    TransactionError,
)


class BtcNetworkError(BaseException):
    pass


class RateLimitError(BtcNetworkError, RuntimeError):
    pass


class JSONError(BtcNetworkError):
    """
    Падает, когда данные были переданы в неверном формате.
    """
    pass


class TransactionDoesnotExists(BtcNetworkError, TransactionNotExists):
    """
    Возникает, когда транзакции не существует.
    """
    pass


class NotEnoughBalance(BtcNetworkError, NotEnoughBalance):
    """
    Возникает при недостатке баланса.
    """
    pass


class TXObjectNotCreated(BtcNetworkError):
    """
    Возникает, когда не получилось создать обхект транзакции.
    """
    pass


class InvalidMoneyType(BtcNetworkError, TransactionError):
    """
    Возникает когда значение было передано в неверном формате при переводе биткоинов в сатоши.
    """
    pass


class WalletDidntCreated(BtcNetworkError, RuntimeError):
    """
    Возникает, когда не получилось создать кошелёк.
    """
    pass


class TransactionNotSend(BtcNetworkError, TransactionError):
    """
    Возникает, когда не получилось отправить транзакцию в сеть
    """
    pass


class GetFeeError(BtcNetworkError, BaseNotFound):
    """
    Возникает при ошибке получения среднего количества фи с блоксайфера.
    """
    pass


class NotEnoughFee(BtcNetworkError, ToLittleGas):
    """
    Возникает при недостатке фи.
    """
    pass


class InvalidAddresses(BtcNetworkError, InvalidAddressOrPrivateKey):
    """
    Возникает, когда передан неверный адрес.
    """
    pass


class SignError(BtcNetworkError, TransactionNotExists):
    """
    Возникает при ошибке подписи транзакции.
    """
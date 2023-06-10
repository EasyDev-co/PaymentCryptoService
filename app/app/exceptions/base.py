class BaseException(Exception):
    pass


class BaseNotFound(BaseException):
    pass


class YouHaveNoRights(BaseException):
    pass


class NotEnoughBalance(BaseException):
    pass


class TransactionNotExists(BaseException):
    pass


class InvalidAddressOrPrivateKey(BaseException):
    pass


class ToMuchGas(BaseException):
    pass


class ToLittleGas(BaseException):
    pass


class TransactionError(BaseException):
    pass


class TooMuchTransfer(BaseException):
    pass
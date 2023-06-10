from app.models.wallets import NetworkType, CryptocurrencyType
from .base import CryptocurrencyInterface
from .btc import Bitcoin
from typing import Optional
from .erc20 import Erc20Network


class CryptoService:
    def __init__(self, bitcoin_network: Bitcoin, erc20_network: Erc20Network) -> None:
        self._bitcoin_network = bitcoin_network
        self._erc20_network = erc20_network

    def __call__(
            self,
            network: NetworkType,
            cryptocurrency: Optional[CryptocurrencyType] = None
    ) -> CryptocurrencyInterface:
        if network == NetworkType.bitcoin_network:
            return self._bitcoin_network
        elif network == NetworkType.erc20:
            if not cryptocurrency:
                return self._erc20_network(CryptocurrencyType.ethereum)
            return self._erc20_network(cryptocurrency)

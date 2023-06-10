from app.repository.transactions import RepositoryCryptoTransaction
from app.repository.wallet import RepositoryCryptoWallet
from app.repository.user import RepositoryUser


class CryptoTransactionService:

    def __init__(
            self,
            repository_user: RepositoryUser,
            repository_crypto_wallet: RepositoryCryptoWallet,
            repository_crypto_transactions: RepositoryCryptoTransaction
    ):
        self._repository_user = repository_user
        self._repository_crypto_wallet = repository_crypto_wallet
        self._repository_crypto_transactions = repository_crypto_transactions

    async def list(self, user_id: int):
        user = self._repository_user.get(user_id=user_id)
        btc_wallet, eth_wallet, usdt_wallet = self._repository_crypto_wallet.list(user_id=user.id)
        return self._repository_crypto_transactions.transaction_history(wallet_crypto_id=btc_wallet.id) + \
            self._repository_crypto_transactions.transaction_history(wallet_crypto_id=eth_wallet.id) + \
            self._repository_crypto_transactions.transaction_history(wallet_crypto_id=usdt_wallet.id)

    async def get(self, transaction_id: int):
        return self._repository_crypto_transactions.get(id=transaction_id)
from dependency_injector import containers, providers
from app.db.session import SyncSession
from app.core.config import Settings
from app.core.celery import celery_app

from app.models.wallets import CryptocurrencyWallet, Wallet
from app.models.webhook_erc20 import WebhookErc20Alchemy
from app.models.settings import Settings as ModelSettings
from app.models.users import Users
from app.models.transactions import CryptoTransaction

from app.repository.wallet import RepositoryWallet, RepositoryCryptoWallet
from app.repository.transactions import RepositoryCryptoTransaction
from app.repository.webhoook_erc20 import RepositoryWebhookErc20
from app.repository.settings import RepositorySettings
from app.repository.user import RepositoryUser

from app.services.crypto.btc import BlockChairApi, BlockCypherApi, Bitcoin
from app.services.crypto.erc20 import (
    EtherscanAPI,
    AlchemyNotify,
    Erc20Token,
    Erc20Network,
    Ethereum
)
from app.services.crypto.trc20 import TRXService, USDTTrc20Service, TRC20Network

from app.services.rate import CheckCurrentCryptoCost
from app.services.crypto import CryptoService
from app.services.transaction_service import CryptoTransactionService
from app.services.wallet import WalletService

from app.workers.add_address_to_webhook import AddAddressToWebhookErc20
from app.workers.check_transactions import CheckTransaction, SendTransaction
from app.workers.check_bitcoin_wallets import CheckBitcoinWallet
from app.workers.check_trc20_wallets import CheckTRC20Wallets


class CustomTaskProvider(providers.Provider):

    __slots__ = ("_singleton",)

    def __init__(self, provides, *args, **kwargs):
        self._singleton = providers.Singleton(provides, *args, **kwargs)
        custom_task = self._singleton.provided()
        celery_app.register_task(custom_task)
        super().__init__()

    def __deepcopy__(self, memo):
        copied = memo.get(id(self))
        if copied is not None:
            return copied

        copied = self.__class__(
            self._singleton.provides,
            *providers.deepcopy(self._singleton.args, memo),
            **providers.deepcopy(self._singleton.kwargs, memo),
        )
        self._copy_overridings(copied, memo)

        return copied

    @property
    def related(self):
        yield from [self._singleton]
        yield from super().related

    def _provide(self, *args, **kwargs):
        return self._singleton(*args, **kwargs)


class Container(containers.DeclarativeContainer):

    config = providers.Singleton(Settings)
    db = providers.Singleton(SyncSession, db_url=config.provided.SYNC_SQLALCHEMY_DATABASE_URI)

    repository_user = providers.Singleton(RepositoryUser, model=Users, session=db)

    repository_wallet = providers.Singleton(RepositoryWallet, model=Wallet, session=db)
    repository_crypto_wallet = providers.Singleton(RepositoryCryptoWallet, model=CryptocurrencyWallet, session=db)
    repository_crypto_transaction = providers.Singleton(
        RepositoryCryptoTransaction,
        model=CryptoTransaction,
        session=db
    )

    repository_settings = providers.Singleton(
        RepositorySettings,
        model=ModelSettings,
        session=db
    )

    repository_webhook_erc20 = providers.Singleton(RepositoryWebhookErc20, model=WebhookErc20Alchemy, session=db)

    trx_service = providers.Factory(TRXService, tronscan_url=config.provided.TRONSCAN_URL)
    usdt_trc20_service = providers.Factory(
        USDTTrc20Service,
        usdt_trc20_contract_address=config.provided.USDT_TRC20_CONTRACT_ADDRESS,
        tronscan_url=config.provided.TRONSCAN_URL
    )

    block_chair_api = providers.Factory(
        BlockChairApi,
        base_url=config.provided.BLOCKCHAIR_API_URL,
        bitcoin_network=config.provided.BLOCK_CHAIR_NETWORK
    )
    block_cypher_api = providers.Factory(
        BlockCypherApi,
        base_url=config.provided.BLOCK_CYPHER_API_URL,
        api_key=config.provided.BLOCK_CYPHER_API_TOKEN,
        network=config.provided.BLOCK_CYPHER_API_URL_NETWORK
    )
    etherscan_api = providers.Factory(
        EtherscanAPI,
        base_url=config.provided.ETHERSCAN_API_URL,
        api_key=config.provided.ETHERSCAN_API_TOKEN
    )
    alchemy_api = providers.Factory(
        AlchemyNotify,
        base_url=config.provided.WEBHOOK_ALCHEMY_URL,
        api_key=config.provided.WEBHOOK_ALCHEMY_TOKEN
    )
    bitcoin_service = providers.Singleton(Bitcoin, block_cypher_api=block_cypher_api, block_chair_api=block_chair_api)
    ethereum_service = providers.Singleton(
        Ethereum, etherscan_api=etherscan_api,
        alchemy=alchemy_api,
        ethereum_network_url=config.provided.ALCHEMY_API_URL
    )
    usdt_service = providers.Singleton(
        Erc20Token,
        contract_address=config.provided.USDT_ERC20_ADDRESS_CONTRACT,
        erc20_abi=config.provided.USDT_ERC20_ABI_CONTRACT,
        decimals=6,
        etherscan_api=etherscan_api,
        alchemy=alchemy_api,
        ethereum_network_url=config.provided.ALCHEMY_API_URL
    )

    trc20_network = providers.Singleton(TRC20Network, trx_service=trx_service, usdt_trc20_service=usdt_trc20_service)
    erc20_network = providers.Singleton(Erc20Network, ethereum_service=ethereum_service, usdt_service=usdt_service)
    crypto_service = providers.Singleton(
        CryptoService,
        erc20_network=erc20_network,
        trc20_network=trc20_network,
        bitcoin_network=bitcoin_service,
    )

    rate_service = providers.Singleton(
        CheckCurrentCryptoCost,
        base_url=config.provided.CHECK_RATES_URL_TOKENS,
    )

    crypto_transaction_service = providers.Singleton(
        CryptoTransactionService,
        repository_user=repository_user,
        repository_crypto_wallet=repository_crypto_wallet,
        repository_crypto_transactions=repository_crypto_transaction
    )

    check_balance_bitcoin_task = CustomTaskProvider(
        CheckBitcoinWallet,
        session=db,
        bitcoin_service=bitcoin_service,
        repository_wallet=repository_wallet,
        repository_cryptocurrency_wallet=repository_crypto_wallet,
        repository_crypto_transaction=repository_crypto_transaction,
        repository_settings=repository_settings
    )

    check_trc20_wallets_task = CustomTaskProvider(
        CheckTRC20Wallets,
        session=db,
        usdt_trc20_service=usdt_trc20_service,
        repository_wallet=repository_wallet,
        repository_cryptocurrency_wallet=repository_crypto_wallet,
        repository_crypto_transaction=repository_crypto_transaction,
        repository_settings=repository_settings
    )

    send_transaction_task = CustomTaskProvider(
        SendTransaction,
        session=db,
        crypto_service=crypto_service,
        repository_crypto_transaction=repository_crypto_transaction,
        settings_repository=repository_settings,
        repository_crypto_wallet=repository_crypto_wallet
    )
    check_transaction_task = CustomTaskProvider(
        CheckTransaction,
        session=db,
        repository_crypto_transaction=repository_crypto_transaction,
        repository_cryptocurrency_wallet=repository_crypto_wallet,
        settings_repository=repository_settings,
        rate_service=rate_service,
        crypto_service=crypto_service,
        repository_user=repository_user
    )

    add_address_to_webhook_erc20_task = CustomTaskProvider(
        AddAddressToWebhookErc20,
        repository_webhook_erc20=repository_webhook_erc20,
        alchemy_api=alchemy_api,
        session=db
    )

    wallet_service = providers.Singleton(
        WalletService,
        repository_cryptocurrency_wallet=repository_crypto_wallet,
        repository_wallet=repository_wallet,
        repository_settings=repository_settings,
        crypto_service=crypto_service,
        repository_crypto_transaction=repository_crypto_transaction,
        add_address_to_webhook_erc20_task=add_address_to_webhook_erc20_task,
        repository_user=repository_user
    )


@containers.copy(Container)
class CeleryContainer(Container):
    config = providers.Singleton(Settings)
    db = providers.Singleton(SyncSession, db_url=config.provided.SYNC_SQLALCHEMY_DATABASE_URI, dispose_session=True)

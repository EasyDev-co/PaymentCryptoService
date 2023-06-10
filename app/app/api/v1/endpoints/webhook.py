from app.core.containers import (
    Container,
    AlchemyNotify,
    RepositoryWallet,
    RepositoryCryptoTransaction,
    Ethereum,
    RepositorySettings,
    Erc20Token,
    RepositoryCryptoWallet
)
from app.models.wallets import CryptocurrencyType, NetworkType
from app.models.transactions import CryptoTransaction
from app.core.config import settings
from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends
from app.api.deps import commit_and_close_session

router = APIRouter()


@router.post("/erc-20")
@inject
@commit_and_close_session
async def balance_erc20(
        data: dict,
        alchemy: AlchemyNotify = Depends(Provide[Container.alchemy_api]),
        rep_crypto_transaction: RepositoryCryptoTransaction = Depends(Provide[Container.repository_crypto_transaction]),
        rep_wallet: RepositoryWallet = Depends(Provide[Container.repository_wallet]),
        ethereum: Ethereum = Depends(Provide[Container.ethereum_service]),
        rep_settings: RepositorySettings = Depends(Provide[Container.repository_settings]),
        rep_crypto_wallet: RepositoryCryptoWallet = Depends(Provide[Container.repository_crypto_wallet]),
        usdt: Erc20Token = Depends(Provide[Container.usdt_service])
):
    db_settings = rep_settings.get()
    gas_price = await ethereum.get_middle_cost_transaction()

    for update_balance in await alchemy.get_notify_from_alchemy(data):
        if rep_crypto_transaction.get(transaction_id=update_balance.hash):
            continue

        if update_balance.contract.address and ethereum.network.toChecksumAddress(update_balance.contract.address) == \
                ethereum.network.toChecksumAddress(settings.USDT_ERC20_ADDRESS_CONTRACT):
            update_balance.value = usdt.from_minimal_part(update_balance.contract.value)

            if update_balance.value < db_settings.minimum_usdt_in:
                return

            value = usdt.to_minimal_part(update_balance.value)

            wallet = rep_wallet.get(address=ethereum.network.toChecksumAddress(update_balance.destination_address))
            if wallet:
                wallet_crypto = rep_crypto_wallet.get(wallet_id=wallet.id, cryptocurrency=CryptocurrencyType.usdt)
                erc20_gas_estimate = db_settings.erc20_gas_estimate or settings.ERC20_GAS_ESTIMATE
                waiting_to_up_balance_transaction = rep_crypto_transaction.create({
                    "network": NetworkType.erc20,
                    "type": CryptoTransaction.TransactionType.in_wallet,
                    "cryptocurrency": CryptocurrencyType.usdt,
                    "count": value,
                    "status": CryptoTransaction.StatusCryptoTransaction.pending,
                    "receive_address": wallet.address,
                    "gas_price": gas_price,
                    "wallet_crypto_id": wallet_crypto.id,
                    "transaction_id": update_balance.hash
                })

                transaction_commission = rep_crypto_transaction.create({
                    "network": NetworkType.erc20,
                    "type": CryptoTransaction.TransactionType.commission,
                    "cryptocurrency": CryptocurrencyType.ethereum,
                    "count": (gas_price * erc20_gas_estimate + gas_price * 21000),
                    "gas_price": gas_price,
                    "receive_address": wallet.address,
                    "wallet_crypto_id": rep_crypto_wallet.get(wallet_id=wallet.id,
                                                              cryptocurrency=CryptocurrencyType.ethereum).id,
                    "start_on_transaction_id": waiting_to_up_balance_transaction.id
                })

                rep_crypto_transaction.create({
                    "network": NetworkType.erc20,
                    "cryptocurrency": CryptocurrencyType.usdt,
                    "count": value,
                    "receive_address": settings.ERC20_ADDRESS,
                    "type": CryptoTransaction.TransactionType.in_system,
                    "wallet_crypto_id": wallet_crypto.id,
                    "gas_price": gas_price,
                    "start_on_transaction_id": transaction_commission.id
                })

        if update_balance.coin_name == "ETH":
            if update_balance.value < db_settings.minimum_ethereum_in:
                return
            value = ethereum.to_minimal_part(update_balance.value)
            wallet = rep_wallet.get(address=ethereum.network.toChecksumAddress(update_balance.destination_address))
            if wallet:
                wallet_crypto = rep_crypto_wallet.get(wallet_id=wallet.id, cryptocurrency=CryptocurrencyType.ethereum)

                waiting_to_up_balance_transaction = rep_crypto_transaction.create({
                    "network": NetworkType.erc20,
                    "type": CryptoTransaction.TransactionType.in_wallet,
                    "cryptocurrency": CryptocurrencyType.ethereum,
                    "count": value,
                    "status": CryptoTransaction.StatusCryptoTransaction.pending,
                    "receive_address": wallet.address,
                    "wallet_crypto_id": wallet_crypto.id,
                    "gas_price": gas_price,
                    "transaction_id": update_balance.hash
                })
                rep_crypto_transaction.create({
                    "network": NetworkType.erc20,
                    "cryptocurrency": CryptocurrencyType.ethereum,
                    "count": value,
                    "receive_address": settings.ERC20_ADDRESS,
                    "type": CryptoTransaction.TransactionType.in_system,
                    "wallet_crypto_id": wallet_crypto.id,
                    "gas_price": gas_price,
                    "start_on_transaction_id": waiting_to_up_balance_transaction.id
                })
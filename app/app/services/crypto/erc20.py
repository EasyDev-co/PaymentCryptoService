import httpx

from binascii import hexlify
from urllib.parse import urljoin
from web3 import Web3 as erc20
from web3.exceptions import TransactionNotFound
from app.schemas.alchemy import (
    AlchemyNotifyScheme,
    AllWebhooks,
    WebhookAddedAndRemoved,
)

from app.models.wallets import CryptocurrencyType
from app.services.crypto.base import StatusTransaction, Wallet, CryptocurrencyInterface
from enum import Enum
from app.exceptions import erc20_exceptions
from typing import Optional


class TypeErc20Token(Enum):
    usdt = "usdt"
    eth = "eth"


class EtherscanAPI:
    def __init__(self, base_url, api_key) -> None:
        self.base_url = base_url
        self.api_key = api_key

    async def get_gas_price(self) -> dict:
        url = urljoin(
            base=self.base_url,
            url=f"api?module=gastracker&action=gasoracle&apikey={self.api_key}"
        )
        response = httpx.get(url, timeout=30.0)

        if response.status_code == 200:
            if response.json().get("result").get("SafeGasPrice"):
                safe_gas_price, _, _ = (
                    int(response.json().get("result").get("SafeGasPrice")) / 1_000_000_000,
                    None,
                    None
                )

                return {
                    "safe_gas_price": safe_gas_price,
                    "propose_gas_price": None,
                    "fast_gas_price": None
                }


class AlchemyNotify:
    def __init__(self, base_url, api_key) -> None:
        self._base_url = base_url
        self._api_key = api_key

    async def create_webhook(self, network: str, webhook_type: str, webhook_url: str) -> str:
        url = urljoin(base=self._base_url, url="create-webhook")
        payload = {
            "addresses": [],
            "network": network,
            "webhook_type": webhook_type,
            "webhook_url": webhook_url,
        }
        headers = {
            "accept": "application/json",
            "X-Alchemy-Token": self._api_key,
            "content-type": "application/json"
        }
        response = httpx.post(url=url, json=payload, headers=headers)
        if response.status_code == 200:
            if response.json().get("data").get("id"):
                return response.json().get('data').get('id')

    async def delete_webhook(self, webhook_id: str) -> str:
        url = urljoin(base=self._base_url, url="delete-webhook?webhook_id={wh_id}".format(wh_id=webhook_id))
        headers = {
            "accept": "application/json",
            "X-Alchemy-Token": self._api_key
        }
        response = httpx.delete(url=url, headers=headers)
        if response.status_code == 200:
            return f"Webhook с ID: {webhook_id} успешно удален!"

    async def get_all_webhook_team(self) -> AllWebhooks:
        url = urljoin(base=self._base_url, url="team-webhooks")

        headers = {
            "accept": "application/json",
            "X-Alchemy-Token": self._api_key
        }

        response = httpx.get(url=url, headers=headers)
        if response.status_code == 200:
            all_data = response.json().get("data")
            webhook_list = []
            for wh_id in all_data:
                webhook_list.append({
                    "id": wh_id.get("id"),
                    "network": wh_id.get("network"),
                    "is_active": wh_id.get("is_active")
                })
            webhook_dict = {
                "data": webhook_list
            }
            return AllWebhooks.parse_obj(webhook_dict)

    async def add_addresses_to_web_hook(
            self,
            webhook_id: str,
            addresses_to_add: list,
            addresses_to_remove: list
    ) -> WebhookAddedAndRemoved:

        url = urljoin(base=self._base_url, url="update-webhook-addresses")
        payload = {
            "addresses_to_add": addresses_to_add,
            "addresses_to_remove": addresses_to_remove,
            "webhook_id": webhook_id
        }
        headers = {
            "accept": "application/json",
            "X-Alchemy-Token": self._api_key,
            "content-type": "application/json"
        }
        response = httpx.patch(url=url, json=payload, headers=headers)
        print(response.text)
        if response.status_code == 200:
            addresses_dict_with_webhook_id = {
                "addresses_to_add": addresses_to_add,
                "addresses_to_remove": addresses_to_remove,
                "webhook_id": webhook_id
            }
            return True
            # return WebhookAddedAndRemoved.parse_obj(addresses_dict_with_webhook_id)

    async def get_notify_from_alchemy(self, notify: dict) -> list[AlchemyNotifyScheme]:
        result = []
        for event in notify.get("event").get("activity"):
            event['hash'] = event['hash'].replace('0x', '')
            result.append(AlchemyNotifyScheme.parse_obj(event))

        return result


class Ethereum(CryptocurrencyInterface):

    def __init__(self, etherscan_api: EtherscanAPI, alchemy: AlchemyNotify, ethereum_network_url: str) -> None:
        self._etherscan_api = etherscan_api
        self.alchemy = alchemy
        self.network = erc20(erc20.HTTPProvider(ethereum_network_url))

    async def create_wallet(self) -> Wallet:
        acct = self.network.eth.account.create("KEYSMASH FJAFJKLDSKF7JKFDJ 1530")

        address = self.network.to_checksum_address(acct.address)
        private_key = acct._private_key

        return Wallet(public_key=address, address=address, private_key=bytes.decode(hexlify(private_key)))

    async def get_middle_cost_transaction(self) -> int:
        return self.network.to_wei((await self._etherscan_api.get_gas_price()).get('safe_gas_price'), 'ether')

    async def send_transaction(
            self,
            private_key: str,
            count: int,
            destination_address: str,
            sender_address: str,
            transaction_price: Optional[int] = None,
            use_transaction_price: bool = True,
            *_args, **_kwargs
    ) -> str:

        try:
            txn = await self._get_dynamic_fee_transaction(
                sender_address=sender_address,
                destination_address=destination_address,
                value=count,
                gas_price=transaction_price,
                use_transaction_price=use_transaction_price
            )

            signed_txn = self.network.eth.account.sign_transaction(
                transaction_dict=txn,
                private_key=private_key
            )

            txn_hash = self.network.eth.send_raw_transaction(signed_txn.rawTransaction)
            return bytes.decode(hexlify(txn_hash))

        except (ValueError, TypeError) as exc:
            await self._check_erc20token_exceptions(exc=exc)

    @classmethod
    async def _check_erc20token_exceptions(cls, exc):
        if isinstance(exc.args[0], dict):
            error_message = exc.args[0].get("message")
            if error_message == 'insufficient funds for gas * price + value':
                raise erc20_exceptions.InsufficientFundsForGas(error_message)
            elif error_message == 'already known':
                raise erc20_exceptions.TransactionInPool(error_message)
            elif error_message == 'replacement transaction underpriced':
                raise erc20_exceptions.TransactionUnderPriced(error_message)
            elif error_message == 'intrinsic gas too low':
                raise erc20_exceptions.GasPriceIsSoLow(error_message)
            elif error_message == 'rlp: input string too long for uint64, decoding into (types.LegacyTx).Nonce':
                raise erc20_exceptions.InvalidAddressOrPrivateKey(error_message)
        else:
            error_message = exc.args[0]
            prefix_address_error = "Unknown format"
            prefix_nonce_error = "Transaction had invalid fields"
            if error_message.startswith(prefix_nonce_error):
                raise erc20_exceptions.NonceError(error_message)
            elif error_message.startswith(prefix_address_error):
                raise erc20_exceptions.InvalidAddressOrPrivateKey(error_message)

        raise erc20_exceptions.Erc20Error(error_message)

    async def check_transaction(self, transaction_id: str) -> StatusTransaction:
        try:
            receipt = self.network.eth.get_transaction_receipt(transaction_id)
        except TransactionNotFound:
            return StatusTransaction.pending

        if bool(receipt.status):
            return StatusTransaction.success
        else:
            return StatusTransaction.failed

    def from_minimal_part(self, count: int) -> float:
        return self.network.from_wei(count, 'ether')

    def to_minimal_part(self, count: float) -> int:
        return int(self.network.to_wei(count, "ether"))

    async def _get_dynamic_fee_transaction(
            self,
            sender_address: str,
            destination_address: str,
            value: int,
            gas_price: Optional[int] = None,
            use_transaction_price: bool = True):
        if not gas_price:
            gas_price = await self.get_middle_cost_transaction()
        if (value - gas_price * 21000) <= 0:
            raise erc20_exceptions.NotEnoughBalance("Не хватает баланса.")

        if use_transaction_price:
            price = value - gas_price * 21000
        else:
            price = value

        txn_create = {
            "nonce": self.network.eth.get_transaction_count(self.network.to_checksum_address(sender_address)),
            "to": self.network.to_checksum_address(destination_address),
            "value": price,
            "gas": 21000,
            "gasPrice": gas_price,
        }

        return txn_create


class Erc20Token(Ethereum):

    def __init__(self, contract_address: str, erc20_abi: list, decimals: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.erc20_token_contract = self.network.eth.contract(contract_address, abi=erc20_abi)
        self.decimals = decimals

    def from_minimal_part(self, count: int) -> float:
        return count / 10 ** self.decimals

    def to_minimal_part(self, count: float) -> int:
        normalize_value = count * 10 ** self.decimals
        return int(normalize_value)

    async def _get_dynamic_fee_transaction_erc20(self, sender_address: str, gas_price: Optional[int] = None):
        if not gas_price:
            gas_price = await self.get_middle_cost_transaction()
        txn_create = {
            "chainId": self.network.eth.chain_id,
            "from": self.network.to_checksum_address(sender_address),
            "gasPrice": gas_price,
            # TODO add count gas
            "nonce": self.network.eth.get_transaction_count(self.network.to_checksum_address(sender_address))
        }

        return txn_create

    async def send_transaction(
            self,
            private_key: str,
            count: int,
            destination_address: str,
            sender_address: str,
            transaction_price: Optional[int] = None,
            *_args, **_kwargs
    ) -> str:
        try:
            transaction = (await self._get_dynamic_fee_transaction_erc20(sender_address=sender_address,
                                                                         gas_price=transaction_price))
            trans = self.erc20_token_contract.functions.transfer(
                self.network.to_checksum_address(
                    destination_address
                ), count
            ).build_transaction(transaction)
            signed_txn = self.network.eth.account.sign_transaction(trans, private_key)
            txn_hash = self.network.eth.send_raw_transaction(signed_txn.rawTransaction)
            return bytes.decode(hexlify(txn_hash))
        except (ValueError, TypeError) as exc:
            await self._check_erc20token_exceptions(exc=exc)


class Erc20Network:

    def __init__(self, ethereum_service: Ethereum, usdt_service: Erc20Token) -> None:
        self._ethereum_service = ethereum_service
        self._usdt_service = usdt_service

        self._mapping = {
            CryptocurrencyType.ethereum: self._ethereum_service,
            CryptocurrencyType.usdt: self._usdt_service
        }

    def __call__(self, token: CryptocurrencyType) -> Ethereum:
        return self._mapping[token]

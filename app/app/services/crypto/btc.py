from urllib.parse import urljoin
from typing import Union, Optional
from bitcoin import (
    der_encode_sig,
    ecdsa_raw_sign,
    ecdsa_raw_verify,
    der_decode_sig
)
from app.services.crypto.base import (
    CryptocurrencyInterface, StatusTransaction, Wallet
)
from app.exceptions import btc_exceptions
import httpx


class BlockChairApi:
    def __init__(self, base_url, bitcoin_network) -> None:
        self._base_url = base_url
        self._bitcoin_network = bitcoin_network

    async def check_balance(
            self,
            btc_addresses: list[str]) -> dict:
        """
        input:
            [
                "address_2", "address_2"
            ]

        return:
            {
                "address_1": "balance_1",
                "address_2": "balance_2"
            }

        """

        url = urljoin(self._base_url, f"/{self._bitcoin_network}/addresses/balances")
        send_post_request = await self._post(
            url,
            data={'addresses': ",".join(btc_addresses)}
        )
        return send_post_request.json()['data']

    async def _post(
            self,
            url: str,
            data: Union[dict, list]) -> Union[list, dict]:
        res = httpx.post(url, json=data, timeout=60 * 15)
        return res


class BlockCypherApi:
    def __init__(self, base_url, api_key, network) -> None:
        self._base_url = base_url
        self._api_key = api_key
        self._network = network

    def _get_address(self, method: str):
        """
            without slash in method start
        """
        method = f"/v1/btc/{self._network}/{method}"
        return urljoin(self._base_url, method)

    def _btc_to_satoshi(self, btc_amount: float) -> int:
        return int(btc_amount * 100_000_000)

    def _satochi_to_btc(self, satoshi_amount: int) -> float:
        return satoshi_amount / 100_000_000

    async def _create_btc_wallet(self) -> Wallet:

        response = httpx.post(self._get_address("addrs"), headers={}, data={})

        if response.status_code != 201:
            raise btc_exceptions.WalletDidntCreated(
                response.text
            )

        response = response.json()
        return Wallet(
            address=response['address'],
            private_key=response['private'],
            public_key=response['public'],
        )

    async def _get_transaction_by_hash(
            self,
            hash: str,
    ) -> StatusTransaction:
        """
            input:
                - hash transaction

            output:
                - status transaction in current network
        """
        resp = httpx.get(self._get_address(f"txs/{hash}"))

        resp_data = resp.json()

        if resp_data.get("error"):
            return StatusTransaction.failed

        if resp_data.get("confirmed"):
            return StatusTransaction.success
        else:
            return StatusTransaction.pending

    async def _get_middle_fee(self) -> int:

        resp = httpx.get(self._base_url)
        resp_data = resp.json()
        middle_fee = resp_data.get("medium_fee_per_kb")
        if not middle_fee:
            raise btc_exceptions.BtcNetworkError(resp.text)

        return middle_fee

    async def _send_transaction(
            self,
            sender_address: str,
            destination_address: str,
            value_in_satoshi: int,
            private_key: str,
            public_key: str,
            use_transaction_price: bool = True) -> str:
        """
            input:
                sender_address - maker transactions
                destination_address - taker transactions

            result:
                - hash new transactions
        """
        fees = await self._get_middle_fee()

        if use_transaction_price:
            price = value_in_satoshi - fees
        else:
            price = value_in_satoshi

        privkey_list = []
        pubkey_list = []
        try:
            unsigned_tx = await self._create_unsigned_tx_object(
                sender_address,
                destination_address,
                price,
                fees=fees
            )
        except TypeError:
            raise btc_exceptions.JSONError(
                "Not correct data"
            )

        to_sign_list = unsigned_tx.get("tosign")
        for _ in range(len(to_sign_list)):
            privkey_list.append(private_key)
            pubkey_list.append(public_key)

        # Создаем цифровую подпись
        try:
            signature = await self._make_tx_signatures(
                txs_to_sign=to_sign_list,
                privkey_list=privkey_list,
                pubkey_list=pubkey_list,
                use_prefix=destination_address.startswith('bc1')
            )
        except Exception:
            raise btc_exceptions.SignError(
                "Произошла ошибка при подписи объекта транзакции"
            )

        # Отправляем транзакцию в сеть
        sended_tx = await self._broadcast_signed_transaction(
            unsigned_tx=unsigned_tx,
            signatures=signature,
            pubkeys=pubkey_list,
            api_key=self.api_key,
        )
        return sended_tx

    async def _create_unsigned_tx_object(
            self,
            sender_address: str,
            destination_address: str,
            value_in_satoshi: int,
            fees: int
    ) -> dict:

        data = {
            "fees": fees,
            "inputs": [
                {"addresses": [sender_address]}
            ],
            "outputs": [
                {
                    "addresses": [destination_address],
                    "value": value_in_satoshi
                }
            ]
        }

        unsigned_tx = httpx.post(self._get_address("txs/new"), json=data, headers={}).json()

        if unsigned_tx.get("errors"):
            for error in unsigned_tx.get("errors"):
                error = error.get("error")
                if error == f"Unable to find a transaction to spend for address {sender_address}.":
                    raise btc_exceptions.TXObjectNotCreated(f"{error} Look's like you don't have enough money")
                if error[:19] == "Not enough funds in":
                    raise btc_exceptions.NotEnoughFee(error)
                if error[:22] == "Not enough funds after":
                    raise btc_exceptions.NotEnoughFee(error)
                if error == "Error validating generated transaction: Transaction missing input or output.":
                    raise btc_exceptions.InvalidAddresses(error)

        return unsigned_tx

    async def _make_tx_signatures(
            self,
            txs_to_sign: list[str],
            privkey_list: list[str],
            pubkey_list: list[str],
            use_prefix=False) -> list[str]:
        """
        Loops through txs_to_sign and makes signatures
        using privkey_list and pubkey_list

        Not sure what privkeys and pubkeys to supply?
        Use get_input_addresses() to return a list of addresses.
        Matching those addresses to keys is up to you
        and how you store your private keys.
        A future version of this library may handle this for you,
        but it is not trivial.

        Note that if spending multisig funds the process
        is significantly more complicated.
        Each tx_to_sign must be signed by *each* private key.
        In a 2-of-3 transaction, two of [privkey1, privkey2, privkey3]
        must sign each tx_to_sign

        http://dev.blockcypher.com/#multisig-transactions
        """

        signatures = []
        for cnt, tx_to_sign in enumerate(txs_to_sign):
            try:
                sig = der_encode_sig(*ecdsa_raw_sign(
                    tx_to_sign.rstrip(' \t\r\n\0'), privkey_list[0])
                                     )
                err_msg = 'Bad Signature: sig %s for tx %s with pubkey %s' % (
                    sig,
                    tx_to_sign,
                    pubkey_list[0],
                )
                assert ecdsa_raw_verify(
                    tx_to_sign, der_decode_sig(sig), pubkey_list[0]), err_msg
            except IndexError:
                continue

            if use_prefix:
                sig += '01'

            signatures.append(sig)
        return signatures

    async def _get_valid_json(self, request, allow_204=False) -> bool:
        """
        Проверяет валидный ли json.
        """
        if request.status_code == 429:
            raise btc_exceptions.RateLimitError(
                'Status Code 429',
                request.text
            )
        elif request.status_code == 204 and allow_204:
            return True
        try:
            return request.json()
        except Exception as error:
            msg = 'JSON deserialization failed: {}'.format(str(error))
            raise btc_exceptions.JSONError(msg)

    async def _broadcast_signed_transaction(
            self,
            unsigned_tx: dict,
            signatures: list[str],
            pubkeys: list[str],
    ) -> str:
        '''
        Broadcasts the transaction from create_unsigned_tx
        '''
        data = unsigned_tx.copy()
        data['signatures'] = signatures
        data['pubkeys'] = pubkeys
        params = {'token': self._api_key}

        response = httpx.post(
            self._get_address("/txs/send"),
            params=params,
            json=data,
            timeout=10
        )
        response_dict = await self._get_valid_json(response)
        sender_address = unsigned_tx.get("tx").get("addresses")[0]
        if response_dict.get("errors"):
            for error in response_dict.get("errors"):
                error = error.get("error")
                if error == f"Unable to find a transaction to spend for address {sender_address}.":
                    raise btc_exceptions.TXObjectNotCreated(error)
                if error[:19] == "Not enough funds in":
                    raise btc_exceptions.NotEnoughFee(error)
                if error[:22] == "Not enough funds after":
                    raise btc_exceptions.NotEnoughFee(error)
                if error == "Error validating generated transaction: Transaction missing input or output.":
                    raise btc_exceptions.InvalidAddresses(error)
                if "Couldn't deserialize request: json:" in error:
                    raise btc_exceptions.InvalidAddresses(error)

        elif error := response_dict.get('error'):
            if error == f"Unable to find a transaction to spend for address {sender_address}.":
                raise btc_exceptions.TXObjectNotCreated(error)
            if error[:19] == "Not enough funds in":
                raise btc_exceptions.NotEnoughFee(error)
            if error[:22] == "Not enough funds after":
                raise btc_exceptions.NotEnoughFee(error)
            if error == "Error validating generated transaction: Transaction missing input or output.":
                raise btc_exceptions.InvalidAddresses(error)
            if "Couldn't deserialize request: json:" in error:
                raise btc_exceptions.InvalidAddresses(error)

        return response_dict.get("tx").get("hash")


class Bitcoin(CryptocurrencyInterface):

    def __init__(
            self,
            block_chair_api: BlockChairApi,
            block_cypher_api: BlockCypherApi,
    ) -> None:
        self._block_chair_api = block_chair_api
        self._block_cypher_api = block_cypher_api

    async def create_wallet(self) -> Wallet:
        """
            Возвращает адресс, приватный и публичный ключ, wif.
            Возвращаются данные в байтах.
        """
        return await self._block_cypher_api._create_btc_wallet()

    async def get_middle_cost_transaction(self) -> int:
        return await self._block_cypher_api._get_middle_fee()

    async def send_transaction(
            self,
            public_key: str,
            private_key: str,
            count: int,
            destination_address: str,
            sender_address: str,
            transaction_price: Optional[int] = None,
            use_transaction_price: bool = True
    ) -> str:
        return await self._block_cypher_api._send_transaction(
            sender_address=sender_address,
            destination_address=destination_address,
            value_in_satoshi=count,
            private_key=private_key,
            public_key=public_key,
            use_transaction_price=use_transaction_price
        )

    async def check_transaction(self, transaction_id: str) -> StatusTransaction:
        return await self._block_cypher_api._get_transaction_by_hash(transaction_id)

    def from_minimal_part(self, count: int) -> float:
        return self._block_cypher_api._satochi_to_btc(satoshi_amount=count)

    def to_minimal_part(self, count: float) -> int:
        return self._block_cypher_api._btc_to_satoshi(
            btc_amount=count
        )

    async def check_balances(self, btc_addresses: list[str]) -> dict:
        return await self._block_chair_api.check_balance(
            btc_addresses=btc_addresses
        )
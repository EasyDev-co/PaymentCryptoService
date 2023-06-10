import httpx


class CheckCurrentCryptoCost:

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    async def get_current_crypto_cost(self, crypto, to_crypto="USD"):
        response = httpx.get(self.base_url.format(crypto=crypto, to_crypto=to_crypto))
        if response.status_code == 200:
            return response.json().get(to_crypto)

    async def get(self, crypto, to_crypto="USD", count=1) -> float:
        return await self.get_current_crypto_cost(crypto, to_crypto) * float(count)

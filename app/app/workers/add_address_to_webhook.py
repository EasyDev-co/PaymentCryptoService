from .base import Base

from app.services.crypto.erc20 import AlchemyNotify
from app.repository.webhook_erc20 import RepositoryWebhookErc20
from app.core.config import settings
from urllib.parse import urljoin


class AddAddressToWebhookErc20(Base):

    def __init__(
            self,
            repository_webhook_erc20: RepositoryWebhookErc20,
            alchemy_api: AlchemyNotify,
            *args, **kwargs):
        self._repository_webhook_erc20 = repository_webhook_erc20
        self._alchemy_api = alchemy_api
        super().__init__(*args, **kwargs)

    async def proccess(self, *args, **kwargs):
        webhook_db = self._repository_webhook_erc20.get()
        if not webhook_db:
            webhook = await self._alchemy_api.create_webhook(
                network=settings.ERC20_NETWORK_TYPE, webhook_type="ADDRESS_ACTIVITY",
                webhook_url=urljoin(settings.BASE_URL, "/api/v1/webhook/erc-20")
            )
            if webhook:
                webhook_db = self._repository_webhook_erc20.create(
                    {
                        "webhook_id": webhook,
                        "address": [kwargs.get('address')]
                    }
                )
        else:
            address = webhook_db.address
            address.append(kwargs.get('address'))
            self._repository_webhook_erc20.update(
                db_obj=webhook_db,
                obj_in={
                    "address": address
                }
            )
        await self._alchemy_api.add_addresses_to_web_hook(
            webhook_db.webhook_id,
            [kwargs.get('address')],
            []
        )

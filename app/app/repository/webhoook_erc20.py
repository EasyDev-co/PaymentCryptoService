from .base import RepositoryBase
from app.models.webhook_erc20 import WebhookErc20Alchemy


class RepositoryWebhookErc20(RepositoryBase[WebhookErc20Alchemy]):
    pass

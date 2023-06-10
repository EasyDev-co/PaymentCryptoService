from uuid import uuid4

from app.db.base_class import Base

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID, JSONB


class WebhookErc20Alchemy(Base):
    __tablename__ = "webhookerc20alchemies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    webhook_id = Column(String, index=True)
    address = Column(JSONB, default=[])

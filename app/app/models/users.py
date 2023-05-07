import datetime

from app.db.base_class import Base

from uuid import uuid4

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID


class Users(Base):
    __tablename__ = 'users'

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid4
    )
    user_id = Column(String, unique=True)

    def __repr__(self):
        return self.user_id


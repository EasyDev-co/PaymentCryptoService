from abc import ABC

from sqlalchemy.types import TypeDecorator
from sqlalchemy import Numeric


class NumericInt(TypeDecorator, ABC):
    """Convert Python bytestring to string with hexadecimal digits and back for storage."""

    impl = Numeric

    def process_result_value(self, value, dialect):
        return int(value) if value else 0

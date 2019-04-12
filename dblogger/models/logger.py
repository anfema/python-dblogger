from typing import Dict, Any
from asyncpg import Record

from .model import BaseModel

__all__ = ['BaseLogLogger']


class BaseLogLogger(BaseModel):
    table = "logger_logger"

    name: str

    def deserialize(self, rowdata: Record) -> None:
        self.name = rowdata.get('name')

    @classmethod
    def serialize_data(cls, data) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        if 'name' in data:
            result['name'] = data['name']

        return result

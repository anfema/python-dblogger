from typing import Dict, Any
from asyncpg import Record

from .model import BaseModel

__all__ = ['BaseLogSource']


class BaseLogSource(BaseModel):
    table = "logger_source"

    path: str

    def deserialize(self, rowdata: Record) -> None:
        self.path = rowdata.get('path')

    @classmethod
    def serialize_data(cls, data) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        if 'path' in data:
            result['path'] = data['path']

        return result

from typing import Dict, Any

from .model import BaseModel

__all__ = ['BaseLogHost']


class BaseLogHost(BaseModel):
    table = "logger_hosts"

    name: str

    def deserialize(self, rowdata: Dict) -> None:
        self.name = rowdata.get('name')

    @classmethod
    def serialize_data(cls, data) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        if 'name' in data:
            result['name'] = data['name']

        return result

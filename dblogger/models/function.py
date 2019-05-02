from typing import Dict, Any

from .model import BaseModel

__all__ = ['BaseLogFunction']


class BaseLogFunction(BaseModel):
    table = "logger_function"

    name: str
    line_number: int
    source_id: int

    def deserialize(self, rowdata: Dict) -> None:
        self.name = rowdata.get('name')
        self.line_number = rowdata.get('lineNumber')
        self.source_id = rowdata.get('sourceID')

    @classmethod
    def serialize_data(cls, data) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        if 'name' in data:
            result['name'] = data['name']
        if 'line_number' in data:
            result['lineNumber'] = data['line_number']
        if 'source_id' in data:
            result['sourceID'] = data['source_id']

        return result

    @property
    def source(self):
        pass

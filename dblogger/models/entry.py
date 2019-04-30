from typing import List, Dict, Any, AsyncGenerator

from logging import DEBUG
from datetime import datetime, timezone

from .model import BaseModel
from .tag import BaseLogTag

__all__ = ['BaseLogEntry']


class BaseLogEntry(BaseModel):
    table = "logger_log"

    level: int
    message: str
    pid: int
    time: datetime
    function_id: int
    logger_id: int
    hostname_id: int

    def deserialize(self, rowdata: Dict) -> None:
        self.level = rowdata.get('level')
        self.message = rowdata.get('message')
        self.pid = rowdata.get('pid')
        self.time = datetime.utcfromtimestamp(rowdata.get('time'))
        self.function_id = rowdata.get('functionID')
        self.logger_id = rowdata.get('loggerID')
        self.hostname_id = rowdata.get('hostnameID')

    @classmethod
    def serialize_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        if 'level' in data:
            result['level'] = data['level']
        if 'message' in data:
            result['message'] = data['message']
        if 'pid' in data:
            result['pid'] = data['pid']
        if 'time' in data:
            result['time'] = data['time'].timestamp()
        if 'function_id' in data:
            result['functionID'] = data['function_id']
        if 'logger_id' in data:
            result['loggerID'] = data['logger_id']
        if 'hostname_id' in data:
            result['hostnameID'] = data['hostname_id']

        return result

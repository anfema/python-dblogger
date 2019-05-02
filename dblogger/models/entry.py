from typing import List, Dict, Any, Optional

from logging import DEBUG
from datetime import datetime, timezone

from .model import BaseModel

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

def get_sql_for_entry_with_date(where_clause: List[str], limit:  Optional[int]=None):
    from .function import BaseLogFunction
    from .source import BaseLogSource
    from .logger import BaseLogLogger
    from .host import BaseLogHost

    return f'''
        SELECT
            le.id, le.level, le.message, le.pid, le.time,
            le."functionID", le."loggerID", le."hostnameID",
            lf."name" as function_name,
            lf."lineNumber" as function_line_number,
            lf."sourceID" as "function_sourceID",
            ls.path as function_source_path,
            ll."name" as logger_name,
            lh."name" as hostname_name
        FROM {BaseLogEntry.table} le
        LEFT JOIN {BaseLogFunction.table} lf ON lf.id = le."functionID"
        LEFT JOIN {BaseLogSource.table} ls ON ls.id = lf."sourceID"
        LEFT JOIN {BaseLogLogger.table} ll ON ll.id = le."loggerID"
        LEFT JOIN {BaseLogHost.table} lh ON lh.id = le."hostnameID"
        {'WHERE' if len(where_clause) > 0 else ''} {where_clause}
        ORDER BY
            le."time" {'ASC' if limit is None else 'DESC'},
            le.id {'ASC' if limit is None else 'DESC'}
        {f'LIMIT {int(limit)}' if limit is not None else ''}
    '''

def get_sql_for_entry_after_id(parameter: str):
    from .function import BaseLogFunction
    from .source import BaseLogSource
    from .logger import BaseLogLogger
    from .host import BaseLogHost

    return f'''
        SELECT
            le.id, le.level, le.message, le.pid, le.time,
            le."functionID", le."loggerID", le."hostnameID",
            lf."name" as function_name,
            lf."lineNumber" as function_line_number,
            lf."sourceID" as "function_sourceID",
            ls.path as function_source_path,
            ll."name" as logger_name,
            lh."name" as hostname_name
        FROM {BaseLogEntry.table} le
        LEFT JOIN {BaseLogFunction.table} lf ON lf.id = le."functionID"
        LEFT JOIN {BaseLogSource.table} ls ON ls.id = lf."sourceID"
        LEFT JOIN {BaseLogLogger.table} ll ON ll.id = le."loggerID"
        LEFT JOIN {BaseLogHost.table} lh ON lh.id = le."hostnameID"
        WHERE le.id > {parameter}
        ORDER BY id;
    '''

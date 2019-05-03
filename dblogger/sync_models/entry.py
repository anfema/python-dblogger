from typing import List, Dict, Any, Generator, Optional

from logging import DEBUG
from datetime import datetime, timezone

from dblogger.models.entry import BaseLogEntry, get_sql_for_entry_with_date, get_sql_for_entry_after_id

from .model import SyncModel
from .tag import LogTag
from .function import LogFunction
from .logger import LogLogger
from .host import LogHost
from .source import LogSource

__all__ = ['LogEntry']

# FIXME: Psycopg2 does not have type information yet


def deserialize_joined(entry: "LogEntry", result: Dict[str, Any]):
    function = LogFunction(rowdata={
        "id": result['functionID'],
        "name": result['function_name'],
        "lineNumber": result['function_line_number'],
        "sourceID": result['function_sourceID']
    })
    source = LogSource(rowdata={
        "id": result['function_sourceID'],
        "path": result['function_source_path']
    })
    logger = LogLogger(rowdata={
        "id": result['loggerID'],
        "name": result['logger_name']
    })
    hostname = LogHost(rowdata={
        "id": result['hostnameID'],
        "name": result['hostname_name']
    })
    setattr(function, '_source', source)
    setattr(entry, '_function', function)
    setattr(entry, '_logger', logger)
    setattr(entry, '_hostname', hostname)


class LogEntry(BaseLogEntry, SyncModel):

    @classmethod
    def load_all_with_date(
        cls,
        db: Any,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List["LogEntry"]:
        if from_date is None and to_date is None and limit is None:
            raise ValueError('Define at least one of `from_date`, `to_date` or `limit`')
        where_clause = []
        values = []
        if from_date is not None:
            where_clause.append('"time" > %s')
            values.append(from_date.timestamp())
        if to_date is not None:
            where_clause.append('"time" < %s')
            values.append(to_date.timestamp())

        where_clause = ' AND '.join(where_clause)
        sql = get_sql_for_entry_with_date(where_clause, limit)
        db.execute(sql, values)

        entries = []
        for result in db.fetchall():
            entry = cls(rowdata=result)
            deserialize_joined(entry, result)
            entries.append(entry)
        return entries

    @classmethod
    def load_all_after_id(cls, db: Any, lowest_id: int) -> List["LogEntry"]:
        db.execute(get_sql_for_entry_after_id("%s"), [lowest_id])

        entries = []
        for result in db.fetchall():
            entry = cls(rowdata=result)
            deserialize_joined(entry, result)
            entries.append(entry)
        return entries

    def add_tag(self, db: Any, tag: LogTag):
        cached_tags: Optional[List[LogTag]] = getattr(self, '_tags', None)
        if cached_tags is not None:
            cached_tags.append(tag)

        db.execute(
            'INSERT INTO logger_log_tag ("logID", "tagID") VALUES (%s, %s);',
            [self.pk, tag.pk]
        )

    def add_tags(self, db: Any, tags: List[LogTag]):
        cached_tags: Optional[List[LogTag]] = getattr(self, '_tags', None)
        if cached_tags is not None:
            for tag in tags:
                cached_tags.append(tag)

        if len(tags) == 0:
            return
        values: List[int] = []
        placeholders: List[str] = []
        for tag in tags:
            placeholders.append('(%s, %s)')
            values.append(self.pk)
            values.append(tag.pk)

        sql = f'INSERT INTO logger_log_tag ("logID", "tagID") VALUES {", ".join(placeholders)};'
        db.execute(sql, values)

    def remove_tag(self, db: Any, tag: LogTag):
        cached_tags: Optional[List[LogTag]] = getattr(self, '_tags', None)
        if cached_tags is not None:
            cached_tags.remove(tag)
        db.execute(
            'DELETE FROM logger_log_tag WHERE "logID" = %s AND "tagID" = %s;',
            [self.pk, tag.pk]
        )

    def tags(self, db: Any) -> List[LogTag]:
        cached_tags: Optional[List[LogTag]] = getattr(self, '_tags', None)

        if cached_tags is None:
            cached_tags = []
            sql = f"""
                SELECT t.* FROM logger_log_tag lt
                JOIN logger_tag t ON t.id = lt."tagID"
                WHERE "logID" = %s;
            """
            db.execute(sql, [self.pk])
            result = db.fetchone()
            while result is not None:
                cached_tags.append(LogTag(rowdata=result))
                result = db.fetchone()

        setattr(self, '_tags', cached_tags)
        return cached_tags

    def function(self, db: Any) -> LogFunction:
        result = getattr(self, '_function', LogFunction.load(db, pk=self.function_id))
        setattr(self, '_function', result)
        return result

    def logger(self, db: Any) -> LogLogger:
        result = getattr(self, '_logger', LogLogger.load(db, pk=self.logger_id))
        setattr(self, '_logger', result)
        return result

    def hostname(self, db: Any) -> LogHost:
        result = getattr(self, '_hostname', LogHost.load(db, pk=self.hostname_id))
        setattr(self, '_hostname', result)
        return result

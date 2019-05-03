from typing import List, Dict, Any, Optional
from asyncpg import Connection, Record

from logging import DEBUG
from datetime import datetime, timezone

from dblogger.models.entry import BaseLogEntry, get_sql_for_entry_with_date, get_sql_for_entry_after_id
from .model import AsyncModel
from .tag import LogTag
from .function import LogFunction
from .logger import LogLogger
from .host import LogHost
from .source import LogSource

__all__ = ['LogEntry']


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


class LogEntry(BaseLogEntry, AsyncModel):

    @classmethod
    async def load_all_with_date(
        cls,
        db: Connection,
        from_date: Optional[datetime]=None,
        to_date: Optional[datetime]=None,
        limit: Optional[int]=None
    ) -> List["LogEntry"]:
        if from_date is None and to_date is None and limit is None:
            raise ValueError('Define at least one of `from_date`, `to_date` or `limit`')
        where_clause = []
        values = []
        if from_date is not None:
            where_clause.append(f'"time" > ${len(where_clause) + 1}')
            values.append(from_date.timestamp())
        if to_date is not None:
            where_clause.append(f'"time" < ${len(where_clause) + 1}')
            values.append(to_date.timestamp())

        where_clause = ' AND '.join(where_clause)

        sql = get_sql_for_entry_with_date(where_clause, limit)
        results = await db.fetch(sql, *values)

        entries = []
        for result in results:
            entry = cls(rowdata=result)
            deserialize_joined(entry, result)
            entries.append(entry)
        return entries

    @classmethod
    async def load_all_after_id(cls, db: Connection, lowest_id: int) -> List["LogEntry"]:
        results = await db.fetch(get_sql_for_entry_after_id("$1"), lowest_id)

        entries = []
        for result in results:
            entry = cls(rowdata=result)
            deserialize_joined(entry, result)
            entries.append(entry)
        return entries

    async def add_tag(self, db: Connection, tag: LogTag):
        cached_tags: Optional[List[LogTag]] = getattr(self, '_tags', None)
        if cached_tags is not None:
            cached_tags.append(tag)

        await db.execute(
            'INSERT INTO logger_log_tag ("logID", "tagID") VALUES ($1, $2);',
            self.pk, tag.pk
        )

    async def add_tags(self, db: Connection, tags: List[LogTag]):
        cached_tags: Optional[List[LogTag]] = getattr(self, '_tags', None)
        if cached_tags is not None:
            for tag in tags:
                cached_tags.append(tag)

        if len(tags) == 0:
            return
        values: List[int] = []
        placeholders: List[str] = []
        for idx, tag in enumerate(tags):
            placeholders.append(f'(${(idx * 2) + 1}, ${(idx * 2) + 2})')
            values.append(self.pk)
            values.append(tag.pk)

        sql = f'INSERT INTO logger_log_tag ("logID", "tagID") VALUES {", ".join(placeholders)};'

        await db.execute(sql, *values)

    async def remove_tag(self, db: Connection, tag: LogTag):
        cached_tags: Optional[List[LogTag]] = getattr(self, '_tags', None)
        if cached_tags is not None:
            cached_tags.remove(tag)

        await db.execute(
            'DELETE FROM logger_log_tag WHERE "logID" = $1 AND "tagID" = $2;',
            self.pk, tag.pk
        )

    async def tags(self, db: Connection) -> List[LogTag]:
        cached_tags: Optional[List[LogTag]] = getattr(self, '_tags', None)
        if cached_tags is not None:
            return cached_tags

        cached_tags = []
        sql = f"""
            SELECT t.* FROM logger_log_tag lt
            JOIN logger_tag t ON t.id = lt."tagID"
            WHERE "logID" = $1;
        """
        results = await db.fetch(sql, self.pk)
        for result in results:
            result = await LogTag(rowdata=result)
            cached_tags.append(result)

        setattr(self, '_tags', cached_tags)
        return cached_tags


    async def function(self, db: Connection) -> LogFunction:
        result = getattr(self, '_function', await LogFunction.load(db, pk=self.function_id))
        setattr(self, '_function', result)
        return result

    async def logger(self, db: Connection) -> LogLogger:
        result = getattr(self, '_logger', await LogLogger.load(db, pk=self.logger_id))
        setattr(self, '_logger', result)
        return result

    async def hostname(self, db: Connection) -> LogHost:
        result = getattr(self, '_hostname', await LogHost.load(db, pk=self.hostname_id))
        setattr(self, '_hostname', result)
        return result

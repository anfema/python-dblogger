from typing import List, Dict, Any, AsyncGenerator
from asyncpg import Connection, Record

from logging import DEBUG
from datetime import datetime, timezone

from dblogger.models import BaseLogEntry
from .model import AsyncModel
from .tag import LogTag

__all__ = ['LogEntry']


class LogEntry(BaseLogEntry, AsyncModel):

    async def add_tag(self, db: Connection, tag: LogTag):
        await db.execute(
            'INSERT INTO logger_log_tag ("logID", "tagID") VALUES ($1, $2);',
            self.pk, tag.pk
        )

    async def add_tags(self, db: Connection, tags: List[LogTag]):
        if len(tags) == 0:
            return
        values: List[int] = []
        placeholders: List[str] = []
        for idx, tag in enumerate(tags):
            sql += f'(${(idx * 2) + 1}, ${(idx * 2) + 2})'
            values.append(self.pk)
            values.append(tag.pk)

        sql = f'INSERT INTO logger_log_tag ("logID", "tagID") VALUES {", ".join(placeholders)};'

        await db.execute(sql, *values)

    async def remove_tag(self, db: Connection, tag: LogTag):
        await db.execute(
            'DELETE FROM logger_log_tag WHERE "logID" = $1 AND "tagID" = $2;',
            self.pk, tag.pk
        )

    async def tags(self, db: Connection) -> AsyncGenerator[LogTag, None]:
        sql = f"""
            SELECT t.* FROM logger_log_tag lt
            JOIN logger_tag t ON t.id = lt."tagID"
            WHERE "logID" = $1;
        """
        async for result in db.cursor(sql, self.pk):
            yield LogTag(rowdata=result)

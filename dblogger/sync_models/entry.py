from typing import List, Dict, Any, Generator

from logging import DEBUG
from datetime import datetime, timezone

from dblogger.models import BaseLogEntry
from .model import SyncModel
from .tag import LogTag

__all__ = ['LogEntry']

# FIXME: Psycopg2 does not have type information yet


class LogEntry(BaseLogEntry, SyncModel):

    def add_tag(self, db: Any, tag: LogTag):
        db.execute(
            'INSERT INTO logger_log_tag ("logID", "tagID") VALUES (%s, %s);',
            [self.pk, tag.pk]
        )

    def add_tags(self, db: Any, tags: List[LogTag]):
        if len(tags) == 0:
            return
        values: List[int] = []
        placeholders: List[str] = []
        for tag in tags:
            sql += f'(%s, %s)'
            values.append(self.pk)
            values.append(tag.pk)

        sql = f'INSERT INTO logger_log_tag ("logID", "tagID") VALUES {", ".join(placeholders)};'
        db.execute(sql, values)

    def remove_tag(self, db: Any, tag: LogTag):
        db.execute(
            'DELETE FROM logger_log_tag WHERE "logID" = %s AND "tagID" = %s;',
            [self.pk, tag.pk]
        )

    def tags(self, db: Any) -> Generator[LogTag, None, None]:
        sql = f"""
            SELECT t.* FROM logger_log_tag lt
            JOIN logger_tag t ON t.id = lt."tagID"
            WHERE "logID" = %s;
        """
        db.execute(sql, [self.pk])
        result = db.fetchone()
        while result is not None:
            yield LogTag(rowdata=result)
            result = db.fetchone()

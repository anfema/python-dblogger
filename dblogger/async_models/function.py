from typing import Any
from asyncpg import Connection

from dblogger.models.function import BaseLogFunction
from .model import AsyncModel
from .source import LogSource


class LogFunction(BaseLogFunction, AsyncModel):

    async def source(self, db: Connection) -> LogSource:
        result = getattr(self, '_source', await LogSource.load(db, pk=self.source_id))
        setattr(self, '_source', result)
        return result

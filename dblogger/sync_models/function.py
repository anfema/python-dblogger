from typing import Any, Generator

from dblogger.models.function import BaseLogFunction
from .model import SyncModel
from .source import LogSource


class LogFunction(BaseLogFunction, SyncModel):

    def source(self, db: Any) -> LogSource:
        result = getattr(self, '_source', LogSource.load(db, pk=self.source_id))
        setattr(self, '_source', result)
        return result

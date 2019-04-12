from dblogger.models.function import BaseLogFunction
from dblogger.models.host import BaseLogHost
from dblogger.models.logger import BaseLogLogger
from dblogger.models.source import BaseLogSource
from .tag import LogTag
from .entry import LogEntry
from .model import AsyncModel

__all__ = ['LogEntry', 'LogFunction', 'LogHost', 'LogLogger', 'LogSource', 'LogTag']


class LogFunction(BaseLogFunction, AsyncModel):
    pass


class LogHost(BaseLogHost, AsyncModel):
    pass


class LogLogger(BaseLogLogger, AsyncModel):
    pass


class LogSource(BaseLogSource, AsyncModel):
    pass

from dblogger.models.function import BaseLogFunction
from dblogger.models.host import BaseLogHost
from dblogger.models.logger import BaseLogLogger
from dblogger.models.source import BaseLogSource
from .tag import LogTag
from .entry import LogEntry
from .model import SyncModel

__all__ = ['LogEntry', 'LogFunction', 'LogHost', 'LogLogger', 'LogSource', 'LogTag']


class LogFunction(BaseLogFunction, SyncModel):
    pass


class LogHost(BaseLogHost, SyncModel):
    pass


class LogLogger(BaseLogLogger, SyncModel):
    pass


class LogSource(BaseLogSource, SyncModel):
    pass

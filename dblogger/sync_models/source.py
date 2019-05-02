from dblogger.models.source import BaseLogSource
from .model import SyncModel


class LogSource(BaseLogSource, SyncModel):
    pass

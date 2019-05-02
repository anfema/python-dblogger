from dblogger.models.logger import BaseLogLogger
from .model import SyncModel


class LogLogger(BaseLogLogger, SyncModel):
    pass

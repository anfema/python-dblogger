from dblogger.models.host import BaseLogHost
from .model import SyncModel


class LogHost(BaseLogHost, SyncModel):
    pass

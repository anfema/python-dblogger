from dblogger.models.host import BaseLogHost
from .model import AsyncModel


class LogHost(BaseLogHost, AsyncModel):
    pass

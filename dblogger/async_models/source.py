from dblogger.models.source import BaseLogSource
from .model import AsyncModel


class LogSource(BaseLogSource, AsyncModel):
    pass

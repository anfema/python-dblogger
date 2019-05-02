from dblogger.models.logger import BaseLogLogger
from .model import AsyncModel


class LogLogger(BaseLogLogger, AsyncModel):
    pass

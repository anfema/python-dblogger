from dblogger.models.tag import BaseLogTag
from .model import AsyncModel

class LogTag(BaseLogTag, AsyncModel):
    pass

from typing import List
from logging import LoggerAdapter, Logger

__all__ = ['TaggedLogger']


class TaggedLogger(LoggerAdapter):
    tags: List[str]

    def __init__(self, logger: Logger, *args):
        self.tags = [str(a) for a in args]
        super().__init__(logger, None)

    def process(self, msg, kwargs):
        """
        Process the logging message and keyword arguments passed in to
        a logging call to insert contextual information.
        """
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        if 'tags' not in kwargs['extra']:
            kwargs['extra']['tags'] = set()
        kwargs['extra']['tags'].update(self.tags)
        return msg, kwargs

from typing import List, Any, Optional, Dict, Tuple
import socket

from datetime import datetime
from logging import Handler, Logger, NOTSET, LogRecord

import psycopg2
from psycopg2.extras import DictCursor

from .sync_models import LogLogger, LogSource, LogHost, LogFunction, LogTag, LogEntry

__all__ = ['DBLogHandler']


class DBLogHandler(Handler):

    # db config and connection
    db_config: Optional[str] = None

    # caches
    src_cache: Dict[str, LogSource] = {}
    func_cache: Dict[str, LogFunction] = {}
    logger_cache: Dict[str, LogLogger] = {}
    host_cache: Dict[str, LogHost] = {}
    tag_cache: Dict[str, LogTag] = {}

    # internal state
    logger_name: str

    def __init__(
        self, name: str,
        db_name: Optional[str]=None,
        db: Optional[Any]=None,
        db_user: Optional[str]=None,
        db_password: Optional[str]=None,
        db_host: str='localhost',
        db_port: int=5432,
        level: int = NOTSET
    ):
        """
        Initialize new DB logging handler

        :param name: Name of the logger in the DB
        :param db_name: DB name to use (exclusive with ``db``)
        :param db: DB handle to use (exclusive with ``db_name``)
        :param db_user: DB user name (optional)
        :param db_password: DB password (optional)
        :param db_host: DB hostname (optional, defaults to ``localhost``)
        :param db_port: DB port (optional, defaults to ``5432``)
        :param level: Log level, defaults to ``NOTSET`` which inherits the level from the logger
        """

        if db is not None:
            self.db = db
            self.db_config = None
        else:
            if db_user is not None:
                if db_password is not None:
                    self.db_config = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
                else:
                    self.db_config = f'postgresql://{db_user}@{db_host}:{db_port}/{db_name}'
            else:
                self.db_config = f'postgresql://{db_host}:{db_port}/{db_name}'
            self.db = psycopg2.connect(self.db_config, cursor_factory=DictCursor)

        self.logger_name = name
        self.createLock()
        super().__init__(level=level)

    def emit(self, record: LogRecord):
        if self.db.closed and self.db_config is not None:
            self.db = psycopg2.connect(self.db_config, cursor_factory=DictCursor)
        elif self.db.closed:
            raise RuntimeWarning('DB handle was closed, can not continue')

        cursor = self.db.cursor()

        try:
            src = self.src_cache.get(record.pathname, None)
            if src is None:
                src = LogSource.get_or_create(cursor, path=record.pathname)
                self.src_cache[record.pathname] = src

            func_key = f'{record.name}.{record.funcName}:{record.lineno}@{src.path}'
            func = self.func_cache.get(func_key, None)
            if func is None:
                func = LogFunction.get_or_create(
                    cursor,
                    name=f'{record.name}.{record.funcName}',
                    line_number=record.lineno,
                    source_id=src.pk,
                )
                self.func_cache[func_key] = func

            logger = self.logger_cache.get(self.logger_name, None)
            if logger is None:
                logger = LogLogger.get_or_create(cursor, name=self.logger_name)
                self.logger_cache[self.logger_name] = logger

            host_key = socket.gethostname()
            host = self.host_cache.get(host_key, None)
            if host is None:
                host = LogHost.get_or_create(cursor, name=host_key)
                self.host_cache[host_key] = host

            entry = LogEntry.create(
                cursor,
                level=record.levelno,
                message=record.getMessage(),
                pid=record.process,
                time=datetime.fromtimestamp(record.created),
                function_id=func.pk,
                logger_id=logger.pk,
                hostname_id=host.pk
            )

            tags_names = getattr(record, 'tags', set())
            tags: List[LogTag] = []
            for tag_name in tags_names:
                if tag_name is None or tag_name == '':
                    continue
                tag = self.tag_cache.get(tag_name, None)
                if tag is None:
                    tag = LogTag.get_or_create(cursor, name=tag_name)
                    self.tag_cache[tag_name] = tag

                tags.append(tag)

            entry.add_tags(cursor, tags)
            self.db.commit()

        except Exception:
            self.handleError(record)

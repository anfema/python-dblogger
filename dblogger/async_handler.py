from typing import List, Any, Optional, Dict, Tuple
import asyncio
import socket

from datetime import datetime
from logging import Handler, Logger, NOTSET, LogRecord, getLogger

from asyncpg import Connection, connect
from asyncpg.pool import Pool

from .async_models import LogLogger, LogSource, LogHost, LogFunction, LogTag, LogEntry

__all__ = ['DBLogHandler', 'AsyncFilter']


class AsyncFilter():

    async def async_filter(self, record: LogRecord):
        return True

logger = getLogger('dblogger')


class DBLogHandler(Handler):

    # db config and connection
    db: Optional[Pool] = None
    db_config: Optional[str] = None

    # state
    queue: List[LogRecord] = []
    emitter: Optional[asyncio.Task] = None

    # caches
    src_cache: Dict[str, LogSource] = {}
    func_cache: Dict[str, LogFunction] = {}
    logger_cache: Dict[str, LogLogger] = {}
    host_cache: Dict[str, LogHost] = {}
    tag_cache: Dict[str, LogTag] = {}

    # internal state
    logger_name: str
    async_filters: List[AsyncFilter]

    def __init__(
        self, name: str,
        db_name: Optional[str]=None,
        db: Optional[Pool]=None,
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

        self.async_filters = []
        self.logger_name = name
        self.createLock()
        super().__init__(level=level)

    def addAsyncFilter(self, filter: AsyncFilter):
        """
        Add the specified async filter to this handler.
        """
        if not (filter in self.async_filters):
            self.async_filters.append(filter)

    def removeAsyncFilter(self, filter: AsyncFilter):
        """
        Remove the specified async filter from this handler.
        """
        if filter in self.async_filters:
            self.async_filters.remove(filter)

    def emit(self, record: LogRecord):
        self.acquire()
        self.queue.append(record)

        if self.emitter is None:
            loop = asyncio.get_event_loop()
            self.emitter = loop.create_task(self.log_emitter())
        self.release()

    async def drain(self):
        if len(self.queue) > 0 and self.emitter is None:
            await self.log_emitter()

        if self.emitter is not None:
            await self.emitter

    async def log_emitter(self):
        if self.db is None:
            if self.db_config is None:
                raise RuntimeWarning('DB handle was closed, can not continue')
            self.acquire()
            self.db = await connect(dsn=self.db_config)
            self.release()

        while len(self.queue) > 0:
            self.acquire()
            q = self.queue
            self.queue = []
            self.release()

            try:
                for record in q:
                    await self.async_emit(record)
            except Exception as e:
                self.emitter = None
                logger.exception(e)

        self.emitter = None

    async def async_emit(self, record: LogRecord):
        # run all async filters
        rv = True
        for f in self.async_filters:
            try:
                if hasattr(f, 'async_filter'):
                    result = await f.async_filter(record)
                else:
                    result = await f(record) # assume callable - will raise if not
                if not result:
                    rv = False
                    break
            except Exception as e:
                rv = True
                logger.exception(e)
        if not rv:
            return

        try:
            src = self.src_cache.get(record.pathname, None)
            if src is None:
                src = await LogSource.get_or_create(self.db, path=record.pathname)
                self.src_cache[record.pathname] = src

            func_key = f'{record.name}.{record.funcName}:{record.lineno}@{src.path}'
            func = self.func_cache.get(func_key, None)
            if func is None:
                func = await LogFunction.get_or_create(
                    self.db,
                    name=f'{record.name}.{record.funcName}',
                    line_number=record.lineno,
                    source_id=src.pk,
                )
                self.func_cache[func_key] = func

            logger = self.logger_cache.get(self.logger_name, None)
            if logger is None:
                logger = await LogLogger.get_or_create(self.db, name=self.logger_name)
                self.logger_cache[self.logger_name] = logger

            host_key = socket.gethostname()
            host = self.host_cache.get(host_key, None)
            if host is None:
                host = await LogHost.get_or_create(self.db, name=host_key)
                self.host_cache[host_key] = host

            entry = await LogEntry.create(
                self.db,
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
                tag = self.tag_cache.get(tag_name, None)
                if tag is None:
                    tag = await LogTag.get_or_create(self.db, name=tag_name)
                    self.tag_cache[tag_name] = tag

                tags.append(tag)

            await entry.add_tags(self.db, tags)

        except Exception:
            self.handleError(record)

from typing import List, Any, Optional, Dict, Tuple, Deque
import asyncio
import socket

from datetime import datetime
from collections import deque
from logging import Handler, Logger, NOTSET, LogRecord

from asyncpg import Connection, connect
from asyncpg.pool import Pool

from .async_models import LogLogger, LogSource, LogHost, LogFunction, LogTag, LogEntry

__all__ = ['DBLogHandler', 'AsyncFilter']


class AsyncFilter():

    async def async_filter(self, record: LogRecord):
        return True


class DBLogHandler(Handler):

    # db config and connection
    db: Optional[Pool] = None
    db_config: Optional[str] = None

    # state
    queue: Deque[LogRecord] = deque()
    start_emitting: asyncio.Future
    stop_emitting: asyncio.Future

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

        loop = asyncio.get_event_loop()
        self.start_emitting = loop.create_future()
        self.stop_emitting = loop.create_future()
        self.stop_emitting.set_result(True)
        loop.create_task(self.log_emitter())

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
        self.queue.append(record)

        if not self.start_emitting.done():
            self.start_emitting.set_result(True)

    async def drain(self):
        if not self.stop_emitting.done():
            await self.stop_emitting

    async def log_emitter(self):
        if self.db is None:
            if self.db_config is None:
                raise RuntimeWarning('DB handle was closed, can not continue')
            self.acquire()
            try:
                self.db = await connect(dsn=self.db_config)
            except Exception:
                return
            self.release()

        loop = asyncio.get_event_loop()

        try:
            while True:
                await self.start_emitting
                self.stop_emitting = loop.create_future()

                try:
                    record = self.queue.popleft()
                except IndexError:
                    record = None

                while record is not None:
                    await self.async_emit(record)
                    try:
                        record = self.queue.popleft()
                    except IndexError:
                        break

                self.stop_emitting.set_result(True)
                self.start_emitting = loop.create_future()
        except asyncio.CancelledError:
            return

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
            except Exception:
                rv = True
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
                if tag_name is None or tag_name == '':
                    continue
                tag = self.tag_cache.get(tag_name, None)
                if tag is None:
                    tag = await LogTag.get_or_create(self.db, name=tag_name)
                    self.tag_cache[tag_name] = tag

                tags.append(tag)

            await entry.add_tags(self.db, tags)

        except Exception:
            self.handleError(record)

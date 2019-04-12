try:
    import asyncpg
    from .async_handler import DBLogHandler
except ImportError:
    try:
        import psycopg2
        from .sync_handler import DBLogHandler
    except ImportError:
        raise RuntimeError("Please install a database driver, you'll need either psycopg2 or asyncpg")

from .taggedlogger import TaggedLogger

__all__ = ['DBLogHandler', 'TaggedLogger']

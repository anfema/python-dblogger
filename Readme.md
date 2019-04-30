Database logging made easy

## Requirements

- PostgreSQL Database
- either `psycopg2` or `asyncpg`

## Usage

### Initialization

Just add the `DBLogHandler` to your logging stack.
The log handler will automatically detect if you want to use the async version or
the default version by looking for the availability of the corresponding DB-Driver.

This means if you have `asyncpg` installed it will default to async logging and
if you have just `psycopg2` installed it will default to synchronous logging like
you know it.

Example:

```python
from typing import Dict, Any
from dblogger import DBLogHandler
from logging import getLogger


def setup_logger(config: Dict[str, Any]):
    root_logger = getLogger()
    handler = DBLogHandler(
        config['logger_name'],
        config['db'],
        db_user=config.get('user', None),
        db_password=config.get('password', None),
        db_host=config.get('host', 'localhost'),
        db_port=config.get('port', 5432)
    )
    root_logger.addHandler(handler)
```

You may give the log-handler a DB handle instead of a DB configuration if you want to
handle the DB connection yourself (or your framework already handles the DB connections).
For that, just skip all ``db_`` parameters and give the handle to the handler with the
``db`` parameter. Be aware that a failed connection can not be handled internally this
way, so if your connection breaks you have to pick up the pieces by yourself.

### Tagging

To add tags to your log info, use the `extra` kwarg of the logger.

Example:

```python
from logging import getLogger
logger = getLogger(__name__)

logger.debug('This is a debug message tagged with "a" and "b"', extra={'tags': ['a', 'b']})
```

If you want to add the same tag to multiple log lines, use the `TaggedLogger` log adapter:

```python
from dblogger import TaggedLogger

tagged = TaggedLogger(logger, 'a', 'b')
tagged.debug('This tagged logger will add tags "a" and "b" to all log records')
tagged.debug('You may even add more tags like "c"', extra={'tags': ['c']})
```

### Setting up the database

To initialize the logging schema in the database import the `schema.sql` SQL file in the
data dir of this package.

TODO: Make setup script

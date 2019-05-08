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

# Import the DBLogHandler from dblogger directly to auto-detect the used DB
# Adapter
from dblogger import DBLogHandler

# Alternatively import the correct handler directly:
# ``from dblogger.sync_handler import DBLogHandler``
# or
# ``from dblogger.async_handler import DBLogHandler``

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

### Special considerations for async logging

#### Draining the log queue before shutting down

If you're using the async log handler make sure to run the `drain()` function before
stopping the event loop:

```python
await handler.drain()
```

#### Async filters

If you need an `async` filter (for example a filter that loads information from a DB)
you can import `AsyncFilter` from the `async_handler` submodule and add those to the
log handler with the corresponding functions:

```python
from dblogger.async_handler import AsyncFilter

class MyAsyncFilter(AsyncFilter):

    async def async_filter(self, record: logging.LogRecord):
        return True

filter = MyAsyncFilter()

# add filter
handler.addAsyncFilter(filter)

# remove filter
handler.removeAsyncFilter(filter)
```


### Setting up the database

To initialize the logging schema in the database import the `schema.sql` SQL file in the
data dir of this package.

TODO: Make setup script


### Searching the log from the command line

To access the log DB from the commandline a script named `logtail` will be installed in the
virtualenv bin directory. Be sure to activate the virtualenv before running the command or run
it through `pipenv run logtail`

To set the DB connection options you may either set the environment variable `PGURI` or supply
the connection string with the `--db` parameter on the command line.

```
usage: logtail [-h] [--db DB] [--exclude EXCLUDE] [--level LEVEL]
               [--logger LOGGER [LOGGER ...]]
               [--exclude-tag EXCLUDE_TAG [EXCLUDE_TAG ...]]
               [--tags ONLY_TAGS [ONLY_TAGS ...]] [--from FROM_DATE]
               [--to TO_DATE]

Display a tail -f like log output

optional arguments:
  -h, --help            show this help message and exit
  --db DB               DB Connection URI, if not set defaults to the
                        environment variable `PGURI` or an empty value
  --exclude EXCLUDE     Exclude log items that match the regex
  --level LEVEL         Only display log items with this level or higher (use
                        name or int)
  --logger LOGGER [LOGGER ...]
                        Only display items of one of these named loggers
  --exclude-tag EXCLUDE_TAG [EXCLUDE_TAG ...]
                        Exclude log items that match this tag
  --tags ONLY_TAGS [ONLY_TAGS ...]
                        Only display log items that match at least one of the
                        tags
  --from FROM_DATE      Display log items from this date (1 hour interval)
  --to TO_DATE          Display log items to this date (to override the 1 hour
                        interval from --from)
```

from typing import List, Dict, Any, Tuple, Optional, AsyncGenerator, ClassVar
from asyncpg import Connection, Record

from dblogger.models.model import BaseModel

__all__ = ['AsyncModel']


class AsyncModel(BaseModel):

    @classmethod
    async def load(cls, db: Connection, **kwargs) -> Optional[Any]:
        ser = cls.serialize_data(kwargs)
        where_clause, values = BaseModel.make_where_statement(ser)

        data = await db.fetchrow(f'SELECT * FROM {cls.table} WHERE {where_clause};', *values)
        if data is None:
            return None
        return cls(rowdata=data)

    @classmethod
    async def load_all(cls, db: Connection, **kwargs) -> List[Any]:
        ser = cls.serialize_data(kwargs)
        where_clause, values = BaseModel.make_where_statement(ser)

        result = await db.fetch(f'SELECT * FROM {cls.table} WHERE {where_clause};', *values)
        return [cls(rowdata=data) for data in result]

    @classmethod
    async def create(cls, db: Connection, ignore_conflicts: bool=False, **kwargs) -> Any:
        ser = cls.serialize_data(kwargs)

        value_list = [f'"{v}"' for v in ser.keys()]
        values = ser.values()
        params = ', '.join([f'${idx + 1}' for idx, _ in enumerate(values)])

        sql = f'''
            INSERT INTO {cls.table} ({', '.join(value_list)})
            VALUES ({params})
        '''

        if ignore_conflicts is True:
            sql += ' ON CONFLICT DO NOTHING'

        sql += ' RETURNING *'
        data = await db.fetchrow(sql, *values)
        return cls(rowdata=data)

    @classmethod
    async def get_or_create(cls, db: Connection, **kwargs) -> Any:
        item = await cls.load(db, **kwargs)
        if item is None:
            item = await cls.create(db, **kwargs)
        return item

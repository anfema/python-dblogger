from typing import List, Dict, Any, Tuple, Optional, ClassVar

from dblogger.models.model import BaseModel

__all__ = ['SyncModel']

# FIXME: psycopg2 does not have any type information yet


class SyncModel(BaseModel):

    @classmethod
    def make_where_statement(cls, data: Dict[str, Any], prefix: Optional[str]=None) -> Tuple[str, List[Any]]:
        where: List[str] = []
        values: List[Any] = []
        for item in data.items():
            key, value = item
            key = key.replace("'", "''")
            if prefix is not None:
                where.append(f'"{prefix}.{key}" = %s')
            else:
                where.append(f'"{key}" = %s')
            values.append(value)

        where_clause = ' AND '.join(where)
        return where_clause, values

    @classmethod
    def load(cls, db: Any, **kwargs) -> Optional[Any]:
        pk = kwargs.pop('pk', None)
        ser = cls.serialize_data(kwargs)
        if pk is not None:
            ser['id'] = pk
        where_clause, values = SyncModel.make_where_statement(ser)

        db.execute(f'SELECT * FROM {cls.table} WHERE {where_clause};', values)
        data = db.fetchone()
        if data is None:
            return None
        return cls(rowdata=data)

    @classmethod
    def load_all(cls, db: Any, **kwargs) -> List[Any]:
        ser = cls.serialize_data(kwargs)
        where_clause, values = SyncModel.make_where_statement(ser)

        db.execute(f'SELECT * FROM {cls.table} WHERE {where_clause};', values)
        return [cls(rowdata=data) for data in db.fetchall()]

    @classmethod
    def create(cls, db: Any, ignore_conflicts: bool=False, **kwargs) -> Any:
        ser = cls.serialize_data(kwargs)

        value_list = [f'"{v}"' for v in ser.keys()]
        values = ser.values()
        params = ', '.join([f'%s' for _ in values])

        sql = f'''
            INSERT INTO {cls.table} ({', '.join(value_list)})
            VALUES ({params})
        '''

        if ignore_conflicts is True:
            sql += ' ON CONFLICT DO NOTHING'

        sql += ' RETURNING *'
        db.execute(sql, list(values))
        data = db.fetchone()
        return cls(rowdata=data)

    @classmethod
    def get_or_create(cls, db: Any, **kwargs) -> Any:
        item = cls.load(db, **kwargs)
        if item is None:
            item = cls.create(db, **kwargs)
        return item

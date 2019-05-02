from typing import List, Dict, Any, Tuple, Optional, ClassVar

__all__ = ['BaseModel']


class BaseModel:
    table: ClassVar[str] = ""

    def __init__(self, rowdata: Optional[Dict] = None, **kwargs):
        if rowdata is not None:
            self.pk = rowdata.get('id', None)
            self.deserialize(rowdata)
        else:
            self.deserialize(kwargs)

    def deserialize(self, rowdata: Dict) -> None:
        """
        DB Record to model conversion
        Has to be overridden in subclasses

        Attention: you do not need to de-serialize the ``id``, this is done automatically

        :param rowdata: The DB record from asyncpg from which to de-serialize
        """
        raise NotImplementedError('Subclasses of Model have to override .deserialize()')

    def serialize(self) -> Dict[str, Any]:
        return self.__class__.serialize_data(self.__dict__)

    @classmethod
    def serialize_data(cls, data) -> Dict[str, Any]:
        """
        Model to DB-Record conversion
        Has to be overridden in subclasses

        Attention: do not serialize the ``id`` property

        :return: Dictionary with key-value pairs to save to DB
        """
        raise NotImplementedError('Subclasses of Model have to override .serialize_data()')

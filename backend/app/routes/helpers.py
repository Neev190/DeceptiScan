import uuid
from app import db

def find_by_id(model_cls, record_id):
    """
    Find a record by ID supporting PostgreSQL native UUID and SQLite string/hex/bytes representations.
    """
    if not record_id:
        return None
    try:
        if isinstance(record_id, uuid.UUID):
            u = record_id
        else:
            u = uuid.UUID(str(record_id))
        
        res = db.session.get(model_cls, u)
        if res:
            return res

        hex_str = u.hex
        hyphen_str = str(u)
        bytes_val = u.bytes

        return model_cls.query.filter(
            (model_cls.id == u) |
            (model_cls.id == hyphen_str) |
            (model_cls.id == hex_str) |
            (model_cls.id == bytes_val)
        ).first()
    except Exception:
        return None

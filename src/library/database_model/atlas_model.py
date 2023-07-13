from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Boolean, DateTime
from datetime import datetime

Base = declarative_base()


class AtlasModel(object):
    """This is the base model that is inherited by most of the other classes (models).
    It includes common fields that all the models need.
    """

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    __table_args__ = {'mysql_engine': 'InnoDB'}
    __mapper_args__ = {'always_refresh': True}

    created = Column(DateTime, default=datetime.now())
    active = Column(Boolean, default=True, nullable=False)

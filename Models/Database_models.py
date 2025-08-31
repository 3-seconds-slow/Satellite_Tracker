from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column



class Base(DeclarativeBase):
    pass

class Satellite(Base):
    __tablename__ = 'Satellite'

    # id = Column(Integer, primary_key=True)
    OBJECT_ID:Mapped[str] = mapped_column(primary_key=True)
    OBJECT_NAME:Mapped[str]
    EPOCH:Mapped[str]
    MEAN_MOTION:Mapped[float]
    ECCENTRICITY:Mapped[float]
    INCLINATION:Mapped[float]
    RA_OF_ASC_NODE:Mapped[float]
    ARG_OF_PERICENTER:Mapped[float]
    MEAN_ANOMALY:Mapped[float]
    EPHEMERIS_TYPE:Mapped[float]
    CLASSIFICATION_TYPE:Mapped[str]
    NORAD_CAT_ID:Mapped[int]
    ELEMENT_SET_NO:Mapped[int]
    REV_AT_EPOCH:Mapped[int]
    BSTAR:Mapped[float]
    MEAN_MOTION_DOT:Mapped[float]
    MEAN_MOTION_DDOT:Mapped[float]
    updated:Mapped[datetime]
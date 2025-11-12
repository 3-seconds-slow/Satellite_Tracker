from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Satellite(Base):
    """
    The Satellite class contains the schema for the satellite table.

    The OBJECT_ID, OBJECT_NAME and EPOCH columns are extracted from the TLE data. line 1 and line 2 columns contain the
    raw TLE data, and updated stores a timestamp of the last time the row was updated.

    I chose to store the raw TLE rather than extracting all the data into separate columns to make it easier to build
    EarthSatellite objects for use in Skyfields's calculations, and so the data can later be exported to a file.
    """
    __tablename__ = 'Satellite'

    OBJECT_ID:Mapped[str] = mapped_column(primary_key=True)
    OBJECT_NAME:Mapped[str]
    EPOCH:Mapped[str]
    line1:Mapped[str]
    line2:Mapped[str]
    updated:Mapped[datetime]
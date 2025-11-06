import json
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

'''
Ok, so I was trying to find a way 
'''

class Satellite(Base):
    __tablename__ = 'Satellite'

    # id = Column(Integer, primary_key=True)
    OBJECT_ID:Mapped[str] = mapped_column(primary_key=True)
    OBJECT_NAME:Mapped[str]
    EPOCH:Mapped[str]
    # MEAN_MOTION:Mapped[float]
    # ECCENTRICITY:Mapped[float]
    # INCLINATION:Mapped[float]
    # RA_OF_ASC_NODE:Mapped[float]
    # ARG_OF_PERICENTER:Mapped[float]
    # MEAN_ANOMALY:Mapped[float]
    # EPHEMERIS_TYPE:Mapped[int]
    # CLASSIFICATION_TYPE:Mapped[str]
    # NORAD_CAT_ID:Mapped[int]
    # ELEMENT_SET_NO:Mapped[int]
    # REV_AT_EPOCH:Mapped[int]
    # BSTAR:Mapped[float]
    # MEAN_MOTION_DOT:Mapped[float]
    # MEAN_MOTION_DDOT:Mapped[int]

    line1:Mapped[str]
    line2:Mapped[str]

    updated:Mapped[datetime]

    def set_raw_text(self, data: dict):
        self.raw_text = json.dumps(data)
        self.OBJECT_NAME = data.get("OBJECT_NAME")
        self.EPOCH = data.get("EPOCH")
        self.updated = datetime.now()

    def get_raw_text(self) -> dict:
        return json.loads(self.raw_json) if self.raw_json else {}
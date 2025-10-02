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

    raw_json:Mapped[str]

    updated:Mapped[datetime]

    def set_raw_json(self, data: dict):
        self.raw_json = json.dumps(data)
        self.OBJECT_NAME = data.get("OBJECT_NAME")
        self.EPOCH = data.get("EPOCH")
        self.updated = datetime.now()

    def get_raw_json(self) -> dict:
        return json.loads(self.raw_json) if self.raw_json else {}
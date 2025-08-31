import pandas as pd
from Models.Database_models import Base, Satellite
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = None

def create_database(db_filename, testing: bool = False):
    global engine
    if testing:
        print("Using in-memory SQLite database (testing mode)")
        engine = create_engine("sqlite:///:memory:", echo=False)
    else:
        print(f"Using file-based SQLite database: {db_filename}")
        engine = create_engine(f"sqlite:///{db_filename}", echo=False)

    Base.metadata.create_all(bind=engine)

def save(response):
    session = sessionmaker(bind=engine)
    with session.begin() as session:
        for sat in response:
            satellite = Satellite(
                OBJECT_ID=sat["OBJECT_ID"],
                OBJECT_NAME=sat["OBJECT_NAME"],
                EPOCH=sat["EPOCH"],
                MEAN_MOTION=sat["MEAN_MOTION"],
                ECCENTRICITY=sat["ECCENTRICITY"],
                INCLINATION=sat["INCLINATION"],
                RA_OF_ASC_NODE=sat["RA_OF_ASC_NODE"],
                ARG_OF_PERICENTER=sat["ARG_OF_PERICENTER"],
                MEAN_ANOMALY=sat["MEAN_ANOMALY"],
                EPHEMERIS_TYPE=sat["EPHEMERIS_TYPE"],
                CLASSIFICATION_TYPE=sat["CLASSIFICATION_TYPE"],
                NORAD_CAT_ID=sat["NORAD_CAT_ID"],
                ELEMENT_SET_NO=sat["ELEMENT_SET_NO"],
                REV_AT_EPOCH=sat["REV_AT_EPOCH"],
                BSTAR=sat["BSTAR"],
                MEAN_MOTION_DOT=sat["MEAN_MOTION_DOT"],
                MEAN_MOTION_DDOT=sat["MEAN_MOTION_DDOT"],
                updated=datetime.now()
            )
            session.merge(satellite)
        session.commit()
        print("✅ Satellites saved to database")

# retrieves all the satellite data from the database and returns pandas dataframes for all satellites
def get_satellite_list():
    session = sessionmaker(bind=engine)
    with session.begin() as session:
        satellites = session.query(Satellite).all()
        data = [
            {column.name: getattr(sat, column.name) for column in Satellite.__table__.columns}
            for sat in satellites
        ]
        satellites_df = pd.DataFrame(data)
        print(satellites_df)
        return satellites_df



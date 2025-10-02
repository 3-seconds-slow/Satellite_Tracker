import pandas as pd
from skyfield.api import EarthSatellite, load
from Models.Database_models import Base, Satellite
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = None
ts = load.timescale()

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
            )
            satellite.set_raw_json(sat)
            session.merge(satellite)
        session.commit()
        print("✅ Satellites saved to database")

# retrieves all the satellite data from the database and returns pandas dataframes for all satellites
def get_satellite_list():
    session = sessionmaker(bind=engine)
    satellites = []
    with session.begin() as session:
        for sat in session.query(Satellite).all():
            raw_json = sat.get_raw_json()
            esat = EarthSatellite.from_omm(ts, raw_json)
            satellites.append(esat)

        print('Loaded', len(satellites), 'satellites')
        print(satellites)
        return satellites



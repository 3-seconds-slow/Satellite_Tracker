import pandas as pd
from skyfield.api import EarthSatellite, load
from skyfield.iokit import parse_tle_file
from Models.Database_models import Base, Satellite
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from itertools import islice
from io import BytesIO, StringIO

engine = None
satellite_lookup = {}
ts = load.timescale()

def create_database(db_filename, testing: bool = False):
    global engine
    if testing:
        print("Using in-memory SQLite database (testing mode)")
        engine = create_engine("sqlite:///:memory:",
                               echo=False,
                               connect_args={"check_same_thread": False},
                               poolclass=StaticPool)
    else:
        print(f"Using file-based SQLite database: {db_filename}")
        engine = create_engine(f"sqlite:///{db_filename}", echo=False)

    Base.metadata.create_all(bind=engine)

def save(data):
    session = sessionmaker(bind=engine)
    count = 0
    with session.begin() as session:
        print("data: ",data)
        f = BytesIO(data)

        satellites = list(parse_tle_file_modified(f))
        print("satellites: ", satellites)
        for name, line1, line2 in satellites:
            print("name: ", name)
            print("line1: ", line1)
            print("line2: ", line2)
            sat_obj = EarthSatellite(line1, line2, name, ts)

            print("sat_obj: ", sat_obj)


            satellite = Satellite(
                OBJECT_ID=sat_obj.model.satnum,
                OBJECT_NAME=sat_obj.name,
                EPOCH=sat_obj.epoch.utc_strftime("%Y-%m-%dT%H:%M:%SZ"),
                line1=line1.rstrip(),
                line2=line2.rstrip(),
                updated=datetime.now(),
                )
            session.merge(satellite)
        session.commit()
        count = len(satellites)
        print(f"{count} satellites saved to database")

    return count


# retrieves all the satellite data from the database and returns pandas dataframes for all satellites
def get_satellite_list():
    global satellite_lookup
    print("retrieving satellite list")
    session = sessionmaker(bind=engine)
    satellites = []
    with session.begin() as session:
        for sat in session.query(Satellite).all():
            sat_object = EarthSatellite(sat.line1, sat.line2, sat.OBJECT_NAME, ts)
            satellites.append(sat_object)

        # print('Loaded', len(satellites), 'satellites')
        # print(satellites)
        satellite_lookup = {sat.model.satnum: sat for sat in satellites}
        print("Lookup keys (first 10):", list(satellite_lookup.keys())[:10])
        return satellites

def get_satellite_lookup():
    return satellite_lookup

'''
This is a modified version of the skyfield.iokit.parse_tle_file function that yields a list containing the tls lines in
string form, rather than a list of satellite objects. this change was made so that the tle data could be stored in the 
database for export into a file
'''
def parse_tle_file_modified(lines, skip_names=False):
    print("parsing ", lines)

    b0 = b1 = b''
    for b2 in lines:
        if (b2.startswith(b'2 ') and len(b2) >= 69 and
            b1.startswith(b'1 ') and len(b1) >= 69):

            if not skip_names and b0:
                b0 = b0.rstrip(b' \n\r')
                if b0.startswith(b'0 '):
                    b0 = b0[2:]  # Spacetrack 3-line format
                name = b0.decode('ascii')
            else:
                name = None

            line1 = b1.decode('ascii')
            line2 = b2.decode('ascii')
            print("name: ", name)
            print("line1: ", line1)
            print("line2: ", line2)
            yield name, line1, line2

            b0 = b1 = b''  # don't accidentally use line 2 as next sat's name
        else:
            b0 = b1
            b1 = b2

def get_satellite_data(id_list=None):
    satellite_data = []
    if id_list is None:
        session = sessionmaker(bind=engine)
        with session.begin() as session:
            for sat in session.query(Satellite).all():
                satellite_data.append((sat.OBJECT_NAME, sat.line1, sat.line2))
    else:
        session = sessionmaker(bind=engine)
        with session.begin() as session:
            for sat in session.query(Satellite).filter(Satellite.OBJECT_ID.in_(id_list)).all():
                satellite_data.append((sat.OBJECT_NAME, sat.line1, sat.line2))

    return satellite_data
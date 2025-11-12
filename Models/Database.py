from skyfield.api import EarthSatellite, load
from Models.Database_models import Base, Satellite
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from io import BytesIO
import logging

engine = None
db_filename = "Satellite_data"
satellite_lookup = {}
ts = load.timescale()

logger = logging.getLogger(__name__)
logging.basicConfig(filename="log.txt", format='%(asctime)s - %(levelname)s:%(message)s', level=logging.INFO)

def create_database(testing: bool = False):
    """
    This function gets called on startup to create the database and Satellite table if they don't exist
    :param testing: a bool to flat weather an in memory database should be used for testing purposes, or a file based
    database. the default value of testing is False.
    """
    logger.info("building database")
    global engine, db_filename
    if testing:
        logger.info("Using in-memory SQLite database (testing mode)")
        engine = create_engine("sqlite:///:memory:",
                               echo=False,
                               connect_args={"check_same_thread": False},
                               poolclass=StaticPool)
    else:
        logger.info(f"Using file-based SQLite database: {db_filename}")
        engine = create_engine(f"sqlite:///{db_filename}", echo=False)

    Base.metadata.create_all(bind=engine)


def save(data, set_progress=None):
    """
    Takes TLE data from a file or web request and coverts it to EarthSatellite objects so that the name, satnum and
    epoch can be extracted. Then these values, the raw TLE data, and a timestamp are saved to the database.
    :param data: TLE data from a file or web request
    :param set_progress: Tracks the progress made saving the satellite list
    :return: count: an int enumerating the number of records saved
    """
    logger.info("saving data")
    # if this function is running as a background task it won't be able to access the engine created in the
    # create_database function, so a new one will need created
    global engine, db_filename
    if engine is None:
        engine = create_engine(f"sqlite:///{db_filename}", echo=False)

    session = sessionmaker(bind=engine)
    count = 0
    with session.begin() as session:
        # print("data: ",data)
        f = BytesIO(data)

        satellites = list(parse_tle_file_modified(f))
        count = len(satellites)
        # print("satellites: ", satellites)

        if count == 0:
            if set_progress:
                set_progress((0, 1))
            return 0

        for i, (name, line1, line2) in enumerate(satellites):
        # for name, line1, line2 in satellites:
            # print("name: ", name)
            # print("line1: ", line1)
            # print("line2: ", line2)
            sat_obj = EarthSatellite(line1, line2, name, ts)

            # print("sat_obj: ", sat_obj)


            satellite = Satellite(
                OBJECT_ID=sat_obj.model.satnum,
                OBJECT_NAME=sat_obj.name,
                EPOCH=sat_obj.epoch.utc_strftime("%Y-%m-%dT%H:%M:%SZ"),
                line1=line1.rstrip(),
                line2=line2.rstrip(),
                updated=datetime.now(),
                )
            session.merge(satellite)


        if set_progress:
            set_progress((i + 1, count))
        logger.info(f"{count} satellites saved to database")
        session.commit()

    return count


def get_satellite_list():
    """
    loads all the records from the database, converting them in to EarthSatellite objects. Also generates a lookup with
    all satellite objects indexed by their satnum
    :return: satellites: a list of EarthSatellite objects
    """
    global satellite_lookup
    logger.info("retrieving satellite list")
    session = sessionmaker(bind=engine)
    satellites = []
    with session.begin() as session:
        for sat in session.query(Satellite).all():
            sat_object = EarthSatellite(sat.line1, sat.line2, sat.OBJECT_NAME, ts)
            satellites.append(sat_object)

        # print('Loaded', len(satellites), 'satellites')
        # print(satellites)
        satellite_lookup = {sat.model.satnum: sat for sat in satellites}
        # print("Lookup keys (first 10):", list(satellite_lookup.keys())[:10])
        return satellites

def get_satellite_lookup():
    """
    returns the satellite lookup dictionary
    :return:
    """
    return satellite_lookup


def parse_tle_file_modified(lines, skip_names=False):
    """
    This is a modified version of the skyfield.iokit.parse_tle_file function that yields a list containing the tls lines
    in string form, rather than a list of satellite objects. This change was made so that the tle data could be stored
    in the database for export into a file
    :param lines: a list of lines from the file or web request
    :param skip_names: a bool representing if the function should use a 3 line format that includes names, or just a 2
    line format that omits them
    :return: the name of the satellite and the two line making up the TLE data
    """

    logger.info("parsing tle data")
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
            # print("name: ", name)
            # print("line1: ", line1)
            # print("line2: ", line2)
            yield name, line1, line2

            b0 = b1 = b''  # don't accidentally use line 2 as next sat's name
        else:
            b0 = b1
            b1 = b2

def get_satellite_data(id_list=None):
    """
    Retrieves the raw TLE data from the database for export into a file

    :param id_list: a list of satellite satnums. If this list is supplied, ony the data of satellites in this list is
    retrieved, otherwise all satellites are retrieved.
    :return: satellite_data: a list of tuples containing the satellites name, TLE line 1 and TLE line 2
    """
    satellite_data = []
    logger.info("retrieving tle data")
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


def delete_all_satellites():
    """
    Deletes all records from the database
    """
    logger.info("deleting all satellites")
    session = sessionmaker(bind=engine)
    with session.begin() as session:
        session.query(Satellite).delete()
        session.commit()

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

def build_tables(db_filename, testing: bool = False):
    if testing:
        print("Using in-memory SQLite database (testing mode)")
        engine = create_engine("sqlite:///:memory:", echo=False)
    else:
        print(f"Using file-based SQLite database: {db_filename}")
        engine = create_engine(f"sqlite:///{db_filename}", echo=False)

    sessionLocal = sessionmaker(bind=engine)
    return engine, sessionLocal
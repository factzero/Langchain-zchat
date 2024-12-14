from zchat.server.db.base import Base, engine


def create_tables():
    Base.metadata.create_all(bind=engine)
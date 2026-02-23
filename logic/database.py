from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from logic.models import Base

class Database:
    def __init__(self, db_url='sqlite:///ems_database.db'):
        
        self.engine = create_engine(db_url)
        self._session_factory = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    @contextmanager
    def get_session(self):
        """Context manager for database sessions. Ensures proper handling of transactions and session closure."""

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

db_obj = Database()
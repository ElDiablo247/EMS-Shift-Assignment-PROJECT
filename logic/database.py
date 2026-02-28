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
        """
        Context manager that handles the full lifecycle of a database session.
        It automatically commits the transaction if the code block succeeds, rolls back if an exception occurs,
        and ensures the session is always closed. This is much easier and safer than the alternative of manually 
        writing try/except/finally blocks for commit, rollback, and close in every single database operation.
        """

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
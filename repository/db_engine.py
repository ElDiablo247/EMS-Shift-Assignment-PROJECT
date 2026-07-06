from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from repository.models import Base
from dotenv import load_dotenv
import os

load_dotenv()

class DatabaseEngine:
    def __init__(self):

        db_url = os.getenv("DATABASE_URL")
        self.engine = create_engine(db_url, pool_pre_ping=True)
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


db_obj = DatabaseEngine()
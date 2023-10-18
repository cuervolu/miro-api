from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError, IntegrityError

from app.core.config import settings
from app.core.logger import logger
from app.db import base


class Database:
    """
    Singleton class for managing database connections and operations.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
            cls._instance.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls._instance.engine)
        return cls._instance

    def connect(self):
        """
        Connect to the database.
        Returns:
            Session: A database session.
        """
        try:
            return self.SessionLocal()
        except OperationalError as e:
            logger.error(f'Operational Error connecting to the database: {e}')
        except IntegrityError as e:
            logger.error(f'Integrity Error connecting to the database: {e}')
        except Exception as e:
            logger.error(f'Error connecting to the database: {e}')

    def create_database(self):
        """
        Create the database tables for all defined models. Call this method to set up the database schema.
        """
        BaseModel.metadata.create_all(self._instance.engine)
        logger.info('Database tables created.')

    def close_connection(self):
        """
        Close the database connection and dispose of the engine.
        """
        self._instance.SessionLocal.close_all()
        self._instance.engine.dispose()
        logger.info('Database connection closed.')


db = Database()

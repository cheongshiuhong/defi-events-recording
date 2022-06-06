# Standard libraries
import os

# 3rd party libraries
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Code
from src.lib.patterns import Singleton


class MongoDBClient(metaclass=Singleton):
    """
    Makes the underlying client a singleton,
    and proxies the calls to the underlying client.
    """

    __db: AsyncIOMotorDatabase

    def __init__(self):
        self.__db = self.__get_db()

    def __getattr__(self, name: str):
        return getattr(self.__db, name)

    def __getitem__(self, name: str):
        return self.__db[name]

    @staticmethod
    def __get_db() -> AsyncIOMotorDatabase:
        """
        Gets the database client.

        Raises:
            ValueError: If the environment variables are not provided.

        Returns:
            The instance of the client
        """
        host = os.environ.get("DB_HOST")
        port = os.environ.get("DB_PORT")
        database = os.environ.get("DB_DATABASE")
        user = os.environ.get("DB_USER")
        password = os.environ.get("DB_PASSWORD")

        if not all([host, port, database, user, password]):
            raise ValueError(
                "Environment variables for the database is incomplete. "
                'Needs "DB_HOST", "DB_PORT", "DB_DATABASE", '
                '"DB_USER", and "DB_PASSWORD"'
            )

        uri = f"mongodb://{user}:{password}@{host}:{port}"
        return AsyncIOMotorClient(uri)[database]

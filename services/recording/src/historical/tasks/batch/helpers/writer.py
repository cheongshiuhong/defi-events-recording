# Standard libraries
import asyncio

# 3rd party libraries
from motor.motor_asyncio import AsyncIOMotorClient

# Code
from src.lib.logger import RecordingLogger
from .types import ProcessedLog


class BatchWriter:
    """
    Writer for writing the processed data batches into the database.
    """

    __logger: RecordingLogger
    __host: str
    __port: str
    __database_name: str
    __user: str
    __password: str

    def __init__(
        self,
        logger: RecordingLogger,
        host: str,
        port: str,
        database_name: str,
        user: str,
        password: str,
    ):
        self.__logger = logger
        self.__host = host
        self.__port = port
        self.__database_name = database_name
        self.__user = user
        self.__password = password

    async def start_writing(
        self, input_queue: asyncio.Queue[list[ProcessedLog]], category: str
    ) -> None:
        """
        Reads from the input queue asynchronously and writing them into the database.

        Args:
            input_queue: The queue to read from.
            category: The category to record the batch into.
        """
        self.__logger.info("Writer starting...")

        db_uri = (
            f"mongodb://{self.__user}:{self.__password}@{self.__host}:{self.__port}"
        )
        client = AsyncIOMotorClient(db_uri)
        collection = client[self.__database_name][category]

        while True:
            processed_logs = await input_queue.get()

            # End if empty list
            if not processed_logs:
                return

            self.__logger.info(f"Writer got {len(processed_logs)} processed events...")

            await collection.insert_many(processed_logs)

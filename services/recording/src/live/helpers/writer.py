# Standard libraries
from typing import Awaitable
import asyncio

# 3rd party libraries
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Code
from src.lib.logger import RecordingLogger
from .types import ProcessorOutput


class StreamWriter:
    """
    Writer for writing the processed data into the database.
    """

    __logger: RecordingLogger
    __client: AsyncIOMotorClient
    __db: AsyncIOMotorDatabase
    __categories: dict[int, str]

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
        self.__client = AsyncIOMotorClient(f"mongodb://{user}:{password}@{host}:{port}")
        self.__db = self.__client[database_name]
        self.__categories = dict()

    def register_category(self, subscription_id: int, category: str) -> None:
        """
        Registers a processor for a given internal subscription id

        Args:
            subscription_id: The subscription id to use the processor for.
            category: The category in the database of the subscription to write into.
        """
        self.__categories[subscription_id] = category

    async def write_forever(
        self, input_queue: asyncio.Queue[ProcessorOutput]
    ) -> Awaitable[None]:
        """
        Reads from the input queue asynchronously and writing them into the database.

        Args:
            input_queue: The queue to read from.
        """
        while True:
            processor_output = await input_queue.get()

            category = self.__categories[processor_output["subscription_id"]]
            await self.__db[category].insert_one(processor_output["data"])

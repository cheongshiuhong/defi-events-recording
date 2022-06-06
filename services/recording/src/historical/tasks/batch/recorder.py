# Standard libraries
import os
import asyncio

# Code
from src.lib.logger import RecordingLogger
from src.events import EventsResolver
from .helpers import EventLog, ProcessedLog, BatchLoader, BatchProcessor, BatchWriter
from .types import BatchConfig, GasPricingConfig

# Constants
# We choose 30 blocks per batch to be absolutely safe
# that we will not miss any events since EtherScan
# does not allow pagination.
BLOCKS_PER_BATCH = 30


class BatchRecorder:
    """
    Main class that composes the loader, processor, and writer
    to record events in batches from the chain indexer into the database.
    """

    __logger: RecordingLogger
    __loader: BatchLoader
    __processor: BatchProcessor
    __writer: BatchWriter

    def __init__(self, logger: RecordingLogger, config: BatchConfig):
        self.__logger = logger
        self.__loader = self.__get_loader(logger)
        self.__processor = self.__get_processor(logger, config["gas_pricing"])
        self.__writer = self.__get_writer(logger)
        self.__rpc_uri = self.__get_rpc_uri()

    def record_synchronously(
        self, contract_address: str, event_id: str, from_block: int, to_block: int
    ) -> None:
        """
        Starts recording synchronously.

        Args:
            contract_address: The contract address to fetch transactions for.
            event_id: The event_id to lookup.
            from_block: The block to record from.
            to_block: The block to record to.
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self.record_asynchronously(contract_address, event_id, from_block, to_block)
        )

    async def record_asynchronously(
        self, contract_address: str, event_id: str, from_block: int, to_block: int
    ) -> None:
        """
        Starts recording asynchronously.

        Args:
            contract_address: The contract address to fetch transactions for.
            event_id: The event_id to lookup.
            from_block: The block to record from.
            to_block: The block to record to.
        """
        event_topic = EventsResolver.get_topic(event_id)
        event_category = EventsResolver.get_category(event_id)
        event_handler = EventsResolver.get_handler(event_id, contract_address)
        await event_handler.resolve_context_asynchronously(self.__rpc_uri)

        processor_queue = asyncio.Queue[list[EventLog]]()
        writer_queue = asyncio.Queue[list[ProcessedLog]]()

        await asyncio.gather(
            self.__loader.start_loading(
                processor_queue,
                contract_address,
                event_topic,
                from_block,
                to_block,
                BLOCKS_PER_BATCH,
            ),
            self.__processor.start_processing(
                processor_queue, writer_queue, event_id, event_handler
            ),
            self.__writer.start_writing(writer_queue, event_category),
        )

    # ------------------------
    # Initialization helpers
    # ------------------------

    @staticmethod
    def __get_loader(logger: RecordingLogger) -> BatchLoader:
        """
        Initializes the batch loader.

        Args:
            logger: The logger instance to pass into the loader.

        Raises:
            ValueError: When the environment variable is not provided.

        Returns:
            The batch loader instance.
        """
        etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")
        if etherscan_api_key is None:
            raise ValueError('Environment variable "ETHERSCAN_API_KEY" not found.')

        return BatchLoader(logger, etherscan_api_key)

    @staticmethod
    def __get_processor(
        logger: RecordingLogger, pricing_config: GasPricingConfig
    ) -> BatchProcessor:
        """
        Initializes the batch processor.

        Args:
            logger: The logger instance to pass into the processor.
            pricing_config: The pricing config dictionary.

        Returns:
            The batch processor instance.
        """
        return BatchProcessor(
            logger,
            pricing_config["gas_currency"],
            pricing_config["quote_currency"],
        )

    @staticmethod
    def __get_writer(logger: RecordingLogger) -> BatchWriter:
        """
        Initializes the batch writer.

        Args:
            logger: The logger instance to pass into the writer.

        Raises:
            ValueError: When any of the required environment variables is not provided.

        Returns:
            The batch writer instance.
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

        return BatchWriter(logger, host, port, database, user, password)

    @staticmethod
    def __get_rpc_uri() -> str:
        """
        Retrieves the node provider rpc uri.

        Raises:
            ValueError: When the environment variable is not provided.

        Returns:
            The node provider rpc uri.
        """
        rpc_uri = os.environ.get("NODE_PROVIDER_RPC_URI")
        if rpc_uri is None:
            raise ValueError('Environment variable "NODE_PROVIDER_RPC_URI" not found.')

        return rpc_uri

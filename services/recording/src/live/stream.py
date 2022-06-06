# Standard libraries
import asyncio
import os

# Code
from src.lib.logger import RecordingLogger
from src.events import EventsResolver
from .helpers import (
    ListenerOutput,
    ProcessorOutput,
    StreamListener,
    StreamProcessor,
    StreamWriter,
)
from .types import (
    StreamConfig,
    GasPricingConfig,
    SubscriptionsConfig,
)


class Stream:
    """
    Main class that composes the listener, processor, and writer
    to stream from the chain into the database.
    """

    __logger: RecordingLogger
    __listener: StreamListener
    __processor: StreamProcessor
    __writer: StreamWriter

    def __init__(self, logger: RecordingLogger, config: StreamConfig):
        self.__logger = logger
        self.__listener = self.__get_listener(logger)
        self.__processor = self.__get_processor(logger, config["gas_pricing"])
        self.__writer = self.__get_writer(logger)
        self.__initialize_subscriptions(
            self.__listener, self.__processor, self.__writer, config["subscriptions"]
        )

    def start_synchronously(self) -> None:
        """
        Starts the stream synchronously.
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.start_asynchronously())

    async def start_asynchronously(self) -> None:
        """
        Starts the stream asynchronously.
        """
        self.__logger.info("Starting asynchronously...")
        processor_queue = asyncio.Queue[ListenerOutput]()
        writer_queue = asyncio.Queue[ProcessorOutput]()

        self.__logger.info("Starting listener, processor, and writer...")
        await asyncio.gather(
            self.__listener.listen_forever(processor_queue),
            self.__processor.process_forever(processor_queue, writer_queue),
            self.__writer.write_forever(writer_queue),
        )

    # ------------------------
    # Initialization helpers
    # ------------------------

    @staticmethod
    def __get_listener(logger: RecordingLogger) -> StreamListener:
        """
        Initializes the stream listener.

        Args:
            logger: The logger instance to pass into the listener.

        Raises:
            ValueError: When the environment variable is not provided.

        Returns:
            The stream listener instance.
        """
        node_provider_wss_uri = os.environ.get("NODE_PROVIDER_WSS_URI")
        if node_provider_wss_uri is None:
            raise ValueError('Environment variable "NODE_PROVIDER_WSS_URI" not found.')

        return StreamListener(logger, node_provider_wss_uri)

    @staticmethod
    def __get_processor(
        logger: RecordingLogger, pricing_config: GasPricingConfig
    ) -> StreamProcessor:
        """
        Initializes the stream processor.

        Args:
            logger: The logger instance to pass into the processor.

        Raises:
            ValueError: When the environment variable is not provided.
            pricing_config: The pricing config dictionary.

        Returns:
            The stream processor instance.
        """
        node_provider_rpc_uri = os.environ.get("NODE_PROVIDER_RPC_URI")
        if node_provider_rpc_uri is None:
            raise ValueError('Environment variable "NODE_PROVIDER_RPC_URI" not found.')

        return StreamProcessor(
            logger,
            node_provider_rpc_uri,
            pricing_config["gas_currency"],
            pricing_config["quote_currency"],
        )

    @staticmethod
    def __get_writer(logger: RecordingLogger) -> StreamWriter:
        """
        Initializes the stream writer.

        Args:
            logger: The logger instance to pass into the writer.

        Raises:
            ValueError: When any of the required environment variables is not provided.

        Returns:
            The stream writer instance.
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

        return StreamWriter(logger, host, port, database, user, password)

    @staticmethod
    def __initialize_subscriptions(
        listener: StreamListener,
        processor: StreamProcessor,
        writer: StreamWriter,
        subscriptions_config: SubscriptionsConfig,
    ) -> None:
        """
        Args:
            listener: The stream listener instance.
            processor: The stream processor instance.
            writer: The stream writer instance.
            subscriptions_config: The subscriptions config dictionary.
        """
        # Environment guaranteed to exist by now
        node_provider_rpc_uri = os.environ["NODE_PROVIDER_RPC_URI"]

        for subscription_config in subscriptions_config:
            event_id = subscription_config["event_id"]
            contract_address = subscription_config["contract_address"]

            # Resolve the event's topic and processor
            event_category = EventsResolver.get_category(event_id)
            event_topic = EventsResolver.get_topic(event_id)
            event_handler = EventsResolver.get_handler(event_id, contract_address)

            # Add the event to be subscribed to
            subscription_id = listener.add_event_subscription(
                contract_address, event_topic
            )

            # Register the event_id with the processor
            processor.register_event_id(subscription_id, event_id)

            # Also register the handler if it exists
            if event_handler is not None:
                event_handler.resolve_context_synchronously(node_provider_rpc_uri)
                processor.register_event_handler(subscription_id, event_handler)

            # Add the event's category to the writer
            writer.register_category(subscription_id, event_category)

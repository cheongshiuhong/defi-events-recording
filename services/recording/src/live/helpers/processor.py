# Standard libraries
import asyncio
import json

# 3rd party libraries
from async_lru import alru_cache
import aiohttp

# Code
from src.lib.logger import RecordingLogger
from src.events import BaseEventHandler
from .types import (
    ListenerOutput,
    TransactionReceipt,
    ProcessorOutputData,
    ProcessorOutput,
)


class StreamProcessor:
    """
    Processor for processing the events fed from the listener,
    with optional processing for even type of event.
    """

    __logger: RecordingLogger
    __rpc_uri: str
    __gas_currency: str
    __quote_currency: str
    __event_ids: dict[int, str]
    __event_handlers: dict[int, BaseEventHandler]

    def __init__(
        self,
        logger: RecordingLogger,
        rpc_uri: str,
        gas_currency: str,
        quote_currency: str,
    ):
        self.__logger = logger
        self.__rpc_uri = rpc_uri
        self.__gas_currency = gas_currency
        self.__quote_currency = quote_currency
        self.__event_ids = dict()
        self.__event_handlers = dict()

    def register_event_id(self, subscription_id: int, event_id: str) -> None:
        """
        Registers the event id for a given internal subscription id.

        Args:
            subscription_id: The subscription id to use the handler for.
            event_id: The id to tag the event as part of processing the it.
        """
        self.__event_ids[subscription_id] = event_id

    def register_event_handler(
        self, subscription_id: int, event_handler: BaseEventHandler
    ) -> None:
        """
        Registers an event handler for a given internal subscription id.

        Args:
            subscription_id: The subscription id to use the handler for.
            event_handler: The handler to handle the raw data into meaningful data.
        """
        self.__event_handlers[subscription_id] = event_handler

    async def process_forever(
        self,
        input_queue: asyncio.Queue[ListenerOutput],
        output_queue: asyncio.Queue[ProcessorOutput],
    ) -> None:
        """
        Reads from the input queue asynchronously, processing each event and
        calling the corresponding handlers if they exist.

        Args:
            input_queue: The queue to read from.
            output_queue: The queue to put into after processing.
        """
        self.__logger.info("StreamProcessor processing forever...")
        async with aiohttp.ClientSession() as session:

            while True:
                listener_output = await input_queue.get()
                subscription_id = listener_output["subscription_id"]
                event_log = listener_output["event_log"]

                # Fetch the block timestamp
                block_timestamp_task = asyncio.create_task(
                    self.__fetch_block_timestamp(
                        session, self.__rpc_uri, event_log["blockHash"]
                    )
                )

                # Fetch the transaction receipt
                transaction_receipt_task = asyncio.create_task(
                    self.__fetch_transaction_receipt(
                        session, self.__rpc_uri, event_log["transactionHash"]
                    )
                )

                # Wait for the block timestamp before fetching the gas currency price
                block_timestamp = await block_timestamp_task

                # Fetch the gas currency price
                gas_currency_price_task = asyncio.create_task(
                    self.__fetch_gas_currency_price(
                        session,
                        self.__gas_currency,
                        self.__quote_currency,
                        block_timestamp,
                    )
                )

                transaction_receipt, (int_price, decimals,) = await asyncio.gather(
                    transaction_receipt_task, gas_currency_price_task
                )

                # Decode the gas prices and compute the gas price as quoted
                gas_used = int(transaction_receipt["gasUsed"], 16)
                gas_price_wei = int(transaction_receipt["effectiveGasPrice"], 16)
                gas_price_quoted_value = (
                    int_price * gas_used * gas_price_wei // 10**decimals
                )

                # Call the specific handler if it exist
                handler = self.__event_handlers.get(subscription_id, None)
                handled_data = (
                    handler.handle(event_log["data"], event_log["topics"])
                    if handler is not None
                    else {}
                )

                await output_queue.put(
                    ProcessorOutput(
                        subscription_id=subscription_id,
                        data=ProcessorOutputData(
                            event_id=self.__event_ids[subscription_id],
                            transaction_hash=event_log["transactionHash"],
                            block_hash=event_log["blockHash"],
                            block_number=int(event_log["blockNumber"], 16),
                            timestamp=block_timestamp,
                            sender=transaction_receipt["from"],
                            recipient=transaction_receipt["to"],
                            gas_used=str(gas_used),
                            gas_price_wei=str(gas_price_wei),
                            gas_price_quote={
                                "currency": self.__quote_currency,
                                "value": str(gas_price_quoted_value),
                            },
                            address=event_log["address"],
                            topics=event_log["topics"],
                            raw_data=event_log["data"],
                            data=handled_data,
                        ),
                    )
                )

    @staticmethod
    @alru_cache(maxsize=16)
    async def __fetch_block_timestamp(
        session: aiohttp.ClientSession, rpc_uri: str, block_hash: str
    ) -> int:
        """
        Fetches a block to retrieve its timestamp from the node provider.
        LRU-cached to reduce the number of calls made.

        Args:
            session: The async http session to use to make the request.
            rpc_uri: The eth node provider's rpc uri.
            block_hash: The hash of the block to fetch the timestamp for.

        Returns:
            The awaitable integer timestamp in seconds from the response.
        """
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_getBlockByHash",
            "params": [block_hash, False],
        }

        while True:
            response = await session.post(rpc_uri, data=json.dumps(body))

            # Parse the json and return the decoded hexadecimal timestamp
            json_response = await response.json()

            if json_response["result"] is None:
                await asyncio.sleep(1)
                continue

            return int(json_response["result"]["timestamp"], 16)

    @staticmethod
    @alru_cache(maxsize=16)
    async def __fetch_transaction_receipt(
        session: aiohttp.ClientSession, rpc_uri: str, transaction_hash: str
    ) -> TransactionReceipt:
        """
        Fetches a transaction receipt from the node provider.
        LRU-cached to reduce the number of calls made.

        Args:
            session: The async http session to use to make the request.
            rpc_uri: The node provider's rpc uri.
            transaction_hash: The hash of the transaction to fetch.

        Returns:
            The transaction receipt dictionary
        """
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_getTransactionReceipt",
            "params": [transaction_hash],
        }

        while True:
            response = await session.post(rpc_uri, data=json.dumps(body))
            json_response = await response.json()

            if json_response["result"] is None:
                await asyncio.sleep(1)
                continue

            result: TransactionReceipt = json_response["result"]
            return result

    @staticmethod
    @alru_cache(maxsize=16)
    async def __fetch_gas_currency_price(
        session: aiohttp.ClientSession,
        gas_currency: str,
        quote_currency: str,
        timestamp: int,
    ) -> tuple[int, int]:
        """
        Fetches the price from a centralized exchange.
        LRU-cached to reduce the number of calls made.

        Args:
            session: The asynchronous http session to use to make the request.
            timestamp: The timestamp in seconds at which to fetch the price.

        Returns:
            The tuple of the kline's integer close price and decimal scaling.
        """
        # Fetch the minute kline where the timestamp was in
        uri = (
            "https://api.binance.com/api/v3/klines"
            f"?symbol={gas_currency}{quote_currency}&interval=1m"
            f"&endTime={timestamp * 1000}&limit=1"
        )

        response = await session.get(uri)
        json_response = await response.json()
        kline = json_response[0]

        # We shall simply use the close price
        string_price = kline[4]
        decimals: int = len(string_price) - string_price.find(".") - 1
        integer_price = int(string_price.replace(".", ""))

        return integer_price, decimals

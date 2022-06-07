# Standard libraries
from typing import Optional
import asyncio

# 3rd party libraries
import aiohttp

# Code
from src.lib.logger import RecordingLogger
from src.events import BaseEventHandler
from .types import EventLog, ProcessedLog


class BatchProcessor:
    """
    Processor to process each batch of event logs.
    """

    __logger: RecordingLogger
    __gas_currency: str
    __quote_currency: str

    def __init__(
        self,
        logger: RecordingLogger,
        gas_currency: str,
        quote_currency: str,
    ):
        self.__logger = logger
        self.__gas_currency = gas_currency
        self.__quote_currency = quote_currency

    async def start_processing(
        self,
        input_queue: asyncio.Queue[list[EventLog]],
        output_queue: asyncio.Queue[list[ProcessedLog]],
        event_id: str,
        handler: Optional[BaseEventHandler],
    ) -> None:
        """
        Processes the event logs in batches and puts the results into the output queue.

        Args:
            input_queue: The input queue to read from.
            output_queue: The output queue to put the results into.
            event_id: The event_id to tag the outputs.
            handler: The event handler to process the raw data.
        """
        self.__logger.info("Processor starting...")

        async with aiohttp.ClientSession() as session:
            while True:
                event_logs = await input_queue.get()

                # End if empty list
                if not event_logs:
                    await output_queue.put([])
                    return

                self.__logger.info(f"Processing {len(event_logs)} event logs...")

                # Iterate and retrive unique timestamps at which
                # we need to fetch to fetch prices at,
                # as well as the max and min.
                unique_timestamps = set[int]()
                max_timestamp = 0
                min_timestamp = 1_000_000_000_000
                for event_log in event_logs:
                    timestamp = int(event_log["timeStamp"], 16)
                    unique_timestamps.add(timestamp)
                    max_timestamp = max(max_timestamp, timestamp)
                    min_timestamp = min(min_timestamp, timestamp)

                # Fetch the range of timestamps
                gas_currency_prices = await self.__fetch_gas_currency_price(
                    session,
                    self.__gas_currency,
                    self.__quote_currency,
                    min_timestamp,
                    max_timestamp,
                )

                # Tag the price into each event
                price_index = 0
                batch_processor_output: list[ProcessedLog] = []
                for event_log in event_logs:
                    # Increment the price index until we see
                    # the one with close_time >= event_time
                    # We can do this since both are sorted
                    # and we are guaranteed to have the range covered
                    event_timestamp = int(event_log["timeStamp"], 16)
                    while gas_currency_prices[price_index][0] < event_timestamp:
                        price_index += 1

                    # Retrieve the price based on the timestamp
                    int_price, decimals = gas_currency_prices[price_index][1:]

                    # Decode the gas prices and compute the gas price as quoted
                    gas_used = int(event_log["gasUsed"], 16)
                    gas_price_wei = int(event_log["gasPrice"], 16)
                    gas_price_quoted_value = (
                        int_price * gas_used * gas_price_wei // 10**decimals
                    )

                    # Call the specific handler if it exist
                    handled_data = (
                        handler.handle(event_log["data"], event_log["topics"])
                        if handler is not None
                        else {}
                    )

                    # Batch the result into a list
                    batch_processor_output.append(
                        ProcessedLog(
                            event_id=event_id,
                            transaction_hash=event_log["transactionHash"],
                            log_index=int(event_log["logIndex"], 16),
                            block_number=int(event_log["blockNumber"], 16),
                            timestamp=int(event_log["timeStamp"], 16),
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

                # Put the processed batch into the queue
                await output_queue.put(batch_processor_output)

    @staticmethod
    async def __fetch_gas_currency_price(
        session: aiohttp.ClientSession,
        gas_currency: str,
        quote_currency: str,
        start_timestamp: int,
        end_timestamp: int,
    ) -> list[tuple[int, int, int]]:
        """
        Fetches the price from a centralized exchange and
        matches the input timestamps with a correspnding price/decimals tuple.

        Args:
            session: The asynchronous http session to use to make the request.
            gas_currency: The gas currency to get the price of.
            quote_currency: The quote currency for the price to be quoted in.
            start_timestamp: The earliest timestamp to fetch.
            end_timestamp: The latest timestamp to fetch.

        Returns:
            The list of tuples of the kline's close time,
            integer close price and decimal scaling.
        """
        # Fetch the minute kline where the timestamp was in
        uri = (
            "https://api.binance.com/api/v3/klines"
            f"?symbol={gas_currency}{quote_currency}&interval=1m"
            f"&startTime={(start_timestamp - 60) * 1000}&endTime={end_timestamp * 1000}"
        )

        response = await session.get(uri)
        json_response = await response.json()
        klines = json_response

        # Parse the close times and prices
        close_times_and_prices = []
        for kline in klines:
            string_price = kline[4]
            decimals: int = len(string_price) - string_price.find(".") - 1
            integer_price = int(string_price.replace(".", ""))
            close_times_and_prices.append((kline[6], integer_price, decimals))

        return close_times_and_prices

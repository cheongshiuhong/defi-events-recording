# Standard libraries
import asyncio

# 3rd party libraries
import aiohttp

# Code
from src.lib.logger import RecordingLogger
from .types import EventLog


class BatchLoader:
    """
    Batch loader to load the event logs in batches.
    """

    __logger: RecordingLogger
    __api_key: str

    def __init__(self, logger: RecordingLogger, api_key: str):
        self.__logger = logger
        self.__api_key = api_key

    async def start_loading(
        self,
        output_queue: asyncio.Queue[list[EventLog]],
        contract_address: str,
        event_topic: str,
        from_block: int,
        to_block: int,
        blocks_per_batch: int,
    ) -> None:
        """
        Loads data from EtherScan and puts the results into the output queue.

        Args:
            output_queue: The output queue to put the results into.
            contract_address: The contract address to fetch events for.
            event_topic: The hashed event topic identifier.
            from_block: The first block the fetch for.
            to_block: The last block to fetch for.
            blocks_per_batch: The number of blocks to fetch per request.
        """
        self.__logger.info("Loader starting...")

        async with aiohttp.ClientSession() as session:
            for i in range(from_block, to_block + 1, blocks_per_batch):

                self.__logger.info(
                    f"Fetching event logs from block {i} to {i + blocks_per_batch}"
                )

                uri: str = (
                    "https://api.etherscan.io/api?module=logs&action=getLogs"
                    f"&apikey={self.__api_key}&address={contract_address}"
                    f"&topic0={event_topic}"
                    f"&fromBlock={i}&toBlock={i + blocks_per_batch}"
                )

                response = await session.get(uri)
                data = await response.json()
                result = data["result"]

                # Skip if empty
                if not result:
                    continue

                # Put the non empty results list into the queue
                await output_queue.put(result)

                # Sleep half a second between requests to prevent rate limit
                # We can remove this if we have $$$ to upgrade our plan lel
                await asyncio.sleep(0.5)

        # Put an empty list to indicate the end
        await output_queue.put([])

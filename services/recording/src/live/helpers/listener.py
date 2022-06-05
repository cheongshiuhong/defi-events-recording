# Standard libraries
import asyncio
import json

# 3rd party libraries
import websockets

# Code
from src.lib.logger import RecordingLogger
from .types import EventLog, ListenerOutput


class StreamListener:
    """
    Listener for listening to events from a contract on the blockchain.
    """

    __logger: RecordingLogger
    __wss_uri: str
    __subscription_messages: list[str]
    __subscription_ids: dict[str, int]

    def __init__(self, logger: RecordingLogger, wss_uri: str):
        self.__logger = logger
        self.__wss_uri = wss_uri
        self.__subscription_messages = []
        self.__subscription_ids = {}

    def add_event_subscription(self, contract_address: str, topic: str) -> int:
        """
        Adds an event to subscribe to by formatting it into the eth-rpc message.

        Args:
            contract_address: The contract to listen to.
            topic: The event identifier to listen for.

        Returns:
            The subscription id for identification purposes.
        """
        self.__subscription_messages.append(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": [
                        "logs",
                        {"address": contract_address, "topics": [topic]},
                    ],
                }
            )
        )
        return len(self.__subscription_messages) - 1

    async def listen_forever(self, output_queue: asyncio.Queue[ListenerOutput]) -> None:
        """
        Listens to the blockchain asynchronously,
        feeding each event into the output queue.

        Args:
            output_queue: The queue to put the events into.
        """
        self.__logger.info("StreamListener listening forever...")

        while True:
            # Always try to reconnect if connection closed
            async with websockets.connect(
                self.__wss_uri, ping_interval=30, ping_timeout=120
            ) as ws:
                self.__logger.info("Setting up subscriptions...")

                # Send the subscription messages
                for i, subscription_message in enumerate(self.__subscription_messages):
                    # Retrieve subscription ids and track them internally
                    await ws.send(subscription_message)
                    string_message = await ws.recv()
                    json_message = json.loads(string_message)
                    self.__subscription_ids[json_message["result"]] = i

                self.__logger.info("Starting to listen for events...")

                try:
                    # Feed the queue
                    while True:
                        string_message = await ws.recv()
                        json_message = json.loads(string_message)

                        self.__logger.info("Listener received event...")

                        # Parse the internal subscription id
                        eth_sub_id: str = json_message["params"]["subscription"]
                        internal_sub_id = self.__subscription_ids[eth_sub_id]

                        # Tag the subscription id and enqueue into the output queue
                        event_log: EventLog = json_message["params"]["result"]
                        await output_queue.put(
                            ListenerOutput(
                                subscription_id=internal_sub_id,
                                event_log=event_log,
                            )
                        )

                except websockets.exceptions.ConnectionClosedError:
                    await asyncio.sleep(0.5)
                    self.__logger.info("Connection closed.. Reconnecting...")

                except Exception as e:
                    self.__logger.error(
                        f"Unhandled exception: {str(e)}. Listening stopped."
                    )
                    raise e

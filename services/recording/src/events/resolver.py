# Standard libraries
from typing import TypedDict, Optional

# Code
from .constants import UNISWAP_LP_SWAP_EVENT_TOPIC
from .handlers.base import BaseEventHandler
from .handlers.uniswap.v3_pool.swap import UniswapV3PoolSwapEventHandler


class EventMetadata(TypedDict):
    """
    Each event must have their topicsbut need not have a processor
    if processing logic is not required for the event.
    """

    category: str
    topic: str
    handler_class: Optional[type]


_EVENT_METADATA_MAPPING: dict[str, EventMetadata] = {
    "uniswap-v3-pool-swap": {
        "category": "swaps",
        "topic": UNISWAP_LP_SWAP_EVENT_TOPIC,
        "handler_class": UniswapV3PoolSwapEventHandler,
    }
}


class EventsResolver:
    """
    Static class to resolve event details based on the event id.
    """

    @classmethod
    def get_category(cls, event_id: str) -> str:
        """
        Args:
            event_id: The id of the event to get the category for.

        Returns:
            The category the event belongs to.
        """
        return cls.__get_metadata(event_id)["category"]

    @classmethod
    def get_topic(cls, event_id: str) -> str:
        """
        Args:
            event_id: The id of the event to get the topic for.

        Returns:
            The hashed event identifier topic.
        """
        return cls.__get_metadata(event_id)["topic"]

    @classmethod
    def get_handler(
        cls, event_id: str, contract_address: str
    ) -> Optional[BaseEventHandler]:
        """
        Initializes and returns an event handler instance
        if it exists, based on the input event_id.

        Args:
            event_id: The event id to lookup the processor for.

        Returns:
            The initialized event processor instance.
        """
        handler_class = cls.__get_metadata(event_id).get("handler_class")
        if handler_class is None:
            return None

        return handler_class(contract_address)

    @staticmethod
    def __get_metadata(event_id: str) -> EventMetadata:
        """
        Args:
            event_id: The id of the event to get the metadata for.

        Raises:
            ValueError: If the input event id's metadata is not found.

        Returns:
            The event metadata.
        """
        metadata = _EVENT_METADATA_MAPPING.get(event_id)
        if metadata is None:
            raise ValueError(f'Event ID "{event_id}" is not recognizable.')

        return metadata

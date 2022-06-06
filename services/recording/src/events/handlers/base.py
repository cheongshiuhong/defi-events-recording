# Standard libraries
from abc import ABC, abstractmethod


class BaseEventHandler(ABC):
    """
    Protocol for an event handler
    """

    contract_address: str

    def __init__(self, contract_address: str):
        self.contract_address = contract_address

    def __repr__(self):
        return f"Event handler for contract: {self.contract_address}"

    def __str__(self):
        return f"Event handler for contract: {self.contract_address}"

    @abstractmethod
    def resolve_context_synchronously(self, rpc_uri: str) -> None:
        """
        Resolves contextual information for the handler to modify the handling process.

        Args:
            rpc_uri: The rpc_uri to read from the chain.
            contract_address: The contract's address to send the call to.
        """

    @abstractmethod
    async def resolve_context_asynchronously(self, rpc_uri: str) -> None:
        """
        Resolves contextual information for the handler to modify the handling process.

        Args:
            rpc_uri: The rpc_uri to read from the chain.
            contract_address: The contract's address to send the call to.
        """

    @abstractmethod
    def handle(self, raw_data: str, topics: list[str]) -> dict[str, str]:
        """
        Handles the raw data and topics by decoding them
        into a meaningful data dictionary.

        Args:
            raw_data: The raw encoded data to handle.
            topics: The topics which could hold indexed fields if any.
        """

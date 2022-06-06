# Standard libraries
import asyncio
import json

# 3rd party libraries
from eth_abi import decode_abi, decode_single
from eth_utils import keccak, encode_hex, decode_hex
import aiohttp

# Code
from src.events.handlers.base import BaseEventHandler


class UniswapV3PoolSwapEventHandler(BaseEventHandler):
    """
    Handler for uniswap's lp swap events.
    """

    # Sender and receipient addresses are indexed topics
    EVENT_DECODE_TYPES: list[str] = ["int256", "int256", "uint160", "uint128", "int24"]

    # Function selectors (first 4 bytes after keccak)
    TOKEN_0_SELECTOR = encode_hex(keccak(text="token0()")[:4])
    TOKEN_1_SELECTOR = encode_hex(keccak(text="token1()")[:4])
    DECIMALS_SELECTOR = encode_hex(keccak(text="decimals()")[:4])
    SYMBOL_SELECTOR = encode_hex(keccak(text="symbol()")[:4])

    # Contextual data
    symbol_0 = None
    symbol_1 = None
    decimals_0 = None
    decimals_1 = None
    swap_price_0_scaling_factor = None
    swap_price_1_scaling_factor = None

    def __repr__(self):
        return super().__repr__() + f" ({self.symbol_0}-{self.symbol_1})"

    def __str__(self):
        return super().__str__() + f" ({self.symbol_0}-{self.symbol_1})"

    def resolve_context_synchronously(self, rpc_uri: str) -> None:
        """
        Resolves the requried contextual data.

        Args:
            rpc_uri: The node provider's rpc uri to resolve the context with.
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.resolve_context_asynchronously(rpc_uri))

    async def resolve_context_asynchronously(self, rpc_uri: str) -> None:
        """
        Resolves the required contextual data asynchronously.

        Args:
            rpc_uri: The node provider's rpc uri to resolve the context with.
        """
        async with aiohttp.ClientSession() as session:
            # Resolve the underlying tokens' addresses
            tokens_addresses_result = await asyncio.gather(
                self.__make_eth_call(
                    session, rpc_uri, self.contract_address, self.TOKEN_0_SELECTOR
                ),
                self.__make_eth_call(
                    session, rpc_uri, self.contract_address, self.TOKEN_1_SELECTOR
                ),
            )

            token_0_address = decode_single(
                "address", decode_hex(tokens_addresses_result[0])
            )
            token_1_address = decode_single(
                "address", decode_hex(tokens_addresses_result[1])
            )

            # Resolve the underlying tokens' symbols and decimals
            tokens_details_result = await asyncio.gather(
                self.__make_eth_call(
                    session, rpc_uri, token_0_address, self.SYMBOL_SELECTOR
                ),
                self.__make_eth_call(
                    session, rpc_uri, token_1_address, self.SYMBOL_SELECTOR
                ),
                self.__make_eth_call(
                    session, rpc_uri, token_0_address, self.DECIMALS_SELECTOR
                ),
                self.__make_eth_call(
                    session, rpc_uri, token_1_address, self.DECIMALS_SELECTOR
                ),
            )

            self.symbol_0 = decode_abi(
                ["string"], decode_hex(tokens_details_result[0])
            )[0]
            self.symbol_1 = decode_abi(
                ["string"], decode_hex(tokens_details_result[1])
            )[0]
            self.decimals_0 = decode_single(
                "uint8", decode_hex(tokens_details_result[2])
            )
            self.decimals_1 = decode_single(
                "uint8", decode_hex(tokens_details_result[3])
            )

            swap_price_0_scaling_decimals = 18 + self.decimals_0 - self.decimals_1
            self.swap_price_0_scaling_factor = 10 ** (swap_price_0_scaling_decimals)
            swap_price_1_scaling_decimals = 18 + self.decimals_1 - self.decimals_0
            self.swap_price_1_scaling_factor = 10 ** (swap_price_1_scaling_decimals)

    async def __make_eth_call(
        self, session: aiohttp.ClientSession, rpc_uri: str, to: str, data: str
    ) -> str:
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_call",
            "params": [{"to": to, "data": data}, "latest"],
        }
        response = await (await session.post(rpc_uri, data=json.dumps(body))).json()
        result: str = response["result"]
        return result

    def handle(self, raw_data: str, topics: list[str]) -> dict[str, str]:
        """
        Handles the swap event's raw data and topics and compute the swap price

        Args:
            raw_data: The swap event's raw encoded data to handle.
            topics: The indexed sender and recipient.

        Returns:
            The dictionary of the event's data.
        """
        if self.symbol_0 is None or self.symbol_1 is None:
            return {}

        # Decode the data
        decoded_data = decode_abi(self.EVENT_DECODE_TYPES, decode_hex(raw_data))
        amount_0, amount_1, sqrt_price_x96, liquidity, tick = decoded_data

        # Guard against 0 amounts (division by zero)
        if amount_0 == 0 or amount_1 == 0:
            swap_price_0 = swap_price_1 = 0
        else:
            # Swap price 0 = price of token_0 quoted in token_1
            swap_price_0 = -(self.swap_price_0_scaling_factor * amount_1 // amount_0)

            # Swap price 1 = price of token_1 quoted in token_0
            swap_price_1 = -(self.swap_price_1_scaling_factor * amount_0 // amount_1)

        # Retrieve the indexed topics
        sender = decode_single("address", decode_hex(topics[1]))
        recipient = decode_single("address", decode_hex(topics[2]))

        return {
            "sender": sender,
            "recipient": recipient,
            "symbol_0": self.symbol_0,
            "symbol_1": self.symbol_1,
            "amount_0": str(amount_0),
            "amount_1": str(amount_1),
            "swap_price_0": str(swap_price_0),
            "swap_price_1": str(swap_price_1),
            "sqrt_price_x96": str(sqrt_price_x96),
            "liquidity": str(liquidity),
            "tick": str(tick),
        }

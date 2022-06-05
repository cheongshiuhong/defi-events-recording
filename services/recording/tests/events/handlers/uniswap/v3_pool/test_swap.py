# Standard libraries
import json

# 3rd party libraries
from asynctest import MagicMock, CoroutineMock, patch
import pytest

# Code
from src.events.handlers.uniswap.v3_pool.swap import (
    UniswapV3PoolSwapEventHandler as Cls,
)


def test_initialization_and_magics():
    """
    Simple initialization no-error check
    """
    instance = Cls("0x123456")
    instance.__repr__()
    instance.__str__()


@patch("src.events.handlers.uniswap.v3_pool.swap.asyncio")
def test_resolve_context(asyncio):
    instance = Cls("0x123456")

    instance.resolve_context_asynchronously = MagicMock()
    instance.resolve_context("rpc_uri")

    assert asyncio.run.is_called()
    assert instance.resolve_context_asynchronously.is_called()


@pytest.mark.asyncio
@patch("src.events.handlers.uniswap.v3_pool.swap.decode_hex")
@patch("src.events.handlers.uniswap.v3_pool.swap.decode_abi")
@patch("src.events.handlers.uniswap.v3_pool.swap.decode_single")
@patch("src.events.handlers.uniswap.v3_pool.swap.aiohttp")
async def test_resolve_context_asynchronously(
    aiohttp, decode_single, decode_abi, decode_hex
):
    """
    Test the synchronous call to resolve context
    """
    # Setup the session's return values
    response = MagicMock()
    response.json = CoroutineMock(
        side_effect=[
            {"jsonrpc": "2.0", "id": 1, "result": "0x000"},  # token 0 address
            {"jsonrpc": "2.0", "id": 1, "result": "0x111"},  # token 1 address
            {"jsonrpc": "2.0", "id": 1, "result": "0x00000"},  # token 0 symbol
            {"jsonrpc": "2.0", "id": 1, "result": "0x11111"},  # token 1 symbol
            {"jsonrpc": "2.0", "id": 1, "result": "0x00012"},  # token 0 decimals
            {"jsonrpc": "2.0", "id": 1, "result": "0X00012"},  # token 1 decimals
        ]
    )

    # Setup the decoders to return a string value
    decode_single.side_effect = ["0x000", "0x111", 18, 18]
    decode_abi.side_effect = [("WETH",), ("WBTC",)]

    session_context = await aiohttp.ClientSession().__aenter__()
    session_context.post = CoroutineMock(return_value=response)

    instance = Cls("0x123456")
    await instance.resolve_context_asynchronously("rpc_uri")

    # Check that the internal states (context) have been set
    assert instance.symbol_0 == "WETH"
    assert instance.symbol_1 == "WBTC"
    assert instance.decimals_0 == 18
    assert instance.decimals_1 == 18
    assert instance.swap_price_0_scaling_factor == 10**18
    assert instance.swap_price_1_scaling_factor == 10**18


@patch("src.events.handlers.uniswap.v3_pool.swap.decode_hex")
@patch("src.events.handlers.uniswap.v3_pool.swap.decode_abi")
def test_handle(decode_abi, _decode_hex):
    """ """
    instance = Cls("0x123456")

    # Directly set the context
    instance.symbol_0 = "WETH"
    instance.symbol_1 = "WBTC"
    instance.decimals_0 = 18
    instance.decimals_1 = 18
    instance.swap_price_0_scaling_factor = 10**18
    instance.swap_price_1_scaling_factor = 10**18

    # Setup the decoders
    decode_abi.return_value = [100, -100, 100, 100, 100]

    result = instance.handle(
        "0xraw_data", ["event_topic", "sender_topic", "recipient_topic"]
    )

    print("RESULT", result)

    assert result == {
        "sender": "sender_topic",
        "recipient": "recipient_topic",
        "symbol_0": "WETH",
        "symbol_1": "WBTC",
        "amount_0": "100",
        "amount_1": "-100",
        "swap_price_0": "1000000000000000000",  # 18 decimals
        "swap_price_1": "1000000000000000000",  # 18 decimals
        "sqrt_price_x96": "100",
        "liquidity": "100",
        "tick": "100",
    }


def test_handle_before_resolve_context():
    instance = Cls("0x123456")
    result = instance.handle("0xraw_data", ["0xtopic0"])

    # Result is simply empty
    assert result == {}

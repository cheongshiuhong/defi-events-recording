# Standard libraries
import json

# 3rd party libraries
from asynctest import MagicMock, CoroutineMock, patch
import pytest

# Code
from src.live.helpers.processor import StreamProcessor as Cls

# Constants
RPC_URI = "mocked_rpc_uri"
GAS_CURRENCY = "ETH"
QUOTE_CURRENCY = "SGD"
MOCKED_EVENT_LOG = {
    "removed": False,
    "logIndex": "0x123",
    "transactionIndex": "0x123",
    "transactionHash": "0x123456789",
    "blockHash": "0x123456789",
    "blockNumber": "0x123",
    "address": "0x123456789",
    "data": "0xa1b2c3d4e5",
    "topics": ["0x123456789"],
}
MOCKED_BLOCK = {"timestamp": "0x12345"}
MOCKED_TRANSACTION_RECEIPT = {
    "from": "0x123456789",
    "to": "0x987654321",
    "gasUsed": "0x123",
    "effectiveGasPrice": "0x456",
}
MOCKED_BINANCE_KLINE = [
    [
        "123456789",  # time
        "1234.5678",  # open
        "1234.5678",  # high
        "1234.5678",  # low
        "1234.5678",  # close
    ]
]


def get_instance():
    """Helper to create an instance"""
    return Cls(MagicMock(), RPC_URI, GAS_CURRENCY, QUOTE_CURRENCY)


def test_register_event_id():
    """ """
    instance = get_instance()
    instance.register_event_id(0, "id_0")
    instance.register_event_id(1, "id_1")
    instance.register_event_id(2, "id_2")


def test_register_event_handler():
    """ """
    instance = get_instance()
    instance.register_event_handler(0, MagicMock())
    instance.register_event_handler(1, MagicMock())
    instance.register_event_handler(2, MagicMock())


@pytest.mark.asyncio
@patch("aiohttp.ClientSession")
async def test_process_forever(session):
    """ """
    # Setup the mocked responses
    mocked_block_response = MagicMock()
    mocked_block_response.json = CoroutineMock(
        return_value={"jsonrpc": "2.0", "id": 1, "result": MOCKED_BLOCK}
    )
    mocked_transaction_receipt_response = MagicMock()
    mocked_transaction_receipt_response.json = CoroutineMock(
        return_value={"jsonrpc": "2.0", "id": 1, "result": MOCKED_TRANSACTION_RECEIPT}
    )
    mocked_binance_response = MagicMock()
    mocked_binance_response.json = CoroutineMock(return_value=MOCKED_BINANCE_KLINE)

    # Setup the mocked session
    session_context = await session().__aenter__()

    session_context.post = CoroutineMock(
        side_effect=[mocked_block_response, mocked_transaction_receipt_response]
    )

    session_context.get = CoroutineMock(side_effect=[mocked_binance_response])

    # Setup the mocked queues (2 inputs)
    input_queue = MagicMock()
    input_queue.get = CoroutineMock(
        side_effect=[
            {"subscription_id": "subscription_id_123", "event_log": MOCKED_EVENT_LOG},
            {"subscription_id": "subscription_id_123", "event_log": MOCKED_EVENT_LOG},
        ]
    )
    output_queue = MagicMock()
    output_queue.put = CoroutineMock()

    # Setup the mocked event handler
    event_handler = MagicMock()

    # Initialize the instance and register the components
    instance = get_instance()
    instance.register_event_id("subscription_id_123", "event_id_123")
    instance.register_event_handler("subscription_id_123", event_handler)

    # Async iterator will raise RuntimeError: StopIteration
    with pytest.raises(RuntimeError):
        await instance.process_forever(input_queue, output_queue)

    # Should have tried to read from input queue 3 times
    # (third time raised error)
    assert len(input_queue.get.mock_calls) == 3

    # Should have put the result into the queue twice
    assert len(output_queue.put.mock_calls) == 2

    # Should have called post on the session twice
    # (once for block once for txn receipt)
    # (second input has same data which should be cached)
    assert len(session_context.post.mock_calls) == 2

    # Should have called get on the session once to binance
    # (second input has same data which should be cached)
    session_context.get.assert_called_once()


@pytest.mark.asyncio
@patch("aiohttp.ClientSession")
async def test_process_forever_retry_transaction_receipt_query(session):
    # Setup the mocked responses
    mocked_block_response = MagicMock()
    mocked_block_response.json = CoroutineMock(
        return_value={"jsonrpc": "2.0", "id": 1, "result": MOCKED_BLOCK}
    )
    mocked_transaction_receipt_empty_response = MagicMock()
    mocked_transaction_receipt_empty_response.json = CoroutineMock(
        return_value={"jsonrpc": "2.0", "id": 1, "result": None}
    )
    mocked_transaction_receipt_response = MagicMock()
    mocked_transaction_receipt_response.json = CoroutineMock(
        return_value={"jsonrpc": "2.0", "id": 1, "result": MOCKED_TRANSACTION_RECEIPT}
    )
    mocked_binance_response = MagicMock()
    mocked_binance_response.json = CoroutineMock(return_value=MOCKED_BINANCE_KLINE)

    # Setup the mocked session
    session_context = await session().__aenter__()

    session_context.post = CoroutineMock(
        side_effect=[
            mocked_block_response,
            mocked_transaction_receipt_empty_response,
            mocked_transaction_receipt_response,
        ]
    )

    session_context.get = CoroutineMock(side_effect=[mocked_binance_response])

    # Setup the mocked queues (2 inputs)
    input_queue = MagicMock()
    input_queue.get = CoroutineMock(
        side_effect=[
            {"subscription_id": "subscription_id_123", "event_log": MOCKED_EVENT_LOG},
            {"subscription_id": "subscription_id_123", "event_log": MOCKED_EVENT_LOG},
        ]
    )
    output_queue = MagicMock()
    output_queue.put = CoroutineMock()

    # Setup the mocked event handler
    event_handler = MagicMock()

    # Initialize the instance and register the components
    instance = get_instance()
    instance.register_event_id("subscription_id_123", "event_id_123")
    instance.register_event_handler("subscription_id_123", event_handler)

    # Async iterator will raise RuntimeError: StopIteration
    with pytest.raises(RuntimeError):
        await instance.process_forever(input_queue, output_queue)

    # Should have tried to read from input queue 3 times
    # (third time raised error)
    assert len(input_queue.get.mock_calls) == 3

    # Should have put the result into the queue twice
    assert len(output_queue.put.mock_calls) == 2

    # Should have called post on the session thrice
    # (once for empty block, once for retry, once for txn receipt)
    # (second input has same data which should be cached)
    assert len(session_context.post.mock_calls) == 3

    # Should have called get on the session once to binance
    # (second input has same data which should be cached)
    session_context.get.assert_called_once()


@pytest.mark.asyncio
@patch("aiohttp.ClientSession")
async def test_process_forever_retry_block_query(session):
    # Setup the mocked responses
    mocked_block_empty_response = MagicMock()
    mocked_block_empty_response.json = CoroutineMock(
        return_value={"jsonrpc": "2.0", "id": 1, "result": None}
    )
    mocked_block_response = MagicMock()
    mocked_block_response.json = CoroutineMock(
        return_value={"jsonrpc": "2.0", "id": 1, "result": MOCKED_BLOCK}
    )
    mocked_transaction_receipt_response = MagicMock()
    mocked_transaction_receipt_response.json = CoroutineMock(
        return_value={"jsonrpc": "2.0", "id": 1, "result": MOCKED_TRANSACTION_RECEIPT}
    )
    mocked_binance_response = MagicMock()
    mocked_binance_response.json = CoroutineMock(return_value=MOCKED_BINANCE_KLINE)

    # Setup the mocked session
    session_context = await session().__aenter__()

    session_context.post = CoroutineMock(
        side_effect=[
            mocked_block_empty_response,
            mocked_transaction_receipt_response,
            mocked_block_response,
        ]
    )

    session_context.get = CoroutineMock(side_effect=[mocked_binance_response])

    # Setup the mocked queues (2 inputs)
    input_queue = MagicMock()
    input_queue.get = CoroutineMock(
        side_effect=[
            {"subscription_id": "subscription_id_123", "event_log": MOCKED_EVENT_LOG},
            {"subscription_id": "subscription_id_123", "event_log": MOCKED_EVENT_LOG},
        ]
    )
    output_queue = MagicMock()
    output_queue.put = CoroutineMock()

    # Setup the mocked event handler
    event_handler = MagicMock()

    # Initialize the instance and register the components
    instance = get_instance()
    instance.register_event_id("subscription_id_123", "event_id_123")
    instance.register_event_handler("subscription_id_123", event_handler)

    # Async iterator will raise RuntimeError: StopIteration
    with pytest.raises(RuntimeError):
        await instance.process_forever(input_queue, output_queue)

    # Should have tried to read from input queue 3 times
    # (third time raised error)
    assert len(input_queue.get.mock_calls) == 3

    # Should have put the result into the queue twice
    assert len(output_queue.put.mock_calls) == 2

    # Should have called post on the session thrice
    # (once for block, once for empty txn receipt, once for txn receipt)
    # (second input has same data which should be cached)
    assert len(session_context.post.mock_calls) == 3

    # Should have called get on the session once to binance
    # (second input has same data which should be cached)
    session_context.get.assert_called_once()

# Standard libraries
import json

# 3rd party libraries
from aiohttp.client_exceptions import ClientConnectionError
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
    instance = get_instance()
    instance.register_event_id(0, "id_0")
    instance.register_event_id(1, "id_1")
    instance.register_event_id(2, "id_2")


def test_register_event_handler():
    instance = get_instance()
    instance.register_event_handler(0, MagicMock())
    instance.register_event_handler(1, MagicMock())
    instance.register_event_handler(2, MagicMock())


@pytest.mark.asyncio
@patch("aiohttp.ClientSession")
async def test_process_forever(session):
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
async def test_process_forever_with_retry(session):
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
            ClientConnectionError(True, "close to test retry"),
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
    # first time client connnection error
    # (third time raised error)
    assert len(input_queue.get.mock_calls) == 3

    # Should have put the result into the queue once
    assert len(output_queue.put.mock_calls) == 1

    # Should have called post on the session twice
    # (once for block once for txn receipt)
    assert len(session_context.post.mock_calls) == 2

    # Should have called get on the session once to binance
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
            mocked_transaction_receipt_empty_response,  # First response
            mocked_transaction_receipt_empty_response,  # Retry fail
            mocked_transaction_receipt_response,  # Second response
            mocked_transaction_receipt_empty_response,  # Retry fail
            mocked_transaction_receipt_response,  # Third response
            mocked_transaction_receipt_response,  # Retry success
        ]
    )

    session_context.get = CoroutineMock(side_effect=[mocked_binance_response])

    # Setup the mocked queues (3 inputs)
    input_queue = MagicMock()
    input_queue.get = CoroutineMock(
        side_effect=[
            {
                "subscription_id": "subscription_id_123",
                "event_log": {**MOCKED_EVENT_LOG, "transactionHash": "0x12345"},
            },
            {
                "subscription_id": "subscription_id_123",
                "event_log": {**MOCKED_EVENT_LOG, "transactionHash": "0x23456"},
            },
            {
                "subscription_id": "subscription_id_123",
                "event_log": {**MOCKED_EVENT_LOG, "transactionHash": "0x34567"},
            },
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

    # Should have tried to read from input queue 4 times
    # (fourth time raised error)
    assert len(input_queue.get.mock_calls) == 4

    # Should have put the result into the queue thrice
    assert len(output_queue.put.mock_calls) == 3

    # Should have called post on the session 6 times
    # once for block, once for first failure, once for failed retry
    # once for second receipt, once for failed retry
    # once for third receipt, once for successful retry
    assert len(session_context.post.mock_calls) == 7

    # Should have called get on the session once to binance
    # (second input has same data which should be cached)
    session_context.get.assert_called_once()


@pytest.mark.asyncio
@patch("aiohttp.ClientSession")
async def test_process_forever_retry_removed_transaction_receipt_query(session):
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
            mocked_transaction_receipt_empty_response,  # First response
            mocked_transaction_receipt_empty_response,  # Retry fail
            mocked_transaction_receipt_response,  # Second response
            mocked_transaction_receipt_empty_response,  # Retry fail
            # mocked_transaction_receipt_response,  # Third response
            # mocked_transaction_receipt_empty_response,  # Retry fail
            # mocked_transaction_receipt_response,  # Fourth response (to remove retry)
        ]
    )

    session_context.get = CoroutineMock(side_effect=[mocked_binance_response])

    # Setup the mocked queues (4 inputs)
    input_queue = MagicMock()
    input_queue.get = CoroutineMock(
        side_effect=[
            # First event that will fail
            {
                "subscription_id": "subscription_id_123",
                "event_log": {
                    **MOCKED_EVENT_LOG,
                    "transactionHash": "0x12345",
                    "removed": False,
                },
            },
            # Regular event
            {
                "subscription_id": "subscription_id_123",
                "event_log": {
                    **MOCKED_EVENT_LOG,
                    "transactionHash": "0x23456",
                    "removed": False,
                },
            },
            # A random removed event
            {
                "subscription_id": "subscription_id_123",
                "event_log": {
                    **MOCKED_EVENT_LOG,
                    "transactionHash": "0x12345",
                    "removed": True,
                },
            },
            # Remove the first one
            {
                "subscription_id": "subscription_id_123",
                "event_log": {
                    **MOCKED_EVENT_LOG,
                    "transactionHash": "0x12345",
                    "removed": True,
                },
            },
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

    # Should have tried to read from input queue 5 times
    # (fifth time raised error)
    assert len(input_queue.get.mock_calls) == 5

    # Should have put the result into the queue once
    # Thid response removes the first response's retries
    assert len(output_queue.put.mock_calls) == 1

    # Should have called post on the session 4 times
    # once for block, once for first failure, once for failed retry
    # once for second receipt, once for failed retry
    # third receipt should have 0 calls since it it removed but does not cancel anything
    # fourth receipt should have 0 calls since it only cancels the retries
    assert len(session_context.post.mock_calls) == 5

    # Should have called get on the session once to binance
    # (second input has same data which should be cached)
    session_context.get.assert_called_once()

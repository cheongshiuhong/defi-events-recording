# Standard libraries
import json

# 3rd party libraries
from asynctest import MagicMock, CoroutineMock, patch, call
import pytest

# Code
from src.historical.tasks.batch.helpers.processor import BatchProcessor as Cls

# Constants
MOCKED_EVENT_LOG = {
    "address": "0x123",
    "topics": ["0x123456789"],
    "data": "0xa1b2c3d4e5",
    "blockNumber": "0x123",
    "timeStamp": "0x000001",
    "gasPrice": "0x123",
    "gasUsed": "0x456",
    "logIndex": "0x123",
    "transactionHash": "0x123456789",
    "transactionIndex": "0x123",
}
MOCKED_BINANCE_KLINE = [
    [
        0,  # open time
        "1234.5678",  # open
        "1234.5678",  # high
        "1234.5678",  # low
        "1234.5678",  # close
        1,  # close time
    ]
]


def get_instance():
    return Cls(MagicMock(), "ETH", "SGD")


def test_initialization():
    # Simple initialization no-error check
    get_instance()


@pytest.mark.asyncio
@patch("src.historical.tasks.batch.helpers.processor.aiohttp")
async def test_start_processing(aiohttp):
    # Setup the mocked responses
    mocked_binance_klines = [
        [
            t * 1000,
            "1234.5678",
            "1234.5678",
            "1234.5678",
            "1234.5678",
            "1234.5678",
            (t + 1) * 1000,
        ]
        for t in range(20)
    ]
    mocked_binance_response = MagicMock()
    mocked_binance_response.json = CoroutineMock(
        side_effect=[mocked_binance_klines[:10], mocked_binance_klines[10:]]
    )

    # Setup the mocked session
    session_context = await aiohttp.ClientSession().__aenter__()
    session_context.get = CoroutineMock(return_value=mocked_binance_response)

    # Setup the mocked queues (2 inputs of 10 events each, 1 empty)
    input_queue = MagicMock()
    input_batch = [{**MOCKED_EVENT_LOG, "timeStamp": hex(t * 1000)} for t in range(20)]
    input_queue.get = CoroutineMock(
        side_effect=[input_batch[:10], input_batch[10:], []]
    )
    output_queue = MagicMock()
    output_queue.put = CoroutineMock()

    # Setup the mocked event handler
    event_handler = MagicMock()

    instance = get_instance()
    await instance.start_processing(
        input_queue, output_queue, "event_id", event_handler
    )

    # Handler should be called 20 times for 20 events
    assert len(event_handler.mock_calls) == 20

    # Session should be called twice with 2 unique timestamps
    assert len(session_context.get.mock_calls) == 2

    # Should get from queue 3 times for 3 inputs (3rd empty)
    assert len(input_queue.get.mock_calls) == 3

    # Should put into output 3 times for 2 non-empty + 1 empty inputs
    assert len(output_queue.put.mock_calls) == 3

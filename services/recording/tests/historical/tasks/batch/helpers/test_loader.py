# Standard libraries
import json

# 3rd party libraries
from asynctest import MagicMock, CoroutineMock, patch, call
import pytest

# Code
from src.historical.tasks.batch.helpers.loader import BatchLoader as Cls


def test_initialization():
    # Simple initialization no-error check
    Cls(MagicMock(), "api_key")


@pytest.mark.asyncio
@patch("src.historical.tasks.batch.helpers.loader.aiohttp")
async def test_start_loadingf(aiohttp):
    # Mock the session responses
    session_context = await aiohttp.ClientSession().__aenter__()
    response = MagicMock()
    response.json = CoroutineMock(
        side_effect=[
            # Regular response
            {"result": [{"data": "The data dictionary"}]},
            # Empty (no events in block range)
            {"result": []},
            # Regular response
            {"result": [{"data": "The data dictionary"}]},
        ]
    )
    session_context.get = CoroutineMock(return_value=response)

    # Mock the output queue
    mocked_output_queue = MagicMock()
    mocked_output_queue.put = CoroutineMock()

    instance = Cls(MagicMock(), "api_key")

    await instance.start_loading(
        output_queue=mocked_output_queue,
        contract_address="contract_adddress",
        event_topic="topic",
        # Configure for 3 iterations
        from_block=1,
        to_block=15,
        blocks_per_batch=5,
    )

    # Should put into output queue thrice
    # once for first and third responses
    # (second was empty and skipped)
    # once at the end to denote the end
    assert mocked_output_queue.put.mock_calls == [
        call([{"data": "The data dictionary"}]),
        call([{"data": "The data dictionary"}]),
        call([]),
    ]

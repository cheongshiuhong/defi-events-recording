# Standard libraries
import json

# 3rd party libraries
from asynctest import MagicMock, CoroutineMock, patch, call
import pytest

# Code
from src.historical.tasks.batch.helpers.writer import BatchWriter as Cls


def get_instance():
    """Helper to create an instance"""
    return Cls(MagicMock(), "host", "port", "database", "user", "password")


@pytest.mark.asyncio
@patch("src.historical.tasks.batch.helpers.writer.AsyncIOMotorClient")
async def test_start_writing(client):
    # Setup the client
    mocked_insert_many = CoroutineMock()
    client().__getitem__().__getitem__().insert_many = mocked_insert_many

    # Setup the mocked input queue (2 inputs of 10 events each, 1 empty)
    mocked_data = {"value": "the data", "transaction_hash": "0x123"}
    input_queue = MagicMock()
    input_queue.get = CoroutineMock(
        side_effect=[[mocked_data] * 10, [mocked_data] * 10, []]
    )

    # Initialize the instance and register the category
    instance = get_instance()

    # Async iterator will raise RuntimeError: StopIteration
    await instance.start_writing(input_queue, "category")

    # Should call the insert_many method 2 times
    assert mocked_insert_many.mock_calls == 2 * [call([mocked_data] * 10)]

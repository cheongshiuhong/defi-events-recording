# Standard libraries
import json

# 3rd party libraries
from asynctest import MagicMock, CoroutineMock, patch
import pytest

# Code
from src.live.helpers.writer import StreamWriter as Cls


def get_instance():
    """Helper to create an instance"""
    return Cls(MagicMock(), "host", "port", "database", "user", "password")


@patch("src.live.helpers.writer.AsyncIOMotorClient")
def test_register_category(_client):
    instance = get_instance()
    instance.register_category(0, "category_0")
    instance.register_category(1, "category_1")
    instance.register_category(2, "category_2")


@pytest.mark.asyncio
@patch("src.live.helpers.writer.AsyncIOMotorClient")
async def test_write_forever(client):
    # Setup the client
    mocked_update_one = CoroutineMock()
    client().__getitem__().__getitem__().update_one = mocked_update_one

    # Setup the input queue
    mocked_data = {"value": "the data", "transaction_hash": "0x123", "log_index": 123}
    input_queue = MagicMock()
    input_queue.get = CoroutineMock(
        side_effect=[
            {
                "subscription_id": 0,
                "data": mocked_data,
            }
        ]
    )

    # Initialize the instance and register the category
    instance = get_instance()
    instance.register_category(0, "category")

    # Async iterator will raise RuntimeError: StopIteration
    with pytest.raises(RuntimeError):
        await instance.write_forever(input_queue)

    # Should call the update one method
    mocked_update_one.assert_called()

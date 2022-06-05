# Standard libraries
import json

# 3rd party libraries
from websockets.exceptions import ConnectionClosedError
from asynctest import MagicMock, CoroutineMock, patch, call
import pytest

# Code
from src.live.helpers.listener import StreamListener as Cls

# Constants
WSS_URI = "mocked_wss_uri"


def test_add_event_subscription():
    """Should return the event ids in increasing numerical order"""
    instance = Cls(MagicMock(), WSS_URI)

    subscription_id_0 = instance.add_event_subscription(
        "0xmocked_address_0", "mocked_topic_0"
    )
    subscription_id_1 = instance.add_event_subscription(
        "0xmocked_address_1", "mocked_topic_1"
    )
    subscription_id_2 = instance.add_event_subscription(
        "0xmocked_address_2", "mocked_topic_2"
    )
    assert subscription_id_0 == 0
    assert subscription_id_1 == 1
    assert subscription_id_2 == 2


@pytest.mark.asyncio
@patch("websockets.connect")
async def test_listen_forever(mocked_ws_connect):
    """ """
    ws_context = await mocked_ws_connect().__aenter__()
    ws_context.send = CoroutineMock()
    ws_context.recv = CoroutineMock(
        side_effect=[
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": "subscription_id_123",
                },
            ),
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "params": {
                        "subscription": "subscription_id_123",
                        "result": {"value": "the result dictionary"},
                    },
                },
            ),
        ]
    )

    instance = Cls(MagicMock(), WSS_URI)
    subscription_id = instance.add_event_subscription(
        "0xmocked_address", "mocked_topic"
    )

    mocked_output_queue = MagicMock()
    mocked_output_queue.put = CoroutineMock()

    # Async iterator will raise RuntimeError: StopIteration
    with pytest.raises(RuntimeError):
        await instance.listen_forever(mocked_output_queue)

    assert mocked_output_queue.put.mock_calls == [
        call(
            {
                "subscription_id": subscription_id,
                "event_log": {"value": "the result dictionary"},
            }
        ),
    ]


@pytest.mark.asyncio
@patch("websockets.connect")
async def test_listen_forever_with_retry(mocked_ws_connect):
    """ """
    ws_context = await mocked_ws_connect().__aenter__()
    ws_context.send = CoroutineMock()

    # Replicate the side effects 2x for the second connection
    ws_context.recv = CoroutineMock(
        side_effect=2
        * [
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": "subscription_id_123",
                }
            ),
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "params": {
                        "subscription": "subscription_id_123",
                        "result": {"value": "the result dictionary"},
                    },
                }
            ),
        ]
    )

    # Mock the output queue
    mocked_output_queue = MagicMock()
    mocked_output_queue.put = CoroutineMock(
        side_effect=[
            ConnectionClosedError(True, "close connection to test retry"),
            None,
        ]
    )

    # Setup the instance and add the subscriptions
    instance = Cls(MagicMock(), WSS_URI)
    subscription_id = instance.add_event_subscription(
        "0xmocked_address", "mocked_topic"
    )

    # Async iterator will raise RuntimeError: StopIteration
    with pytest.raises(RuntimeError):
        await instance.listen_forever(mocked_output_queue)

    # There should be two calls, the second one is after retrying
    assert mocked_output_queue.put.mock_calls == 2 * [
        call(
            {
                "subscription_id": subscription_id,
                "event_log": {"value": "the result dictionary"},
            }
        ),
    ]

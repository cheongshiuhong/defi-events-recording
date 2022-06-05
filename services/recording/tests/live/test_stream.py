# Standard libraries
import os

# 3rd party libraries
from asynctest import MagicMock, CoroutineMock, patch
import pytest

# Code
from src.live.stream import Stream as Cls

# Constants
MOCKED_ENVIRONMENT = {
    "NODE_PROVIDER_WSS_URI": "mocked_wss_uri",
    "NODE_PROVIDER_RPC_URI": "mocked_rpc_uri",
    "DB_DATABASE": "database",
    "DB_USER": "user",
    "DB_PASSWORD": "password",
    "DB_HOST": "host",
    "DB_PORT": "port",
}


def get_instance():
    config = {
        "gas_pricing": {"gas_currency": "ETH", "quote_currency": "SGD"},
        "subscriptions": [
            {
                "event_id": "event_0",
                "contract_address": "0x123456789",
            }
        ],
    }
    return Cls(MagicMock(), config)


@patch("src.live.stream.EventsResolver")
@patch("src.live.stream.StreamWriter")
@patch("src.live.stream.StreamProcessor")
@patch("src.live.stream.StreamListener")
def test_initialization_with_environment_variables(
    listener, processor, writer, _events_resolver
):
    with patch.dict(os.environ, MOCKED_ENVIRONMENT):
        instance = get_instance()

    # Should set the subscriptions in the components
    listener().add_event_subscription.assert_called()
    processor().register_event_id.assert_called()
    writer().register_category.assert_called()


@patch("src.live.stream.EventsResolver")
@patch("src.live.stream.StreamWriter")
@patch("src.live.stream.StreamProcessor")
@patch("src.live.stream.StreamListener")
def test_initialization_without_node_provider_rpc_uri_environement(
    _listener, _processor, _writer, _events_resolver
):
    with patch.dict(
        os.environ,
        {k: v for k, v in MOCKED_ENVIRONMENT.items() if k != "NODE_PROVIDER_RPC_URI"},
    ):
        with pytest.raises(ValueError):
            instance = get_instance()


@patch("src.live.stream.EventsResolver")
@patch("src.live.stream.StreamWriter")
@patch("src.live.stream.StreamProcessor")
@patch("src.live.stream.StreamListener")
def test_initialization_without_node_provider_wss_uri_environement(
    _listener, _processor, _writer, _events_resolver
):
    with patch.dict(
        os.environ,
        {k: v for k, v in MOCKED_ENVIRONMENT.items() if k != "NODE_PROVIDER_WSS_URI"},
    ):
        with pytest.raises(ValueError):
            instance = get_instance()


@patch("src.live.stream.EventsResolver")
@patch("src.live.stream.StreamWriter")
@patch("src.live.stream.StreamProcessor")
@patch("src.live.stream.StreamListener")
def test_initialization_without_db_environement(
    _listener, _processor, _writer, _events_resolver
):
    with patch.dict(
        os.environ, {k: v for k, v in MOCKED_ENVIRONMENT.items() if "DB" not in k}
    ):
        with pytest.raises(ValueError):
            instance = get_instance()


@patch("src.live.stream.EventsResolver")
@patch("src.live.stream.StreamWriter")
@patch("src.live.stream.StreamProcessor")
@patch("src.live.stream.StreamListener")
def test_initialization_with_event_handler(
    _listener, processor, _writer, events_resolver
):
    event_handler = MagicMock()
    events_resolver.get_handler.return_value = event_handler

    with patch.dict(os.environ, MOCKED_ENVIRONMENT):
        instance = get_instance()

    # Handler should have its context resolved
    event_handler.resolve_context.assert_called()

    # Processor should register the event handler
    processor().register_event_handler.assert_called()


@patch("src.live.stream.EventsResolver")
@patch("src.live.stream.StreamWriter")
@patch("src.live.stream.StreamProcessor")
@patch("src.live.stream.StreamListener")
def test_initialization_without_event_handler(
    _listener, processor, _writer, events_resolver
):
    events_resolver.get_handler.return_value = None

    with patch.dict(os.environ, MOCKED_ENVIRONMENT):
        instance = get_instance()

    # Processor should now register an event handler
    processor().register_event_handler.assert_not_called()


@patch("src.live.stream.asyncio")
@patch("src.live.stream.EventsResolver")
@patch("src.live.stream.StreamWriter")
@patch("src.live.stream.StreamProcessor")
@patch("src.live.stream.StreamListener")
def test_start_synchronously(_listener, _processor, _writer, _events_resolver, asyncio):
    """ """
    with patch.dict(os.environ, MOCKED_ENVIRONMENT):
        instance = get_instance()

    instance.start_asynchronously = MagicMock()
    instance.start_synchronously()

    # Should call the asynchronous version of the method through asyncio
    asyncio.run.assert_called_with(instance.start_asynchronously())


@pytest.mark.asyncio
@patch("src.live.stream.asyncio")
@patch("src.live.stream.EventsResolver")
@patch("src.live.stream.StreamWriter")
@patch("src.live.stream.StreamProcessor")
@patch("src.live.stream.StreamListener")
async def test_start_asynchronously(
    listener, processor, writer, _events_resolver, asyncio
):
    """ """
    with patch.dict(os.environ, MOCKED_ENVIRONMENT):
        instance = get_instance()

        # Setup the asyncio coroutines
        asyncio.gather = CoroutineMock()

        await instance.start_asynchronously()

        # Should call the component's methods
        listener().listen_forever.assert_called()
        processor().process_forever.assert_called()
        writer().write_forever.assert_called()

        # The calls should be gathered asynchronously
        asyncio.gather.assert_called_with(
            listener().listen_forever(),
            processor().process_forever(),
            writer().write_forever(),
        )

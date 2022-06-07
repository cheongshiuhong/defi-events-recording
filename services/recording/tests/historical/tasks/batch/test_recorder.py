# Standard libraries
import os

# 3rd party libraries
from asynctest import MagicMock, CoroutineMock, patch
import pytest

# Code
from src.historical.tasks.batch.recorder import BatchRecorder as Cls

# Code
MOCKED_ENVIRONMENT = {
    "ETHERSCAN_API_KEY": "etherscan_api_key",
    "NODE_PROVIDER_RPC_URI": "mocked_rpc_uri",
    "DB_DATABASE": "database",
    "DB_USER": "user",
    "DB_PASSWORD": "password",
    "DB_HOST": "host",
    "DB_PORT": "port",
}


# Clear the environment
os.environ = {}


def get_instance():
    config = {"gas_pricing": {"gas_currency": "ETH", "quote_currency": "SGD"}}
    return Cls(MagicMock(), config)


@patch("src.historical.tasks.batch.recorder.EventsResolver")
@patch("src.historical.tasks.batch.recorder.BatchWriter")
@patch("src.historical.tasks.batch.recorder.BatchProcessor")
@patch("src.historical.tasks.batch.recorder.BatchLoader")
def test_initialization_with_environment_variables(
    loader, processor, writer, _events_resolver
):
    with patch.dict(os.environ, MOCKED_ENVIRONMENT):
        # Simple initialization no-error check
        get_instance()

    # Should initialize the components
    loader.assert_called()
    processor.assert_called()
    writer.assert_called()


@patch("src.historical.tasks.batch.recorder.EventsResolver")
@patch("src.historical.tasks.batch.recorder.BatchWriter")
@patch("src.historical.tasks.batch.recorder.BatchProcessor")
@patch("src.historical.tasks.batch.recorder.BatchLoader")
def test_initialization_without_etherscan_api_key_environment(
    _loader, _processor, _writer, _events_resolver
):
    with patch.dict(
        os.environ,
        {k: v for k, v in MOCKED_ENVIRONMENT.items() if k != "ETHERSCAN_API_KEY"},
    ):
        with pytest.raises(ValueError):
            get_instance()


@patch("src.historical.tasks.batch.recorder.EventsResolver")
@patch("src.historical.tasks.batch.recorder.BatchWriter")
@patch("src.historical.tasks.batch.recorder.BatchProcessor")
@patch("src.historical.tasks.batch.recorder.BatchLoader")
def test_initialization_without_node_provider_rpc_uri_environment(
    _loader, _processor, _writer, _events_resolver
):
    with patch.dict(
        os.environ,
        {k: v for k, v in MOCKED_ENVIRONMENT.items() if k != "NODE_PROVIDER_RPC_URI"},
    ):
        with pytest.raises(ValueError):
            get_instance()


@patch("src.historical.tasks.batch.recorder.EventsResolver")
@patch("src.historical.tasks.batch.recorder.BatchWriter")
@patch("src.historical.tasks.batch.recorder.BatchProcessor")
@patch("src.historical.tasks.batch.recorder.BatchLoader")
def test_initialization_without_db_environment(
    _loader, _processor, _writer, _events_resolver
):
    with patch.dict(
        os.environ, {k: v for k, v in MOCKED_ENVIRONMENT.items() if "DB" not in k}
    ):
        with pytest.raises(ValueError):
            get_instance()


@patch("src.historical.tasks.batch.recorder.EventsResolver")
@patch("src.historical.tasks.batch.recorder.BatchWriter")
@patch("src.historical.tasks.batch.recorder.BatchProcessor")
@patch("src.historical.tasks.batch.recorder.BatchLoader")
@patch("src.historical.tasks.batch.recorder.asyncio")
def test_record_synchronously(asyncio, _loader, _processor, _writer, _events_resolver):
    with patch.dict(os.environ, MOCKED_ENVIRONMENT):
        instance = get_instance()

    instance.record_asynchronously = CoroutineMock()
    instance.record_synchronously(
        contract_address="0x123456",
        event_id="event_id",
        from_block=123456,
        to_block=654321,
    )

    # Should call the asynchronous method
    instance.record_asynchronously.assert_called_once()

    # Should call it with asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete.assert_called_once()


@pytest.mark.asyncio
@patch("src.historical.tasks.batch.recorder.EventsResolver")
@patch("src.historical.tasks.batch.recorder.BatchWriter")
@patch("src.historical.tasks.batch.recorder.BatchProcessor")
@patch("src.historical.tasks.batch.recorder.BatchLoader")
async def test_record_asynchronously(loader, processor, writer, events_resolver):
    # Mock the components
    loader().start_loading = CoroutineMock()
    processor().start_processing = CoroutineMock()
    writer().start_writing = CoroutineMock()

    event_handler = MagicMock()
    event_handler.resolve_context_asynchronously = CoroutineMock()
    events_resolver.get_handler.return_value = event_handler

    with patch.dict(os.environ, MOCKED_ENVIRONMENT):
        instance = get_instance()

    await instance.record_asynchronously(
        contract_address="0x123456",
        event_id="event_id",
        from_block=123456,
        to_block=654321,
    )

    # Should call the the component's methods

    events_resolver.get_topic.assert_called_once()
    events_resolver.get_category.assert_called_once()
    events_resolver.get_handler.assert_called_once()
    event_handler.resolve_context_asynchronously.assert_called_once()
    loader().start_loading.assert_called_once()
    processor().start_processing.assert_called_once()
    writer().start_writing.assert_called_once()


@pytest.mark.asyncio
@patch("src.historical.tasks.batch.recorder.EventsResolver")
@patch("src.historical.tasks.batch.recorder.BatchWriter")
@patch("src.historical.tasks.batch.recorder.BatchProcessor")
@patch("src.historical.tasks.batch.recorder.BatchLoader")
async def test_record_asynchronously_without_handler(loader, processor, writer, events_resolver):
    # Mock the components
    loader().start_loading = CoroutineMock()
    processor().start_processing = CoroutineMock()
    writer().start_writing = CoroutineMock()

    events_resolver.get_handler.return_value = None

    with patch.dict(os.environ, MOCKED_ENVIRONMENT):
        instance = get_instance()

    await instance.record_asynchronously(
        contract_address="0x123456",
        event_id="event_id",
        from_block=123456,
        to_block=654321,
    )

    # Should call the the component's methods

    events_resolver.get_topic.assert_called_once()
    events_resolver.get_category.assert_called_once()
    events_resolver.get_handler.assert_called_once()
    loader().start_loading.assert_called_once()
    processor().start_processing.assert_called_once()
    writer().start_writing.assert_called_once()

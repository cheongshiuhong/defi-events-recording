# Standard libraries
import json

# 3rd party libraries
from mock import patch, MagicMock
from fastapi.testclient import TestClient
import pytest

# Code
from src.historical.app import app

# The mocked app client
client = TestClient(app)


STATUS_TEST_PARAMETERS = [
    (False, False, "Pending"),
    (True, False, "Failed"),
    (True, True, "Completed"),
]


@pytest.mark.parametrize("ready,successful,expected", STATUS_TEST_PARAMETERS)
@patch("src.historical.tasks.router.worker.AsyncResult")
def test_get_task_status(async_result, ready, successful, expected):
    # Mock that task is not ready (pending)
    async_result().ready.return_value = ready
    async_result().successful.return_value = successful

    response = client.get("/api/rpc/v1/tasks/get_status/123456")

    assert response.status_code == 200
    assert response.json() == {"task_id": "123456", "status": expected}


RECORD_HISTORICAL_EVENTS_PARAMETERS = [
    # Proper
    ("event_id", "0x123456789", 100, 500, 200, True),
    # From block > To block
    ("event_id", "0x123456789", 500, 100, 400, False),
    # Missing parameters
    ("", "0x123456789", 500, 100, 400, False),
    ("event_id", "", 500, 100, 400, False),
    ("event_id", "0x123456789", -100, 100, 400, False),
    ("event_id", "0x123456789", 500, -100, 400, False),
]


@pytest.mark.parametrize(
    "event_id,contract_address,from_block,to_block,expected_status_code,is_task_called",
    RECORD_HISTORICAL_EVENTS_PARAMETERS,
)
@patch("src.historical.tasks.router.record_historical_events_task")
def test_router_record_historical_events(
    task: MagicMock,
    event_id,
    contract_address,
    from_block,
    to_block,
    expected_status_code,
    is_task_called,
):
    response = client.post(
        "/api/rpc/v1/tasks/record_historical_events",
        data=json.dumps(
            {
                "event_id": event_id,
                "contract_address": contract_address,
                "from_block": from_block,
                "to_block": to_block,
            }
        ),
    )

    assert response.status_code == expected_status_code
    assert bool(task.mock_calls) == is_task_called

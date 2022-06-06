# Standard libraries
import json

# 3rd party libraries
from mock import patch
from fastapi.testclient import TestClient

# Code
from src.historical.app import app

# The mocked app client
client = TestClient(app)


@patch("src.historical.tasks.router.worker.AsyncResult")
def test_get_task_status_when_not_ready(async_result):
    # Mock that task is not ready (pending)
    async_result().ready.return_value = False
    async_result().successful.return_value = False

    response = client.get("/api/v1/tasks/get_status/123456")

    assert response.status_code == 200
    assert response.json() == {"task_id": "123456", "status": "Pending"}


@patch("src.historical.tasks.router.worker.AsyncResult")
def test_get_task_status_when_failed(async_result):
    # Mock that task has failed
    async_result().ready.return_value = True
    async_result().successful.return_value = False

    response = client.get("/api/v1/tasks/get_status/123456")

    assert response.status_code == 200
    assert response.json() == {"task_id": "123456", "status": "Failed"}


@patch("src.historical.tasks.router.worker.AsyncResult")
def test_get_task_status_when_pending(async_result):
    # Mock that task is completed
    async_result().ready.return_value = True
    async_result().successful.return_value = True

    response = client.get("/api/v1/tasks/get_status/123456")

    assert response.status_code == 200
    assert response.json() == {"task_id": "123456", "status": "Completed"}


@patch("src.historical.tasks.router.record_historical_events_task")
def test_router_record_historical_events_with_invalid_blocks(task):
    response = client.post(
        "/api/v1/tasks/record_historical_events",
        data=json.dumps(
            {
                "event_id": "event_id",
                "contract_address": "0x123456789",
                "from_block": 500,
                "to_block": 100,
            }
        ),
    )

    # Should get a bad request
    assert response.status_code == 400


@patch("src.historical.tasks.router.record_historical_events_task")
def test_router_record_historical_events(task):
    response = client.post(
        "/api/v1/tasks/record_historical_events",
        data=json.dumps(
            {
                "contract_address": "0x123456789",
                "event_id": "event_id",
                "from_block": 100,
                "to_block": 500,
            }
        ),
    )

    # Should get a bad request
    assert response.status_code == 200

    # Should call the task
    task.delay.assert_called_with("0x123456789", "event_id", 100, 500)

# 3rd party libraries
from fastapi import APIRouter, HTTPException

# from celery.result import AsyncResult

# Code
from .models import RecordHistoricalEventsRequest, TaskResult
from .batch.task import record_historical_events_task
from .worker import worker

task_router = APIRouter()


@task_router.get("/get_status/{task_id}", response_model=TaskResult)
async def get_task_status(task_id: str) -> dict[str, str]:
    """
    Gets the status of a task by its task id.

    Args:
        task_id: The task_id to lookup.

    Returns:
        The response dictionary of the task_id and its status.
    """
    task = worker.AsyncResult(task_id)

    if not task.ready():
        return {"task_id": task_id, "status": "Pending"}

    if task.successful():
        return {"task_id": task_id, "status": "Completed"}

    return {"task_id": task_id, "status": "Failed"}


@task_router.post("/record_historical_events", response_model=TaskResult)
async def record_historical_events(
    request_data: RecordHistoricalEventsRequest,
) -> dict[str, str]:
    """
    Invokes the task to record historical events.

    Note: "from_block" must be smaller than "to_block".

    Args:
        request_data: The request body of the task's arguments.

    Returns:
        The response dictionary of thes task_id and an initially pending status.
    """
    # Bad request if from_block greater than to block
    if request_data.from_block >= request_data.to_block:
        raise HTTPException(
            status_code=400, detail='"from_block" must be smaller than "to_block"'
        )

    task_id = record_historical_events_task.delay(
        request_data.contract_address,
        request_data.event_id,
        request_data.from_block,
        request_data.to_block,
    )

    return {"task_id": str(task_id), "status": "Pending"}

# 3rd party libraries
from fastapi import APIRouter, HTTPException

# Code
from .models import RecordHistoricalEventsRequest, TaskResult
from .batch.task import record_historical_events_task
from .worker import worker

task_router = APIRouter()


@task_router.get(
    "/get_status/{task_id}",
    summary="Get Task Status",
    response_model=TaskResult,
)
async def get_task_status(task_id: str) -> dict[str, str]:
    """
    **Gets the status of a task by its task id**.

    - **task_id**: The id of the task to get the status of.

    <u>Returns the task's status, which is one of</u>:\n
    - **Pending**
    - **Failed**
    - **Completed**

    \f
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


@task_router.post(
    "/record_historical_events",
    summary="Invoke the Recording of Historical Events",
    response_model=TaskResult,
)
async def record_historical_events(
    request_data: RecordHistoricalEventsRequest,
) -> dict[str, str]:
    """
    **Invokes the task to record historical events.**

    <u>Request body</u>:\n
    - **event_id**: The identifier of the event to resolve the handler
        when processing. (e.g., "uniswap-v3-pool-swap" for the Uniswap V3
        Pool's Swap events)
    - **contract_address**: The address of the contract to record
        the emitted events from.
    - **from_block**: The smallest block number to record events from.
    - **to_block**: The largest block number to record events from.

    <u>Returns **400 - Bad Request** if</u>:
    - **from_block** > **to_block**.
    - Either of **from_block** or **to_block** < 0.
    - Either of **event_id** or **contract_address** is an empty string.

    \f
    Args:
        request_data: The request body of the task's arguments.

    Returns:
        The response dictionary of thes task_id and an initially pending status.
    """
    if (
        not request_data.contract_address
        or not request_data.event_id
        or request_data.from_block < 0
        or request_data.to_block < 0
    ):
        raise HTTPException(status_code=400, detail="Request body incomplete")

    # Bad request if from_block greater than to block
    if request_data.from_block > request_data.to_block:
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

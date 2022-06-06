# 3rd party libraries
from pydantic import BaseModel


class TaskResult(BaseModel):
    task_id: str
    status: str


class RecordHistoricalEventsRequest(BaseModel):
    event_id: str
    contract_address: str
    from_block: int
    to_block: int

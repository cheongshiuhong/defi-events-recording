# 3rd party libraries
from dotenv import load_dotenv
import yaml

# Code
from src.lib.logger import RecordingLogger
from ..worker import worker
from .recorder import BatchRecorder
from .types import BatchConfig

# Load the environment
load_dotenv()


@worker.task(name="record_historical_events_task")
def record_historical_events_task(*args, **kwargs) -> str:
    """
    The task entrypoint to invoke the recording process.
    """
    with open("config.yaml", "r") as f:
        config: BatchConfig = yaml.load(f, yaml.Loader)["batch"]

    logger = RecordingLogger("HistoricalEventsRecordingTaskLogger")
    recorder = BatchRecorder(logger, config)
    recorder.record_synchronously(*args, **kwargs)
    logger.info("Task complete!")

    return "OK"

# Code
from src.lib.logger import RecordingLogger as Cls


def test_initialization():
    # Simple initialization no-error check
    Cls("testing_logger")

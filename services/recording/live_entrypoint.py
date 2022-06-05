# 3rd party libraries
from dotenv import load_dotenv
import yaml

# Code
from src.lib.logger import RecordingLogger
from src.live.stream import Stream


if __name__ == "__main__":
    with open("config.yaml", "r") as f:
        config = yaml.load(f, yaml.Loader)

    load_dotenv()

    logger = RecordingLogger("LiveRecordingLogger")
    stream = Stream(logger, config)
    stream.start_synchronously()

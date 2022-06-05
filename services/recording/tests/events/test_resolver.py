# 3rd party libraries
from asynctest import MagicMock, patch, call
import pytest

# Code
from src.events.resolver import EventsResolver as Cls

# Constants
MOCKED_HANDLER_CLASS = MagicMock()
MOCKED_EVENT_METADATA_MAPPING = {
    "event_0": {
        "category": "category_0",
        "topic": "0x000",
        "handler_class": MOCKED_HANDLER_CLASS,
    },
    "event_1": {
        "category": "category_1",
        "topic": "0x111",
        # No handler class
    },
}


def test_get_category():
    """ """
    with patch.dict(
        "src.events.resolver._EVENT_METADATA_MAPPING", MOCKED_EVENT_METADATA_MAPPING
    ):
        category_0 = Cls.get_category("event_0")
        category_1 = Cls.get_category("event_1")

        assert category_0 == "category_0"
        assert category_1 == "category_1"


def test_get_topic():
    """ """
    with patch.dict(
        "src.events.resolver._EVENT_METADATA_MAPPING", MOCKED_EVENT_METADATA_MAPPING
    ):
        topic_0 = Cls.get_topic("event_0")
        topic_1 = Cls.get_topic("event_1")

        assert topic_0 == "0x000"
        assert topic_1 == "0x111"


def test_get_handler():
    """ """
    with patch.dict(
        "src.events.resolver._EVENT_METADATA_MAPPING", MOCKED_EVENT_METADATA_MAPPING
    ):
        mocked_contract_address = "0x123456789"
        handler_0 = Cls.get_handler("event_0", mocked_contract_address)
        handler_1 = Cls.get_handler("event_1", mocked_contract_address)

        assert handler_0 == MOCKED_HANDLER_CLASS()
        assert handler_1 == None


def test_get_unknown_event():
    with patch.dict(
        "src.events.resolver._EVENT_METADATA_MAPPING", MOCKED_EVENT_METADATA_MAPPING
    ):
        with pytest.raises(ValueError):
            Cls.get_category("not_an_event_id_999")

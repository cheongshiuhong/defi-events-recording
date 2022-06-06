# 3rd party libraries
import pytest

# Code
from src.events.handlers.base import BaseEventHandler


def test_abstract_class_uninstantiable():
    with pytest.raises(TypeError):
        BaseEventHandler("0x123")


def test_sub_class_initialization():
    class SubClass(BaseEventHandler):
        def resolve_context_synchronously(self, rpc_uri: str):
            pass

        def resolve_context_asynchronously(self, rpc_uri: str):
            pass

        def handle(self, raw_data: str, topics: list[str]) -> dict[str, str]:
            pass

    sub_instance = SubClass("0x123")
    assert sub_instance.contract_address == "0x123"
    assert sub_instance.__repr__() == "Event handler for contract: 0x123"
    assert sub_instance.__str__() == "Event handler for contract: 0x123"

# Standard libraries
import json

# 3rd party libraries
from asynctest import CoroutineMock, patch
from fastapi.testclient import TestClient
import pytest

# Code
from src.app import app

# The mocked app client
client = TestClient(app)

# Constants
MOCKED_SWAP_EVENT = {
    "transaction_hash": "0x123456",
    "block_number": 123456,
    "timestamp": 123456789,
    "gas_used": "123456",
    "gas_price_wei": "123456789",
    "gas_price_quote": {"currency": "SGD", "value": "123456789"},
    "data": {
        "sender": "0x123456789",
        "recipient": "0x123456789",
        "symbol_0": "WETH",
        "symbol_1": "WBTC",
        "amount_0": "123456789",
        "amount_1": "123456789",
        "swap_price_0": "123456789",
        "swap_price_1": "123456789",
    },
}


PARSED_MOCKED_SWAP_EVENT = {
    "transaction_hash": "0x123456",
    "block_number": 123456,
    "timestamp": 123456789,
    "gas_used": 123456,
    "gas_price_wei": 123456789,
    "gas_price_quote": {"currency": "SGD", "value": 123456789},
    "sender": "0x123456789",
    "recipient": "0x123456789",
    "symbol_0": "WETH",
    "symbol_1": "WBTC",
    "amount_0": 123456789,
    "amount_1": 123456789,
    "swap_price_0": 123456789,
    "swap_price_1": 123456789,
}


SUCCESS_RESPONSE_PARAMETERS = [
    "/api/v1/uniswap/v3-pool/swaps?transaction_hash=0x123456",
    "/api/v1/uniswap/v3-pool/swaps?from_block=123",
    "/api/v1/uniswap/v3-pool/swaps?to_block=321",
    "/api/v1/uniswap/v3-pool/swaps?from_block=123&to_block=321",
    "/api/v1/uniswap/v3-pool/swaps?from_block=123&to_block=321&contract_address=0x123",
]


@pytest.mark.parametrize("uri", SUCCESS_RESPONSE_PARAMETERS)
@patch("src.routers.v1.endpoints.uniswap.v3_pool.MongoDBClient")
def test_get_swaps_with_transaction_hash(db, uri):
    # Mock the db response
    db().swaps.find().sort().skip().to_list = CoroutineMock(
        return_value=10 * [MOCKED_SWAP_EVENT]
    )
    db().swaps.count_documents = CoroutineMock(return_value=100)

    response = client.get(uri)

    result = response.json()

    # Should parse and return what the database returns
    assert result["data"] == 10 * [PARSED_MOCKED_SWAP_EVENT]
    assert result["count"] == 10
    assert result["total"] == 100


@patch("src.routers.v1.endpoints.uniswap.v3_pool.MongoDBClient")
def test_get_swaps_without_arguments(db):
    # Mock the db response
    db().swaps.find().sort().skip().to_list = CoroutineMock(
        return_value=10 * [MOCKED_SWAP_EVENT]
    )
    db().swaps.count_documents = CoroutineMock(return_value=100)

    uri = "/api/v1/uniswap/v3-pool/swaps"
    response = client.get(uri)

    # Should return 400 - Bad Request
    assert response.status_code == 400

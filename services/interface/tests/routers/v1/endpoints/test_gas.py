# Standard libraries
import json

# 3rd party libraries
from asynctest import CoroutineMock, patch
from fastapi.testclient import TestClient

# Code
from src.app import app

# The mocked app client
client = TestClient(app)


@patch("src.routers.v1.endpoints.gas.MongoDBClient")
def test_get_gas_details(db):
    # Mock the db's response
    db().swaps.find_one = CoroutineMock(
        return_value={
            "gas_used": "123456",
            "gas_price_wei": "123456789",
            "gas_price_quote": {"currency": "SGD", "value": "123456789"},
        }
    )

    response = client.get("/api/v1/gas/0x123456")

    # Should return 200 - OK
    assert response.status_code == 200

    data = response.json()

    # The data should be parsed
    assert data == {
        "gas_used": 123456,
        "gas_price_wei": 123456789,
        "gas_price_quote": {"currency": "SGD", "value": 123456789},
    }


@patch("src.routers.v1.endpoints.gas.MongoDBClient")
def test_get_gas_details_but_not_found(db):
    # Mock the db's response
    db().swaps.find_one = CoroutineMock(return_value=None)

    response = client.get("/api/v1/gas/0x123456")

    # Should return 404 - Not Found
    assert response.status_code == 404

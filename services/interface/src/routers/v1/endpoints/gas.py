# 3rd party libraries
from fastapi import APIRouter, HTTPException

# Code
from src.core.db import MongoDBClient
from .models import GasResponse

# The router instance
gas_router = APIRouter()


@gas_router.get("/{transaction_hash}", response_model=GasResponse)
async def get_gas_details(transaction_hash: str = "") -> GasResponse:
    """
    **Gets the gas details for a transaction by its hash**:

    - **transaction_hash**: The transaction hash whose gas details
        will be returned.
    \n
    Returns **404 - Not Found** if gas details for **transaction_hash**
        could not be found.

    \f
    Args:
        transaction_hash: The transaction hash to lookup.

    Returns:
        The gas details for the transaction found.
    """
    # Check the query
    client = MongoDBClient()
    query: dict[str, str] = {"transaction_hash": transaction_hash}

    # For now we query from the swaps collection
    # We might denormalize the gas-specific details
    # into a separate collection in the future
    # if this access pattern persists
    data = await client.swaps.find_one(query)

    # If empty:
    if not data:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return GasResponse(**data)

# Standard libraries
from typing import Union
import asyncio

# 3rd party libraries
from fastapi import APIRouter, HTTPException

# Code
from src.core.types import EventLog
from src.core.db import MongoDBClient
from .models import UniswapV3PoolSwap, UniswapV3PoolSwapResponse

# The router instance
uniswap_v3_pool_router = APIRouter()


def parse_swaps(raw_data: list[EventLog]) -> list[UniswapV3PoolSwap]:
    """
    Parses the swaps data
    """
    return [UniswapV3PoolSwap(**d, **d["data"]) for d in raw_data]


@uniswap_v3_pool_router.get(
    "/swaps",
    summary="Get Uniswap V3 Pool's Swap Events",
    response_model=UniswapV3PoolSwapResponse,
)
async def get_swaps(
    transaction_hash: str = "",
    from_block: int = 0,
    to_block: int = 0,
    contract_address: str = "",
    limit: int = 200,
    offset: int = 0,
) -> UniswapV3PoolSwapResponse:
    """
    **Gets uniswap v3 pool's swap events with the arguments**:

    Two types of query parameters are allowed:

    <u>First type (*transaction-based*)</u>:\n
    - **transaction_hash**: Gets the events by the transaction hash (top priority).
        If this argument is provided, all the others are disregarded.

    <u>Second type (*range-based*)</u>:\n
    - **from_block**: Filters the events larger than or equal to this number.
    - **to_block**: Filters the events smaller than or equal to this number.
    - **contract_address** (optional):
        Filters the events that are emitted from this address.
    - **limit** (optional):
        The maximum number of events to be fetched. (default=200)
    - **offset** (optional):
        The number of events to skip. Useful for pagination. (default=0)

    Returns **400 - Bad Request** if no arguments provided.

    \f
    Args:
        transaction_hash: The transction hash to get the events for.
        from_block: The smallest block number to get events from.
        to_block: The largest block number to get events from.
        limit: The maximum number of events returned.
        offset: The number of events to skip.

    Returns:
        The json response of a list of events, the return count and total count.
    """
    # Check the query
    client = MongoDBClient()
    query: dict[str, Union[str, dict[str, int]]] = {"event_id": "uniswap-v3-pool-swap"}

    # First priority - Find by txn hash
    # limit/offfset is not used here
    if transaction_hash:
        query["transaction_hash"] = transaction_hash

    # Second priority queries
    else:
        # Bad request
        if not from_block or not to_block:
            detail = (
                'Query must include either "transaction_hash" or '
                'both ("from_block" & "to_block")'
            )
            raise HTTPException(status_code=400, detail=detail)

        # Block query
        query["block_number"] = {"$gte": from_block, "$lte": to_block}

        # Optional filtering by contract address
        if contract_address:
            query["address"] = contract_address

    cursor = client.swaps.find(query).sort("block_number").skip(offset)

    data, total = await asyncio.gather(
        cursor.to_list(limit), client.swaps.count_documents(query)
    )

    return UniswapV3PoolSwapResponse(
        data=parse_swaps(data), count=len(data), total=total
    )

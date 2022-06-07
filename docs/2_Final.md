<div id="top"></div>

<!-- omit in toc -->

# Final Update

## The Interface

We have succesfully written an interface exposing RESTful API endpoints to retrieve data from the database. They can be called with a `GET` request to:

- The transaction gas endpoint: `/api/v1/gas/{transaction_hash}`
- The fully processed uniswap data endpoint `/api/v1/uniswap/v3-pool/swaps`

The gas endpoint simply retrieves the gas details for a given transaction:
```JSON
{
    "gas_used": 123456,
    "gas_price_wei": 1234567890, // 18 decimals from ether, 9 decimals from gwei
    "gas_price_quote": {
        "currency": "USDT",
        "value": 123456789123456789 // 18 decimals
    }
}
```

The Uniswap V3 Pool swaps endpoint retrieves the entire transaction with the decoded event parameters:
```JSON
{
    "data": [
        {
            // Transaction details
            "transaction_hash": "0xa1b2c3d4e5f6...",
            "block_number": 123456,
            "timestamp": 123456,
            "gas_used": 123456,
            "gas_price_wei": 1234567890, // 18 decimals from ether, 9 decimals from gwei
            "gas_price_quote": {
                "currency": "USDT",
                "value": 1234567890
            },
            // Decoded event + additional tags
            "sender": "0Xa1b2c3d4e5f6...",
            "recipient": "0Xa1b2c3d4e5f6...",
            "symbol_0": "USDC",
            "symbol_1": "WETH",
            "amount_0": 1000000000000000000,
            "amount_1": 2000000000000000000,
            "swap_price_0": 2000000000000000000, // amount_1 / amount_0 (18 decimals)
            "swap_price_1": 500000000000000000 // amount_0 / amount_1 (18 decimals)
        },
        ...
    ],
    "count": 200, // Response count
    "total": 1000, // Total count (to paginate)
}
```

Note: This endpoint returns an array of swaps as a transaction could comprise multiple swap events, be it across pools or within the same pool itself (The `id` in the database is `{transaction_hash}-{log_index}` to keep each transaction-event unique).

The query arguments are:

- `transaction_hash` - The `transaction_hash` to fetch events for.
- `from_block` - The earliest block to fetch events for.
- `to_block` - The last block to fetch events for.
- `contract_address` - optional filter by contract address.
- `limit` - Maximum number of events per response.
- `offset` - The number of events to skip (for pagination).

If the `transaction_hash` argument is provided, all other arguments are disregarded (i.e., a transaction-based query). Otherwise, the combination of the remaining arguments will be used for filtering the query.

<br><br>

## The Proxy

We setup a separate container running `Nginx` to proxy our requests to either the Historical Recording RPC API or the Interface REST API. This way, it appears as though we are using the same `interface` to perform both RPC and RESTful API calls, where in fact, they are separate services and could be running on different machines.

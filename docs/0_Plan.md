<div id="top"></div>

<!-- omit in toc -->
# The Plan

- [1. Overview](#1-overview)
  - [1.1. Core Requirements](#11-core-requirements)
  - [1.2. Considerations](#12-considerations)
    - [Keeping up to date with on-chain swaps](#keeping-up-to-date-with-on-chain-swaps)
  - [1.3. Steps](#13-steps)
  - [1.4. Observations](#14-observations)
  - [1.5. Assumptions](#15-assumptions)
- [2. Architecture](#2-architecture)
  - [2.1. Design and Scaling](#21-design-and-scaling)
  - [2.2. The Database](#22-the-database)
  - [2.3. The Interface](#23-the-interface)
  - [2.4. The Roadmap](#24-the-roadmap)
    - [Phase 1: Live-streaming of swap events](#phase-1-live-streaming-of-swap-events)
    - [Phase 2: Processing the event data](#phase-2-processing-the-event-data)
    - [Phase 3: Dockerizing and writing into database](#phase-3-dockerizing-and-writing-into-database)
    - [Phase 4: Historical recording of swap events](#phase-4-historical-recording-of-swap-events)
    - [Phase 5: API endpoints for fetching data](#phase-5-api-endpoints-for-fetching-data)


<br><br>

# 1. Overview

## 1.1. Core Requirements
[<u>back to contents</u>](#top)

- Design a system that records swaps involved in a given liquidity pool
    - Recording can occur in 2 settings:
        1. live - listening and recording them as they occur
        2. historical - lookback and record the historical transactions
    - Data recorded should include:
        1. Value of the gas used in the transaction, quoted in USDT
        2. The swap price
- Expose a RESTful API to:
    1. Query the required information
    2. Invoke the loading of historical data

<br><hr><br>

## 1.2. Considerations
[<u>back to contents</u>](#top)

### Keeping up to date with on-chain swaps

Generally speaking, this falls under 2 primary categories:
1. Scheduled queries from a blockchain indexer like `EtherScan`
    - This would involve querying the event logs between a `fromBlock` and `toBlock` for a given `address` and `topic`
    - This would be useful for historical recording but not ideal for live-recording since we have to first wait for EtherScan to index and record the event on their end
2. Streaming of events from a node provider like `Infura` through the 
    - This would involve setting up a websocket connection with the node provider to facilitate the `eth_subscribe` method
    - This only serves live-recording but is ideal for it since we get 'notified' of a swap on a contract we are listening to and can immediately 'react'

In both, events logs would be filtered by the following parameters:
- address - e.g. `"0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640"` (The ETH-USDC LP address)
- topic - e.g., `keccak256('Swap(address,address,int256,int256,uint160,uint128,int24)')` (`Swap` event for UniSwap LPs)

Note: we do not query for transactions directly since transactions with a liquidity pool are typically called through a router as internal transactions. We also do not want to only query for internal transactions from the router since we would have to filter after the fact and we would also be missing out on transactions called from other sources.

We will go with approach `2` for live recording since it is the simplest and probably the fastest without relying on blockchain indexers. Historical recording will still rely on approach `1`, where instead of scheduled, it is invoked via an RPC endpoint.

<br><hr><br>

## 1.3. Steps
[<u>back to contents</u>](#top)

- Live recording can be broken into 5 key steps:
    1. Stream the contract's swap events from the node provider
    2. Decoding the parameters of the events
    3. Tagging a value for the amount of gas used by the transaction, based on the price from a CEX
    4. Writing into a database
    5. Exposing a RESTful API endpoint that reads from the database

- Historical recording only differs in the first 2 steps:
    1. RPC endpoint to invoke the historical recording process
    2. Search for swap events within the specified time interval from the blockchain indexer

<br><hr><br>

## 1.4. Observations
[<u>back to contents</u>](#top)

- Dominated by I/O-bound tasks
    - e.g., fetching on-chain transactions, fetching prices from CEX(s)
    - CPU-bound tasks like decoding and simple arithmetic operations are mostly trivial
- Processing is inherently coupled with the type of the event
    - How we process a `Swap` event is specific to the swap event
        - e.g., Decoding the parameters of a `Swap` event is vastly different from that of `Mint`/`Burn` events.

<br><hr><br>

## 1.5. Assumptions
[<u>back to contents</u>](#top)

1. We assume that scalability is required across multiple liquidity pools and event contract types and event types
2. We assume the database is to be run on a different machine, shared by all the recorders
    - This stems from a reasonable assumption that the write throughput of a modern database is greater than the transaction throughput of a decentralized blockchain, even more so for a subset of transactions we are interested in recording
3. We assume each instance of the individual services are potentially running on separate machines
4. We assume that the maximum amount of processing requirement in the future is trivial enough to be performed on the same machine at least for one event from one contract
    - There are no intense cpu-bound processing that would constitute a bottleneck more than the I/O-bound nature of the tasks
        - e.g., decoding the bytes data of an event log
    - In the event where aggregated processing is to be required (e.g., computation on the combined data of multiple liqudity pools' swaps/mints), this can be pushed downstream to run be run on separate processes perhaps with load balancing mechanisms

<br><br><br>

# 2. Architecture

## 2.1. Design and Scaling
[<u>back to contents</u>](#top)

From our observations, we deduce that it makes little sense to separate the `streaming` and `processing` layers into separate processes, less so separate machines. This avoids unnecessary IPC latencies while keeping closely-coupled operations together. Scalability can be achieved still, through multiple instances catered for disjoint subsets of liquidity pools or events. For instance, suppose a machine can only accommodate the workload of streaming, processing, and recording for 2 liquidity pools. Then, we split the instances into something like this:

- Instance A: Records `Swap` events for `WETH-USDC` and `WBTC-WETH` pool 
- Instance B: Records `Swap` events for `1INCH-USDC` and `AAVE-WETH` pool
- Instance C: Records `Mint` events for `WETH-USDC` and `WBTC-WETH` pool 
- Instance D: Records `Mint` events for `1INCH-USDC` and `AAVE-WETH` pool

The redundancies will thus be the pricing of gas fees, where each instance has to fetch the price of the gas currency from a CEX. This is acceptable since:
  1. This is an I/O-bound task that can be concurrently performed while events are being streamed. For this reason, we can rely on Python for simplicity and speed of development without being constrained by the global interpreter lock (GIL).
  2. Centralized exchanges are generally performant enough to not be of concern

The requirements will be split into 3 main components:
- The Live Recorder
- The Historical Recorder
- The Interface -- comprises the API endpoints and a simple GUI

Due to the similarities between the Live Recorder and Historical Recorder, both will be from the same codebase, but with different entrypoints.

<br><hr><br>

## 2.2. The Database
[<u>back to contents</u>](#top)

Our requirements for the database are:
- Primary: one that supports the lookup of transactions via the transaction hash
- Secondary: one that also supports range-based lookups of transactions via timestamps/block heights since this would be a natural access-pattern albeit not a primary requirement

While SQL databases would be both a decent and probably a common choice here, we shall go with a NoSQL document-oriented database, sepcifically MongoDB, for the following reasons:
  1. Ease of use to facilitate the strict timeline where the `schema` could be evolving in this rushed development process
  2. We can simply represent the blockchain's data as they are, except having them decoded, practising some levels of dernomalization, since blockchain data are likely 1-time write operations without the need for updating.
  3. Useful enough to allow for indexing of fields in anticipation of future requirements (see secondary requirement)

A thing to note will be that we will be storing the numerical values except the `timestamp` and `block_height` fields as a string representation of integers to accommodate the large values (e.g. `uint256` would be a problem to store in MongoDB).


<br><hr><br>

## 2.3. The Interface
[<u>back to contents</u>](#top)

We will split the interface into three parts:

1. RESTful endpoints to fetch data from the database
2. RPC endpoints to invoke the historical recording process
3. Simply GUI to showcase and detail what we've built

We will be using Fast API to bootstrap our API service, also utilizing its integration with Swagger to simplify the fulfilment of one of the requirements for API documentation.

The RESTful endpoints will likely look like:

- `api/swaps?transaction_hash=0x12345...`
- `api/swaps?transaction_hash=0x12345...&event_id=uniswap-v3-pool-swap`
- `api/swaps?from_block=12345&to_block=54321`

The RPC endpoints will likely look like:

- `api/record-historical-events?category=swaps&contract_address=0x...&event_id=uniswap-v3-pool-swap`


<br><hr><br>


## 2.4. The Roadmap
[<u>back to contents</u>](#top)

### Phase 1: Live-streaming of swap events

We will first setup the stream with the node provider and ensure that it is reliable.

<br>

### Phase 2: Processing the event data

We will strategize our retrieval of transaction receipts and prices from the CEX, likely requiring some form of LRU-caching. These will be considered the primary processing that is required.

After this, we can start writing contract-event-specific processing for the Uniswap V3 Pool contract's Swap Event. This will handle the decoding of event data and some simple computations like getting the swap price. This part will be separate from the live-recording part so that it can be re-used for the historical-recording part.

<br>

### Phase 3: Dockerizing and writing into database

We will then dockerize the stream and setup a MongoDB container to actually record the processed data.

<br>

### Phase 4: Historical recording of swap events

After having a rough sense of the live streaming pipeline, we simply replicate the process, re-using our contract-event-specific handlers to handle the data in batch, retrieved from the blockchain indexer.

<br>

### Phase 5: API endpoints for fetching data

We will finally work on the API service to expose the RESTful and RPC endpoints, as well as a simple GUI to showcase the project.

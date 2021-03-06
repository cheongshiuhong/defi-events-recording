# Standard libraries
from typing import TypedDict


class EventLog(TypedDict):
    address: str
    topics: list[str]
    data: str
    blockNumber: str
    timeStamp: str
    gasPrice: str
    gasUsed: str
    logIndex: str
    transactionHash: str
    transactionIndex: str


class GasPriceQuote(TypedDict):
    currency: str
    value: str


class ProcessedLog(TypedDict):
    event_id: str
    transaction_hash: str
    log_index: int
    block_number: int
    timestamp: int
    gas_used: str
    gas_price_wei: str
    gas_price_quote: GasPriceQuote
    address: str
    topics: list[str]
    raw_data: str
    data: dict[str, str]

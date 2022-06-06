# Standard libraries
from typing import TypedDict


class EventLog(TypedDict):
    removed: bool
    logIndex: str
    transactionIndex: str
    transactionHash: str
    blockHash: str
    blockNumber: str
    address: str
    data: str
    topics: list[str]


class ListenerOutput(TypedDict):
    subscription_id: int
    event_log: EventLog


class TransactionReceipt(TypedDict):
    gasUsed: str
    effectiveGasPrice: str


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


class ProcessorOutput(TypedDict):
    subscription_id: int
    data: ProcessedLog

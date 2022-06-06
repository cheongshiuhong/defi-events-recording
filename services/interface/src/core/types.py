# Standard libraries
from typing import TypedDict


class GasPriceQuote(TypedDict):
    currency: str
    value: str


class EventLog(TypedDict):
    event_id: str
    transaction_hash: str
    block_number: int
    timestamp: int
    gas_used: str
    gas_price_wei: str
    gas_price_quote: GasPriceQuote
    address: str
    topics: list[str]
    raw_data: str
    data: dict[str, str]

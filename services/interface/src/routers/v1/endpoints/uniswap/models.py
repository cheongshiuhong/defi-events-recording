# 3rd party libraries
from pydantic import BaseModel


class GasPriceQuote(BaseModel):
    currency: str
    value: int


class UniswapV3PoolSwap(BaseModel):
    transaction_hash: str
    block_number: int
    timestamp: int
    gas_used: int
    gas_price_wei: int
    gas_price_quote: GasPriceQuote
    sender: str
    recipient: str
    symbol_0: str
    symbol_1: str
    amount_0: int
    amount_1: int
    swap_price_0: int
    swap_price_1: int


class UniswapV3PoolSwapResponse(BaseModel):
    data: list[UniswapV3PoolSwap]
    count: int
    total: int

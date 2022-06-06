# 3rd party libraries
from pydantic import BaseModel


class GasPriceQuote(BaseModel):
    currency: str
    value: int


class GasResponse(BaseModel):
    gas_used: int
    gas_price_wei: int
    gas_price_quote: GasPriceQuote

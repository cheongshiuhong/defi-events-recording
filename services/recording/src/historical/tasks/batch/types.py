# Standard libraries
from typing import TypedDict


class GasPricingConfig(TypedDict):
    gas_currency: str
    quote_currency: str


class BatchConfig(TypedDict):
    gas_pricing: GasPricingConfig

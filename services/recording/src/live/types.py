# Standard libraries
from typing import TypedDict


class SubscriptionConfig(TypedDict):
    contract_address: str
    event_id: str


SubscriptionsConfig = list[SubscriptionConfig]


class GasPricingConfig(TypedDict):
    gas_currency: str
    quote_currency: str


class StreamConfig(TypedDict):
    subscriptions: SubscriptionsConfig
    gas_pricing: GasPricingConfig

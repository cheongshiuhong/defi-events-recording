# 3rd party libraries
from eth_utils import keccak, encode_hex


UNISWAP_LP_SWAP_EVENT_SIGNATURE: str = (
    "Swap(address,address,int256,int256,uint160,uint128,int24)"
)
UNISWAP_LP_SWAP_EVENT_TOPIC: str = encode_hex(
    keccak(text=UNISWAP_LP_SWAP_EVENT_SIGNATURE)
)

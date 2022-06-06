# 3rd party libraries
from fastapi import APIRouter

# Code
from .endpoints.gas import gas_router
from .endpoints.uniswap.v3_pool import uniswap_v3_pool_router

v1_router = APIRouter()

v1_router.include_router(gas_router, prefix="/gas")
v1_router.include_router(uniswap_v3_pool_router, prefix="/uniswap/v3-pool")

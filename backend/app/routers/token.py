import os
from fastapi import APIRouter
from web3 import Web3

from ..schemas import TokenStats
from ..web3_client import read_pair_reserves

router = APIRouter(prefix="/token", tags=["token"])

TET_TOKEN_ADDRESS = os.getenv("TET_TOKEN_ADDRESS", "")
UNISWAP_V2_PAIR_ADDRESS = os.getenv("UNISWAP_V2_PAIR_ADDRESS", "")


@router.get("/stats", response_model=TokenStats)
def token_stats():
    """Every field here is either a fixed on-chain address or read live from the
    Uniswap pair's reserves. There is no page that shows manufactured price/volume
    numbers — if liquidity hasn't been added yet, this correctly returns nulls."""
    reserves = read_pair_reserves()

    price_eth = None
    liquidity_eth = None
    liquidity_tet = None
    if reserves and reserves["price_eth_per_tet"] is not None:
        price_eth = str(reserves["price_eth_per_tet"])
        liquidity_eth = str(Web3.from_wei(reserves["eth_reserve_wei"], "ether"))
        liquidity_tet = str(Web3.from_wei(reserves["tet_reserve_wei"], "ether"))

    return TokenStats(
        token_address=TET_TOKEN_ADDRESS,
        pair_address=UNISWAP_V2_PAIR_ADDRESS or None,
        price_eth=price_eth,
        liquidity_eth=liquidity_eth,
        liquidity_tet=liquidity_tet,
    )

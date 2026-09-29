import os
import json
from functools import lru_cache
from web3 import Web3

RPC_URL = os.getenv("RPC_URL", "")
TET_ESCROW_ADDRESS = os.getenv("TET_ESCROW_ADDRESS", "0x" + "0" * 40)
TET_TOKEN_ADDRESS = os.getenv("TET_TOKEN_ADDRESS", "0x" + "0" * 40)
UNISWAP_V2_PAIR_ADDRESS = os.getenv("UNISWAP_V2_PAIR_ADDRESS", "")

ESCROW_ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "id", "type": "uint256"}],
        "name": "getAgreement",
        "outputs": [
            {
                "components": [
                    {"internalType": "address", "name": "sender", "type": "address"},
                    {"internalType": "address", "name": "receiver", "type": "address"},
                    {"internalType": "address", "name": "arbiter", "type": "address"},
                    {"internalType": "address", "name": "token", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "uint256", "name": "createdAt", "type": "uint256"},
                    {"internalType": "uint256", "name": "deliveredAt", "type": "uint256"},
                    {"internalType": "uint8", "name": "status", "type": "uint8"},
                    {"internalType": "string", "name": "termsURI", "type": "string"},
                ],
                "internalType": "struct TetEscrow.Agreement",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "_reserve0", "type": "uint112"},
            {"name": "_reserve1", "type": "uint112"},
            {"name": "_blockTimestampLast", "type": "uint32"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "type": "function"},
]


@lru_cache
def get_w3() -> Web3:
    if not RPC_URL:
        raise RuntimeError("RPC_URL is not configured (set it in backend/.env)")
    return Web3(Web3.HTTPProvider(RPC_URL))


def get_escrow_contract():
    w3 = get_w3()
    return w3.eth.contract(address=Web3.to_checksum_address(TET_ESCROW_ADDRESS), abi=ESCROW_ABI)


def read_agreement_onchain(onchain_id: int) -> dict:
    """Read the ground-truth state of an agreement directly from the contract —
    the off-chain DB row is a cache for fast UI reads, this is the source of truth."""
    c = get_escrow_contract()
    result = c.functions.getAgreement(onchain_id).call()
    keys = ["sender", "receiver", "arbiter", "token", "amount", "createdAt", "deliveredAt", "status", "termsURI"]
    return dict(zip(keys, result))


def read_pair_reserves() -> dict | None:
    """Real, live liquidity reserves from the Uniswap V2 pair — used for the
    token-stats endpoint. Returns None if no pair address is configured yet
    (e.g. before liquidity has been added)."""
    if not UNISWAP_V2_PAIR_ADDRESS:
        return None
    w3 = get_w3()
    pair = w3.eth.contract(address=Web3.to_checksum_address(UNISWAP_V2_PAIR_ADDRESS), abi=PAIR_ABI)
    reserve0, reserve1, _ = pair.functions.getReserves().call()
    token0 = pair.functions.token0().call()
    tet_is_token0 = token0.lower() == TET_TOKEN_ADDRESS.lower()
    tet_reserve, eth_reserve = (reserve0, reserve1) if tet_is_token0 else (reserve1, reserve0)
    return {
        "tet_reserve_wei": tet_reserve,
        "eth_reserve_wei": eth_reserve,
        "price_eth_per_tet": (eth_reserve / tet_reserve) if tet_reserve else None,
    }

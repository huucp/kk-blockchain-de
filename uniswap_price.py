import json
import time

from web3 import Web3
from cake_price import save_to_sql

ETHER = 10 ** 18

USDT = '0xdac17f958d2ee523a2206206994597c13d831ec7'
WETH = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
WBTC = '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599'
UNI = '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984'
ROUTER_ADDRESS = Web3.toChecksumAddress('0x10ed43c718714eb63d5aa57b78b54704e256024e')

web3 = Web3(Web3.HTTPProvider('https://eth-mainnet.alchemyapi.io/v2/LO7hoYZP-ekHltipWjayoHmneEV9pgGp'))
FACTORY = web3.toChecksumAddress('0x1F98431c8aD98523631AE4a59f267346ea31F984')

with open("abi/uni_price.json") as f:
    ABI = json.load(f)


def get_price(token):
    token0 = web3.toChecksumAddress(token)
    token1 = web3.toChecksumAddress(USDT)

    decimal0 = web3.eth.contract(address=token0, abi=ABI).functions.decimals().call()
    decimal1 = web3.eth.contract(address=token1, abi=ABI).functions.decimals().call()
    pair = web3.eth.contract(address=FACTORY, abi=ABI).functions.getPool(token0, token1, 3000).call()
    pair_contract = web3.eth.contract(address=pair, abi=ABI)
    pool_balance = pair_contract.functions.slot0().call()
    pricex96 = pool_balance[0]
    return (pricex96 * pricex96 * (10 ** (decimal0 - decimal1))) / (2 ** 192)


if __name__ == '__main__':
    save_to_sql("ETH", get_price(WETH), "uniswap")
    save_to_sql("BTC", get_price(WBTC), "uniswap")
    save_to_sql("UNI", get_price(UNI), "uniswap")

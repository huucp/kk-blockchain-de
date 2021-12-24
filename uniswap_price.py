import json
import time

from web3 import Web3

ETHER = 10 ** 18

USDT = '0xdac17f958d2ee523a2206206994597c13d831ec7'
WETH = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
ROUTER_ADDRESS = Web3.toChecksumAddress('0x10ed43c718714eb63d5aa57b78b54704e256024e')

web3 = Web3(Web3.HTTPProvider('https://eth-mainnet.alchemyapi.io/v2/LO7hoYZP-ekHltipWjayoHmneEV9pgGp'))


with open("abi/uni_price.json") as f:
    ABI = json.load(f)

if __name__ == '__main__':
    FACTORY = web3.toChecksumAddress('0x1F98431c8aD98523631AE4a59f267346ea31F984')

    token0 = web3.toChecksumAddress(WETH)
    token1 = web3.toChecksumAddress(USDT)

    decimal0 = web3.eth.contract(address=token0, abi=ABI).functions.decimals().call()
    decimal1 = web3.eth.contract(address=token1, abi=ABI).functions.decimals().call()
    # allPair = web3.eth.contract(address=CAKE_FACTORY_V2, abi=ABI).functions.allPairs(100).call()
    # print(allPair)
    pair = web3.eth.contract(address=FACTORY, abi=ABI).functions.getPool(token0, token1, 500).call()
    pair_contract = web3.eth.contract(address=pair, abi=ABI)
    start = round(time.time() * 1000)
    pool_balance = pair_contract.functions.slot0().call()
    pricex96 = pool_balance[0]
    price = (pricex96 * pricex96 * (10 ** (decimal0 - decimal1))) / (2 ** 192)
    end = round(time.time() * 1000)
    print(f"1 WETH = {price} USDT with duration {end-start}ms")

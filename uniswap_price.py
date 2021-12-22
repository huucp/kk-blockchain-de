import json

from web3 import Web3
from web3.middleware import geth_poa_middleware  # Needed for Binance

from json import loads
from decimal import Decimal

ETHER = 10 ** 18

USDT = '0xdac17f958d2ee523a2206206994597c13d831ec7'
WETH = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
ROUTER_ADDRESS = Web3.toChecksumAddress('0x10ed43c718714eb63d5aa57b78b54704e256024e')

# web3 = Web3(Web3.HTTPProvider('https://bsc-dataseed1.binance.org:443'))
# web3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/a9cd5560216d45af97d3503214706d60'))
web3 = Web3(Web3.HTTPProvider('https://eth-mainnet.alchemyapi.io/v2/LO7hoYZP-ekHltipWjayoHmneEV9pgGp'))
# web3.middleware_onion.inject(geth_poa_middleware, layer=0)  # Again, this is needed for Binance, not Ethirium


with open("abi/uni_price.json") as f:
    ABI = json.load(f)


def get_price(token, decimals, pair_contract, is_reversed, is_price_in_peg):
    (reserve0, reserve1, blockTimestampLast) = pair_contract.functions.getReserves().call()

    print(reserve0, reserve1, blockTimestampLast)

    if is_reversed:
        peg_reserve = reserve0
        token_reserve = reserve1
    else:
        peg_reserve = reserve1
        token_reserve = reserve0

    print(f'is reversed: {is_reversed}')

    if token_reserve and peg_reserve:
        if is_price_in_peg:
            # CALCULATE PRICE BY TOKEN PER PEG
            price = (Decimal(token_reserve) / 10 ** decimals) / (Decimal(peg_reserve) / ETHER)
        else:
            # CALCULATE PRICE BY PEG PER TOKEN
            price = (Decimal(peg_reserve) / ETHER) / (Decimal(token_reserve) / 10 ** decimals)

        return price

    return Decimal('0')


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
    pool_balance = pair_contract.functions.slot0().call()
    print(pool_balance)
    pricex96 = pool_balance[0]
    print(pricex96, decimal0, decimal1)
    price = (pricex96 * pricex96 * (10 ** (decimal0 - decimal1))) / (2 ** 192)
    print(price)

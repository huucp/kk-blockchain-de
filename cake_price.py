import time
from decimal import Decimal
from json import loads
from web3 import Web3

ETHER = 10 ** 18

WBNB = '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'
BUSD = '0xe9e7cea3dedca5984780bafc599bd69add087d56'
ADA = '0x3ee2200efb3400fabb9aacf31297cbdd1d435d47'
CAKE_ROUTER_V2 = Web3.toChecksumAddress('0x10ed43c718714eb63d5aa57b78b54704e256024e')

web3 = Web3(Web3.HTTPProvider('https://bsc-dataseed1.binance.org:443'))

ABI = loads(
    '[{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],'
    '"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"token0","outputs":[{'
    '"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view",'
    '"type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"",'
    '"type":"address"}],"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{'
    '"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],'
    '"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,'
    '"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"getReserves","outputs":[{'
    '"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1",'
    '"type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":false,'
    '"stateMutability":"view","type":"function"},'
    '{"constant":true,"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"allPairs","outputs":[{'
    '"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view",'
    '"type":"function"},{"constant":true,"inputs":[],"name":"allPairsLength","outputs":[{"internalType":"uint256",'
    '"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]')


# with open("pancake_router.json") as f:
#     ABI = json.load(f)


def get_price(decimals, pair_contract, is_reversed, is_price_in_peg):
    (reserve0, reserve1, blockTimestampLast) = pair_contract.functions.getReserves().call()

    if is_reversed:
        peg_reserve = reserve0
        token_reserve = reserve1
    else:
        peg_reserve = reserve1
        token_reserve = reserve0

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
    CAKE_FACTORY_V2 = web3.eth.contract(address=CAKE_ROUTER_V2, abi=ABI).functions.factory().call()

    token0 = web3.toChecksumAddress(BUSD)
    token1 = web3.toChecksumAddress(ADA)
    pair = web3.eth.contract(address=CAKE_FACTORY_V2, abi=ABI).functions.getPair(token0, token1).call()
    print(pair)
    pair_contract = web3.eth.contract(address=pair, abi=ABI)
    is_reversed = pair_contract.functions.token0().call() == token1
    decimals = web3.eth.contract(address=token0, abi=ABI).functions.decimals().call()
    is_price_in_peg = True

    start = round(time.time() * 1000)
    price = get_price(decimals, pair_contract, is_reversed, True)
    end = round(time.time() * 1000)
    print(f"1 ADA = {price} BUSD with duration {end - start} ms")


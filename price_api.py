import json
import time
from decimal import Decimal

from flask import Flask, url_for
from web3 import Web3

from pair import Pair

app = Flask(__name__)
DEX_LIST = ["pancake", "uniswap"]
COIN_LIST = ["ada", "eth", "cake", "uni"]
CAKE_COINS = {
    "ada": "0x1E249DF2F58cBef7EAc2b0EE35964ED8311D5623"
}
DECIMALS = {
    "ada": 18
}
ETHER = 10 ** 18

cake_w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed1.binance.org:443'))
with open('abi/cake_price.json') as f:
    cake_abi = json.load(f)

uni_w3 = Web3(Web3.HTTPProvider('https://eth-mainnet.alchemyapi.io/v2/LO7hoYZP-ekHltipWjayoHmneEV9pgGp'))
with open("abi/uni_price.json") as f:
    uni_abi = json.load(f)


@app.route("/health")
def health():
    ok = {
        "code": 200
    }
    return ok


@app.route("/<dex>/<coin>")
def price(dex, coin):
    if dex not in DEX_LIST or coin not in COIN_LIST:
        return {
            "code": 400,
            "msg": "not support"
        }

    return get_pancake_price(coin)


def get_pancake_price(coin: str):
    if coin not in CAKE_COINS:
        return {
            "code": 400,
            "msg": "not support"
        }
    pair_address = Web3.toChecksumAddress(CAKE_COINS[coin])
    pair_contract = cake_w3.eth.contract(address=pair_address, abi=cake_abi)

    start = round(time.time() * 1000)
    (reserve0, reserve1, blockTimestampLast) = pair_contract.functions.getReserves().call()
    peg_reserve = reserve1
    token_reserve = reserve0

    if token_reserve and peg_reserve:
        p = (Decimal(peg_reserve) / ETHER) / (Decimal(token_reserve) / 10 ** DECIMALS[coin])
        end = round(time.time() * 1000)
        return {
            "code": 200,
            "data": {
                "protocol_name": "pancake",
                "token_name": coin,
                "time_record": start,
                "connection_time": end - start,
                "price": p
            }
        }
    else:
        return {
            "code": 500,
            "msg": "internal server error"
        }

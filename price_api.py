import json
import time
from decimal import Decimal

from flask import Flask, url_for
from web3 import Web3

from pair import Pair

UNISWAP = "uniswap"

PANCAKE = "pancake"

app = Flask(__name__)
DEX_LIST = ["pancake", "uniswap"]
CAKE_COIN_LIST = ["ada", "eth", "cake", "btc"]
CAKE_PAIRS = {
    "ada": "0x1E249DF2F58cBef7EAc2b0EE35964ED8311D5623",
    "eth": "0x7213a321F1855CF1779f42c0CD85d3D95291D34C",
    "cake": "0x804678fa97d91B974ec2af3c843270886528a9E6",
    "btc": "0xF45cd219aEF8618A92BAa7aD848364a158a24F33"
}
UNI_COIN_LIST = ["eth", "uni", "btc"]
UNI_PAIRS = {
    "eth": "0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36",
    "uni": "0x3470447f3CecfFAc709D3e783A307790b0208d60",
    "btc": "0x9Db9e0e53058C89e5B94e29621a205198648425B"
}

DECIMALS = {
    "ada": 18,
    "cake": 18,
    "eth": 18,
    "btc": 18,
    "uni": 18,
    "usdt": 6,
    "busd": 18
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
    if dex not in DEX_LIST or (dex == ("%s" % PANCAKE) and coin not in CAKE_COIN_LIST) or (
            dex == ("%s" % UNISWAP) and coin not in UNI_COIN_LIST):
        return {
            "code": 400,
            "msg": "not support"
        }
    if dex == PANCAKE:
        return get_pancake_price(coin)
    if dex == UNISWAP:
        return get_uni_price(coin)


def get_pancake_price(coin: str):
    if coin not in CAKE_PAIRS:
        return {
            "code": 400,
            "msg": "not support"
        }
    pair_address = Web3.toChecksumAddress(CAKE_PAIRS[coin])
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
                "price": float(p)
            }
        }
    else:
        return {
            "code": 500,
            "msg": "internal server error"
        }


def get_uni_price(coin: str):
    start = round(time.time() * 1000)
    token0 = uni_w3.toChecksumAddress(coin)

    pair = UNI_PAIRS[coin]
    pair_contract = uni_w3.eth.contract(address=pair, abi=uni_abi)
    pool_balance = pair_contract.functions.slot0().call()
    pricex96 = pool_balance[0]
    p = (pricex96 * pricex96 * (10 ** (DECIMALS[coin] - DECIMALS["usdt"]))) / (2 ** 192)
    end = round(time.time() * 1000)
    return {
        "code": 200,
        "data": {
            "protocol_name": "pancake",
            "token_name": coin,
            "time_record": start,
            "connection_time": end - start,
            "price": float(p)
        }
    }

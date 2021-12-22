import datetime
import json
import logging
import time
import pymysql
import pandas as pd
import tqdm as tqdm
from web3 import HTTPProvider, Web3

from web3.datastructures import AttributeDict
from web3.middleware import geth_poa_middleware

from event_scanner import EventScanner
from event_scanner_state import EventScannerState
from pair import Pair
from sqlalchemy import create_engine


class CakeEventScanner(EventScannerState):

    def __init__(self, pair: Pair):
        self.last_block = 0
        self.last_save = 0
        self.pair = pair
        self.swap_events = pd.DataFrame.empty
        self.deposit_events = pd.DataFrame.empty
        self.connection = pymysql.connect(host='localhost',
                                          user='root',
                                          password='root',
                                          database='kk',
                                          cursorclass=pymysql.cursors.DictCursor)
        self.sql_engine = create_engine('mysql+pymysql://root:root@locahost/kk')

    def reset(self):
        with self.connection:
            with self.connection.cursor() as cursor:
                query = "insert into last_block_scan (address,block) values (%s,0)"
                cursor.execute(query, self.pair.address)
            self.connection.commit()

    def restore(self):
        with self.connection:
            with self.connection.cursor() as cursor:
                query = "select block from last_block_scan where address=%s"
                cursor.execute(query, self.pair.address)
                ret = cursor.fetchone()
                if ret is not None:
                    self.last_block = ret['block']

    def save(self):
        with self.sql_engine.connect() as connection:
            deposit_table = f"dex_{self.pair.dex}_{self.pair.name}_deposit_data"
            self.deposit_events.to_sql(deposit_table, connection, if_exists='append')
            self.deposit_events = self.deposit_events.iloc[0:0]

            swap_table = f"dex_{self.pair.dex}_{self.pair.name}_swap_data"
            self.swap_events.to_sql(swap_table, connection, if_exists='append')
            self.swap_events = self.swap_events.iloc[0:0]

        with self.connection:
            with self.connection.cursor() as cursor:
                query = "update last_block_scan set block=%s where address=%s"
                cursor.execute(query, (self.last_block, self.pair.address))
            self.connection.commit()
        self.last_save = time.time()

    def get_last_scanned_block(self) -> int:
        return self.last_block

    def start_chunk(self, block_number: int):
        pass

    def end_chunk(self, block_number: int):
        self.last_block = block_number
        if time.time() - self.last_save > 60:
            self.save()

    def process_event(self, block_when: datetime.datetime, event: AttributeDict) -> object:
        """Record a ERC-20 event in our database."""
        # Events are keyed by their transaction hash and log index
        # One transaction may contain multiple events
        # and each one of those gets their own log index

        print(event)

        log_index = event.logIndex  # Log index within the block
        # transaction_index = event.transactionIndex  # Transaction index within the block
        tnx_hash = event.transactionHash.hex()  # Transaction hash
        block_number = event.blockNumber

        # Convert ERC-20 Transfer event to our internal format
        args = event["args"]
        event_name = event["event"].lower()
        if event_name == 'mint' or event_name == 'burn':
            event = {
                "block": block_number,
                "tnx_hash": tnx_hash,
                "log_index": log_index,
                "amount0": args["amount0"],
                "amount1": args["amount1"],
                "sender": args["sender"],
                "timestamp": block_when.isoformat(),
            }
            self.deposit_events.append(event)
        elif event_name == 'swap':
            event = {
                "block": block_number,
                "tnx_hash": tnx_hash,
                "log_index": log_index,
                "timestamp": block_when.isoformat(),
            }
            self.swap_events.append(event)

        # Return a pointer that allows us to look up this event later if needed
        return f"{block_number}-{tnx_hash}-{log_index}"

    def delete_data(self, since_block: int) -> int:
        pass


if __name__ == '__main__':
    api_url = 'https://bsc-dataseed1.binance.org:443'

    # Enable logs to the stdout.
    # DEBUG is very verbose level
    logging.basicConfig(level=logging.INFO)

    provider = HTTPProvider(api_url)

    # Remove the default JSON-RPC retry middleware
    # as it correctly cannot handle eth_getLogs block range
    # throttle down.
    provider.middlewares.clear()

    web3 = Web3(provider)
    if api_url.find("binance") != -1:
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    # Prepare stub ERC-20 contract object
    with open('abi/cake_pair.json') as f:
        abi = json.load(f)
    contract = web3.eth.contract(abi=abi)

    # Restore/create our persistent state
    ada_busd_pair = Pair("ada_busd", '0x1E249DF2F58cBef7EAc2b0EE35964ED8311D5623', 'pancake')

    state = CakeEventScanner(ada_busd_pair)
    state.restore()

    # chain_id: int, web3: Web3, abi: dict, state: EventScannerState, events: List, filters: {}, max_chunk_scan_size: int=10000
    scanner = EventScanner(
        web3=web3,
        contract=contract,
        state=state,
        events=[contract.events.Swap],
        filters={"address": web3.toChecksumAddress(ada_busd_pair.address)},
        # How many maximum blocks at the time we request from JSON-RPC
        # and we are unlikely to exceed the response size limit of the JSON-RPC server
        max_chunk_scan_size=5000
    )

    # Assume we might have scanned the blocks all the way to the last Ethereum block
    # that mined a few seconds before the previous scan run ended.
    # Because there might have been a minor Etherueum chain reorganisations
    # since the last scan ended, we need to discard
    # the last few blocks from the previous scan results.
    chain_reorg_safety_blocks = 10
    scanner.delete_potentially_forked_block_data(state.get_last_scanned_block() - chain_reorg_safety_blocks)

    # Scan from [last block scanned] - [latest ethereum block]
    # Note that our chain reorg safety blocks cannot go negative
    start_block = max(state.get_last_scanned_block() - chain_reorg_safety_blocks, 0)
    end_block = scanner.get_suggested_scan_end_block()
    blocks_to_scan = end_block - start_block

    print(f"Scanning events from blocks {start_block} - {end_block}")

    # Render a progress bar in the console
    start = time.time()
    with tqdm(total=blocks_to_scan) as progress_bar:
        def _update_progress(start, end, current, current_block_timestamp, chunk_size, events_count):
            if current_block_timestamp:
                formatted_time = current_block_timestamp.strftime("%d-%m-%Y")
            else:
                formatted_time = "no block time available"
            progress_bar.set_description(
                f"Current block: {current} ({formatted_time}), blocks in a scan batch: {chunk_size}, events processed "
                f"in a batch {events_count}")
            progress_bar.update(chunk_size)


        # Run the scan
        result, total_chunks_scanned = scanner.scan(start_block, end_block, progress_callback=_update_progress)

    state.save()
    duration = time.time() - start
    print(
        f"Scanned total {len(result)} Transfer events, in {duration} seconds, total {total_chunks_scanned} chunk "
        f"scans performed")
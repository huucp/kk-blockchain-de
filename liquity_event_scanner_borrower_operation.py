import json
import logging
import time

from tqdm import tqdm
from web3 import HTTPProvider, Web3
from web3.middleware import geth_poa_middleware

from event_scanner import EventScanner
from liquity_event_scanner import LiquityEventScanner
from pair import Pair

if __name__ == '__main__':
    api_url = 'https://eth-mainnet.alchemyapi.io/v2/LO7hoYZP-ekHltipWjayoHmneEV9pgGp'

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
    with open('abi/liquity_event.json') as f:
        abi = json.load(f)
    contract = web3.eth.contract(abi=abi)

    contract_address = Pair("BorrowerOperation", '0x24179cd81c9e782a4096035f7ec97fb8b783e007', 'liquity')

    state = LiquityEventScanner(contract_address)
    state.restore()

    # chain_id: int, web3: Web3, abi: dict, state: EventScannerState, events: List, filters: {}, max_chunk_scan_size: int=10000
    scanner = EventScanner(
        web3=web3,
        contract=contract,
        state=state,
        events=[contract.events.TroveUpdated],
        filters={"address": web3.toChecksumAddress(contract_address.address)},
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

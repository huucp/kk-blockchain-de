from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine
from web3 import Web3

TABLE_NAME = "lending_liquity_eth_lending_data.sql"

sql_engine = create_engine('mysql+pymysql://root:root@localhost/kk')

BORROWER_OPERATIONS = ["openTrove", "closeTrove", "adjustTrove"]
TROVE_MANAGER = ["applyPendingRewards", "liquidateInNormalMode", "liquidateInRecoveryMode", "redeemCollateral"]

ETH = 10 ** 18
LUSD = 10 ** 18

web3 = Web3(Web3.HTTPProvider('https://eth-mainnet.alchemyapi.io/v2/LO7hoYZP-ekHltipWjayoHmneEV9pgGp'))


def get_all_update():
    with sql_engine.connect() as connection:
        df = pd.read_sql(
            sql="select borrower,block,log_index,debt, collateral, stake, operation, contract_name,tnx_hash from "
                "dex_liquity_trove_updated_event "
                "order by borrower, block asc, log_index asc", con=connection)
        return df


def truncate_db():
    with sql_engine.connect() as connection:
        connection.execute("truncate table %s" % TABLE_NAME)


def save(data_frame):
    with sql_engine.connect() as connection:
        data_frame.to_sql(TABLE_NAME, connection, if_exists='append', index=False)
        return data_frame.iloc[0:0]


def get_eth_price(block_number):
    # get eth price from block number
    return 4000


if __name__ == '__main__':
    transaction = get_all_update()
    current_borrower = ''
    tnxs = pd.DataFrame()

    last_debt = 0
    last_coll = 0
    truncate_db()

    for index, row in transaction.iterrows():
        if row['contract_name'] == 'BorrowerOperation':
            operation = BORROWER_OPERATIONS[int(row['operation'])]
        elif row['contract_name'] == 'TroveManager':
            operation = TROVE_MANAGER[int(row['operation'])]
        else:
            operation = 'N/A'

        if len(current_borrower) == 0:
            current_borrower = row['borrower']
        if current_borrower != row['borrower']:
            tnxs = save(tnxs)
            current_borrower = row['borrower']
            last_coll = 0
            last_debt = 0

        block = row['block']
        log_index = row['log_index']
        debt = row['debt']
        coll = row['collateral']
        stake = row['stake']
        ts = datetime.fromtimestamp(web3.eth.get_block(int(block)).timestamp)
        eth_price = get_eth_price(block)
        print(row['tnx_hash'], last_debt, debt, last_coll,coll)

        if operation == 'openTrove':
            tnx = {
                "action_type": "open_account",
                "collateral_change": coll,
                "debt_change": debt,
                "time_recorded": ts,
                "market_price": eth_price
            }
        elif operation == 'closeTrove':
            tnx = {
                "action_type": "close_account",
                "collateral_change": -1 * last_coll,
                "debt_change": -1 * last_debt,
                "time_recorded": ts,
                "market_price": eth_price
            }
        elif operation == 'adjustTrove':
            if last_debt != debt or last_coll != coll:
                # repay
                if last_debt > debt and last_coll == coll:
                    tnx = {
                        "action_type": "repay",
                        "collateral_change": 0,
                        "debt_change": debt - last_debt,
                        "time_recorded": ts,
                        "market_price": eth_price
                    }
                # withdraw lusd
                elif last_coll == coll and last_debt < debt:
                    tnx = {
                        "action_type": "withdraw_lusd",
                        "collateral_change": 0,
                        "debt_change": (coll - last_coll) * eth_price,
                        "time_recorded": ts,
                        "market_price": eth_price
                    }
                elif last_debt == debt and last_coll > coll:  # withdraw collateral
                    tnx = {
                        "action_type": "withdraw_collateral",
                        "collateral_change": coll - last_coll,
                        "debt_change": 0,
                        "time_recorded": ts,
                        "market_price": eth_price
                    }
                else:
                    tnx = {
                        "action_type": "adjust_account",
                        "collateral_change": coll - last_coll,
                        "debt_change": debt - last_debt,
                        "time_recorded": ts,
                        "market_price": eth_price
                    }
            elif operation == "applyPendingRewards":
                tnx = {
                    "action_type": "reward",
                    "collateral_change": coll - last_coll,
                    "debt_change": debt - last_debt,
                    "time_recorded": ts,
                    "market_price": eth_price
                }
            elif operation == 'liquidateInNormalMode' or operation == 'liquidateInRecoveryMode':
                tnx = {
                    "action_type": "liquidation",
                    "collateral_change": coll - last_coll,
                    "debt_change": debt - last_debt,
                    "time_recorded": ts,
                    "market_price": eth_price
                }
            elif operation == 'redeemCollateral':
                tnx = {
                    "action_type": "redeem",
                    "collateral_change": coll - last_coll,
                    "debt_change": debt - last_debt,
                    "time_recorded": ts,
                    "market_price": eth_price
                }
        last_debt = debt
        last_coll = coll
        tnxs = tnxs.append(tnx, ignore_index=True)

    save(tnxs)  # last commit

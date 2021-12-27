# kk-blockchain-de

`NOTICE: this project build on Linux platform, it should be run on MacOS.`

## How to install
### Python package
Install python packages with command 

`
pip install -r requirements.txt
`


### Database setup (MySQL)
In this project, I use MySQL as the main database to save the data which is crawled from on-chain.

- Set up the username/password : 'root/root'
- Create the database 'kk'
- Run all the sql file to create the tables.
- Dexes data tables should be auto-generated from code.


## How to use project
### Price data
There are two dexes so I separate to two python file: uniswap_price and cake_price. Both file have functions to get price from on chain data then save to MySQL. To update price periodically, we should use cron command or some workflow management tool such as airflow.

The price data will be saved at the table `token_price_data`
### Instant price API
Run the bash file `api.sh` the open the link `localhost:5000/health` to check API health.

Use this path to get price from API `locahost:5000/{dex}/{token}`

The dex should be one of two: `pancake` or `uniswap`.
The API can get price data of `uni, eth, btc` token in `uniswap` platform, `ada,eth,cake,btc` token in `pancake` platform.

For example to get the price of `ada` in `pancake` we use the command:

`curl http://localhost:5000/pancake/ada`

### Dexes data
#### Deposit data
Run `python3 cake_event_scanner.py token0Name_token1Name pair_address` to get deposit/swap data from pancake of one pair.

Run `python3 unit_event_scanner.py token0Name_token1Name pair_address` to get deposit/swap data from uniswap of one pair.


### Lending project: Liquity
Liquity is a decentralized borrowing protocol that allows you to draw 0% interest loans against Ether used as collateral. Loans are paid out in LUSD - a USD pegged stablecoin, and need to maintain a minimum collateral ratio of only 110%.

At the moment, the liquity only support ETH as collateral and LUSD as the debt.

Because the Liquity platform only publish the TroveUpdated (when there is the change from Trove - LiquityAccount). There are many actions that can lead to this event:
- OpenTrove
- AdjustTrove
- CloseTrove
- Repay
- WithdrawLUSD
- WithdrawCollateral
- RedeemCollateral
- Liquidate
- ApplyReward

So, this project will read the on-chain data TroveUdpated event from TroveManager and BorrowerOperations. After that, we can extract the change from Trove as the volume of lending platform.
To grab the volume data, please run the script `liquity.sh`. We can set up the flow by using the cron tab on Linux or using airflow for better workflow management.

```Interest rate: according to the Liquitty, the borrowing is [interest-free](https://docs.liquity.org/faq/borrowing#how-can-the-protocol-offer-interest-free-borrowing)``


## Further work:
- Liquity do not provide the market price data at the event, so we need to build the lookup table which return ETH price data with the block number.
- Should use airflow as workflow management instead of crontab.
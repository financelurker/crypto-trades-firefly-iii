# Supported Exchanges

So you know the API of your exchange and are interested in extending this service to work with a new exchange which isn't supported by now?
This documentation gives you all you need to know to add another supported exchange to the library.

## How to use supported exchanges
- Binance (formerly known as [binance-firefly-iii](https://github.com/financelurker/binance-firefly-iii))
  - "notes identifier": "crypto-trades-firefly-iii:binance"
  - Environmental Variables
    - BINANCE_API_KEY
    - BINANCE_API_SECRET

In the doing:
- Kraken
- coinbase
- KuCoin
- bitpanda
- bitfinex
- HitBTC
- Crypto.com
- Nexo
- PayPal
- ...

## How to add supported exchanges

### Overview

[Big Picture](../../../plantuml/exchanges_overview.svg)
<img src="../../plantuml/exchanges_overview.svg">

### Implementation

To add a new exchange as data source you need to implement two classes which super classes are [declared in here](exchange_interface.py):
- **AbstractCryptoExchangeClientModule** which is the meta class for your exchange module. It defines meta information and access to the client implementation
  - **is_enabled(self) -> bool**
    - Checks the environmental variables which are needed to run this exchange plugin.
  - **get_exchange_name(self) -> str**
    - Returns the name of the exchange.
  - **get_exchange_client(self) -> AbstractCryptoExchangeClient**
    - Creates and returns an instance of the appropriate AbstractCryptoExchangeClient sub-class.
  - **static get_instance() -> AbstractCryptoExchangeClientModule**
    - Creates and returns an instance of that very module class.
- **AbstractCryptoExchangeClient** is the specific implementation class for the exchange API which provides
  - **get_trading_pairs(self, list_of_symbols_and_codes: List[str]) -> List[TradingPair]**
    - Description: Checks all eligible trading products on the exchange and matches them with the list of currency symbols and codes your Firefly-III accounts support and has asset accounts already set up.
    - Parameters:
      - **list_of_symbols_and_codes: List[str]:** This parameter contains a list of all currency symbols and codes from eligible Firefly-III accounts. Example: ["BTC", "₿", "ETH", "Ξ", "EUR", "€", "USD", "$"]
  - **get_trades(self, from_timestamp: int, to_timestamp: int, list_of_trading_pairs: List[TradingPair]) -> List[TradeData]**
    - Description: Gets and returns all trades of the account (for a given time period).
    - Parameters:
      - **from_timestamp: int:** a timestamp in milli-seconds from where trades should be considered for import
      - **to_timestamp: int:** a timestamp in milli-seconds to where trades should be considered for import
      - **list_of_trading_pairs: List[TradingPair]:** The trading pairs for which the exchange has eligible products. This is the response from the get_trading_pairs call.
  - **get_savings_interests(self, from_timestamp: int, to_timestamp: int, list_of_assets: List[str]) -> List[InterestData]**
    - Description: a method to get all received interest (for a given time period)
    - Parameters:
      - **from_timestamp: int:** a timestamp in milli-seconds from where received interest should be considered for import
      - **to_timestamp: int:** a timestamp in milli-seconds to where received interest should be considered for import
      - **list_of_assets: List[str]:** a list of assets where there are eligible asset accounts within Firefly-III and received interest can be imported to. Example: ["BTC", "ETH", "EUR", "USD"]
  - **get_withdrawals(self, from_timestamp: int, to_timestamp: int, list_of_assets: List[str]) -> List[WithdrawalData]**
    - Description: Gets and returns all withdrawals from that exchange
    - Parameters:
      - **from_timestamp: int:** a timestamp in milli-seconds from where withdrawals should be considered for import
      - **to_timestamp: int:** a timestamp in milli-seconds to where withdrawals should be considered for import
      - **list_of_assets: List[str]:** a list of assets where there are eligible asset accounts within Firefly-III and withdrawals can be imported to. Example: ["BTC", "ETH", "EUR", "USD"]
  - **get_deposits(self, from_timestamp: int, to_timestamp: int, list_of_assets: List[str]) -> List[DepositData]**
    - Description: Gets and returns all deposits to that exchange
    - Parameters:
      - **from_timestamp: int:** a timestamp in milli-seconds from where deposits should be considered for import
      - **to_timestamp: int:** a timestamp in milli-seconds to where deposits should be considered for import
      - **list_of_assets: List[str]:** a list of assets where there are eligible asset accounts within Firefly-III and deposits can be imported to. Example: ["BTC", "ETH", "EUR", "USD"]

When you have those classes implemented add your module (*.py file) to [the impl package](impls). Implementations of AbstractCryptoExchangeClientModule in that package will be picked up automatically during initialization phase of the service.

If you want your exchange implementation added to this repository, just create a pull request with your exchange implementation. When you add the needed environmental variables declared by your exchange plugin the service will automatically connect to that exchange and import data.

Pull requests containing writing actions to the exchange will probably be rejected - as all exchange interactions have to be of read nature.

### Exceptions and Exchange Outages

#### Exchange services under maintenance

For the case being that the configured crypto exchange is under maintenance you can catch that Exception and throw a **ExchangeUnderMaintenanceException** instead. This ensures that the imports will be delayed until the services are operational again.
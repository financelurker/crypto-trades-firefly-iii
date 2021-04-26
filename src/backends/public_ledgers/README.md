# Supported Blockchains

Supported Blockchains enables this service to rewrite "unclassified" transactions which are created when importing deposits or withdrawals between your crypto currency exchange and other holding positions (other cold or hot wallets).

Given the nature that exchanges provide public ledger data for their deposits/withdrawals the service cannot determine the appropriate account of the other side (like BTC addresses you use on your Ledger/Trezor/...). This is where Supported Blockchains come into play.

## How to use

To use a supported Blockchain you simply need to configure your relevant asset accounts as follows:

### BTC/Bitcoin

Add your xPub key to the notes of that account in Firefly III in the following structure:

```
xpub="your xPub key"
```

To make sure this integration will work you can check your key upfront by opening the following url:
```
https://blockchain.info/multiaddr?active=<your xPub key>
```
When you see a JSON in your browser, saying something with "addresses" you're all fine and can proceed.

### NEO/Neo

Add your address to the notes of that account in Firefly III in the following structure:

```
address="your public neo address"
```

To make sure this integration will work you can check your key upfront by opening the following url:
```
https://neoscan.io/api/main_net/v1/get_last_transactions_by_address/<your public neo address>
```
When you see a JSON in your browser, saying something with "vouts" you're all fine and can proceed.

## How to add

So you know the API of a blockchain explorer and are interested in extending this service to work with a new Blockchain which isn't supported by now?
This documentation gives you all you need to know to add another supported exchange to the library.

### Overview

[Big Picture](../../../plantuml/ledger_overview.svg)
<img src="../../plantuml/ledger_overview.svg">

### Implementation

Tbd.

### Exceptions and Exchange Outages

Tbd.
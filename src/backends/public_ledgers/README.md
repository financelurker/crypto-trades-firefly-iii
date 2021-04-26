# Supported Blockchains

Supported Blockchains enables this service to rewrite "unclassified" transactions which are created when importing deposits or withdrawals between your crypto currency exchange and other holding positions (other cold or hot wallets).

Given the nature that exchanges provide public ledger data for their deposits/withdrawals the service cannot determine the appropriate account of the other side (like BTC addresses you use on your Ledger/Trezor/...). This is where Supported Blockchains come into play.

## How to use

To use a supported Blockchain you simply need to configure your relevant asset accounts as follows:

### BTC/Bitcoin

Add your xPub key to the notes of that account in Firefly III in the following structure: xpub="your xPub key"

```
xpub="xpub6CUdnB2WuukhmeDHUU64qj65dnwjmRMv2Ah7ZpdmBGEgtKAKz2eTwxcZ64hABXE1ntHNTMWAkY493fSuJ49eWxWew8ovu7z7MMEyswUw3m5"
```

To make sure this integration will work you can check your key upfront by opening the following url:
```
https://blockchain.info/multiaddr?active=<your xPub key>
```
When you see a JSON in your browser, saying something with "addresses" you're all fine and can proceed.

## How to add

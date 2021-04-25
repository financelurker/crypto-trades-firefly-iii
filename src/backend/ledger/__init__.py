from backend.ledger import blockchain_info_client, neotracker_io_client

supported_blockchains = {
    "BTC": {"client": blockchain_info_client, "identifier": "xpub", "expression": r"xpub=\"([a-zA-Z0-9]*)\""},
    "NEO": {"client": neotracker_io_client, "identifier": "address", "expression": r"address=\"([a-zA-Z0-9]*)\""}
}

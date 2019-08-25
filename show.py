#!/usr/bin/env python3
import argparse
import cbor, bson, msgpack
import pprint
from bitcoinrpc.authproxy import AuthServiceProxy

#
# Print Metanet node and subprotocol data found in a transaction.
#

# Globals to override from command-line
RPCUSER='user'
RPCPASSWORD='password'
RPCPORT=18332 # Testnet 18332, Mainnet 8332
ENCODING="cbor"

def decode_function(name):
    d = { "cbor":cbor.loads, "bson":bson.loads, "msgpack":msgpack.loads }
    return d[name]

def main(txid):
    bitcoin = AuthServiceProxy("http://{}:{}@127.0.0.1:{}".format(RPCUSER, RPCPASSWORD, RPCPORT))
    tx = bitcoin.getrawtransaction(txid, 1)
    for vout in tx["vout"]:
        script = bytes.fromhex(vout["scriptPubKey"]["hex"])
        # Check for OP_RETURN
        if script[0] != 0x6a:
            continue
        
        # Check for 'meta' header
        # We know range as next opcode will be 0x01-0x4b or OP_PUSHDATA1/2/4 followed by length bytes.
        index = 0
        metaflag = b'meta'
        for pos in range(2,7):
            if script[pos:pos+4]==metaflag:
                index = pos + 4
                break
        if index == 0:
            continue

        # Deserialize and print
        payload = script[index:]
        node = decode_function(ENCODING)(payload)
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(node)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("txid", help="txid of transaction containing Metanet data")
    parser.add_argument("-u", "--user", help="rpcuser")
    parser.add_argument("-p", "--password", help="rpcpassword")
    parser.add_argument("-e", "--encoding", choices=["bson", "cbor", "msgpack"], default="cbor", help="data encoding format")
    parser.add_argument("--mainnet", help="use mainnet (default is testnet)", action="store_true", default=False)
    args = parser.parse_args()
    if args.user:
        RPCUSER = args.user
    if args.password:
        RPCPASSWORD = args.password
    if args.mainnet:
        RPCPORT = 8332
    ENCODING = args.encoding
    main(args.txid)

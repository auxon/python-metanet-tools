#!/usr/bin/env python3
import argparse
import cbor, bson, msgpack
import io, secrets, string, time
from hashlib import sha256
from bitcoinrpc.authproxy import AuthServiceProxy
from PIL import Image

#
# Create a chain of Metanet nodes populated with random subprotocol data.
#

# Globals to override from command-line
RPCUSER='user'
RPCPASSWORD='password'
RPCPORT=18332 # Testnet 18332, Mainnet 8332
ADDRESS=None
NUM_NODES_TO_CREATE=5
ENCODING="cbor"

def encode_function(name):
    d = { "cbor":cbor.dumps, "bson":bson.dumps, "msgpack":msgpack.dumps }
    return d[name]

def hash_identity(address, txid):
    s = address + txid
    data = s.encode('utf-8')
    return sha256(sha256(data).digest()).hexdigest()

def create_node(address, parent_txid = "NULL"):
    node = {}
    node['address'] = address
    node['parent_txid'] = parent_txid
    attrs = {}
    attrs['name'] = ''.join(secrets.choice(string.ascii_letters) for i in range(5))
    if parent_txid is "NULL":
        attrs['index_parent'] = "NULL"
    else:
        attrs['index_parent'] = hash_identity(address, parent_txid)
    node['attributes'] = attrs
    node['subprotocols'] = []
    return node

# jpeg image
def gen_media():
    o = {}
    o["protocol_id"] = "MediaProtocolID"
    o["mime-type"] = "image/jpg"
    o["filename"] = "test.jpg"
    o["artist"] = secrets.choice(["Pablo Picasso", "Piet Mondrian", "Paul Cézanne"])
    im = Image.new(mode='RGB', size=(32, 32), color=(secrets.randbelow(256),secrets.randbelow(256),secrets.randbelow(256)))
    buffer = io.BytesIO()
    im.save(buffer, format='JPEG')
    o['content'] = buffer.getvalue()
    return o

# utf-8 text
def gen_pastebin():
    o = {}
    o["protocol_id"] = "PastebinProtocolID"
    o["title"] = secrets.choice(["Aloha", "歡迎", "ようこそ", "ยินดีต้อนรับ"]).encode('utf-8')
    o["tags"] = ["Lorem","Ipsum","Dolor"]
    o["content-type"] = "text/plain"
    o["charset"] = "utf-8"
    o["contents"] = ("Created at " + time.ctime()).encode('utf-8')
    return o

# binary data
def gen_randomdata():
    o = {}
    o["protocol_id"] = "RandomDataProtocolID"
    o["tags"] = ["random", "binary", "data"]
    o["content-type"] = "application/octet-stream"
    o["data"] = secrets.token_bytes(1 + secrets.randbelow(100))
    return o

def main():
    bitcoin = AuthServiceProxy("http://{}:{}@127.0.0.1:{}".format(RPCUSER, RPCPASSWORD, RPCPORT))
    address = ADDRESS
    if address is None:
        address = bitcoin.getaddressesbyaccount("")[0]
        print("Using wallet address: ", address)
    parent_txid = "NULL"
    subprotocols = [None, gen_media, gen_pastebin, gen_randomdata]

    # Create nodes...
    for i in range(NUM_NODES_TO_CREATE):
        node = create_node(address, parent_txid)

        # Add subprotocols to node 
        for _ in range(5):
            subprotocol = secrets.choice(subprotocols)
            if subprotocol is not None:
                node['subprotocols'].append(subprotocol())

        # Create OP_RETURN data
        data = b'meta' + encode_function(ENCODING)(node)
        assert(len(data) < 100000) # sanity check for op_return max limit
        data_hex = data.hex()

        # bitcoin rpc commands to create and fund tx with metanet data in OP_RETURN
        rawtx = bitcoin.createrawtransaction([], {'data':data_hex})
        result = bitcoin.fundrawtransaction(rawtx, {'changeAddress':address})
        rawtx = result['hex']
        result = bitcoin.signrawtransaction(rawtx)
        assert(result['complete'])
        signedtx = result['hex']
        txid = bitcoin.sendrawtransaction(signedtx)

        # Prepare for next iteration
        parent_txid = txid
        print("[Node {}]: https://test.whatsonchain.com/tx/{}".format(i, txid))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--address", help="address used to create metanet nodes (default is to get address from wallet)")
    parser.add_argument("-n", "--num", type=int, help="number of metanet nodes to create", default=NUM_NODES_TO_CREATE)
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
    if args.address:
        ADDRESS = args.address
    assert(args.num > 0)
    NUM_NODES_TO_CREATE = args.num
    ENCODING = args.encoding
    main()

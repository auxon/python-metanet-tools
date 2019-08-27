# python-metanet-tools

Tools and scripts to experiment with the Metanet protocol as described here:

https://nchain.com/app/uploads/2019/06/The-Metanet-Technical-Summary-v1.0.pdf

Related OP_RETURN tools:

https://github.com/bitcartel/python-bitcom-tools

## Metanet Data Layout

How Metanet protocol data should be organized and encoded has not yet been formally specified.

As an experiment, we will treat a single OP_RETURN payload as Metanet protocol related if the data starts with the magic bytes `meta` .

For example, the scriptPubKey of a transaction output containing Metanet data might look like this:

```
6a 4d 34 12 6d 65 74 61 xx xx .. .. xx xx
|  |  |---| |---------| |---------------|
1  2    3        4              5
```
1. OP_RETURN opcode
2. OP_PUSHDATA2 opcode
3. Length of data (little-endian)
4. Magic bytes: 'meta'
5. Metanet data

## Installation

Requirements:
- BitcoinSV node (v0.2.1 or later)
- Python 3

Dependencies to install:

```
pip3 install bson cbor msgpack python-bitcoinrpc
```

## Usage

### create.py

The purpose of `create.py` is to create a series of linked Metanet nodes containing random subprotocol data (text, binary, jpeg) encoded in CBOR (default), BSON or MsgPack.

Each Metanet node's public key 𝑃𝑛𝑜𝑑𝑒 will be the same address as supplied on the command line or selected from the wallet. 

Each Metanode node may contain multiple subprotocols, including multiple instances of the same subprotocol. The Metanet technical summary does not specify if this is desirable or not, but we demonstrate it is possible.

Funding and transaction fees are determined by the Bitcoin node via the Bitcoin RPC call `fundrawtransaction`.

```
usage: create.py [-h] [-a ADDRESS] [-n NUM] [-u USER] [-p PASSWORD]
                 [--mainnet]

optional arguments:
  -h, --help            show this help message and exit
  -a ADDRESS, --address ADDRESS
                        address used to create metanet nodes (default is to
                        get address from wallet)
  -n NUM, --num NUM     number of metanet nodes to create
  -u USER, --user USER  rpcuser
  -p PASSWORD, --password PASSWORD
                        rpcpassword
  -e {bson,cbor,msgpack}, --encoding {bson,cbor,msgpack}
                        data encoding format
  --mainnet             use mainnet (default is testnet)
```

Here is an example running on testnet.  Please make sure any address you specify has funds.

```
$ python3 create.py

Using wallet address:  mp47hZK2Auz2mLXumHnAhGuuAaV4L3Qwyk
[Node 0]: https://test.whatsonchain.com/tx/bb13460f570193bf71dcce4a2c6047dac65c3c264bfc2bb11113bcf15a2d37e9
[Node 1]: https://test.whatsonchain.com/tx/37e2f5c744939db5653069b69effbce14df590a29c67c6c5206091434f9ecf21
[Node 2]: https://test.whatsonchain.com/tx/69013a135ed5b4d34abefbf9d2cf21bbb1b2340299833454ad1dbe6a3ef572c1
[Node 3]: https://test.whatsonchain.com/tx/48defa2d7733f16b10dfdf2c998d3cfb332b2b3a635892592ffd9c80b654320a
[Node 4]: https://test.whatsonchain.com/tx/20e4558dc83cf819957ba3d3e4e18da4a00520716f44ad06db15a9d0a751a7e5
```

### show.py

The purpose of `show.py` is to display any Metanet protocol data stored in a given transaction.

The encoded data is deserialized into a Python object and then pretty printed to console.  The default encoding format is CBOR.

```
usage: show.py [-h] [-u USER] [-p PASSWORD] [-e {bson,cbor,msgpack}]
               [--mainnet]
               txid

positional arguments:
  txid                  txid of transaction containing Metanet data

optional arguments:
  -h, --help            show this help message and exit
  -u USER, --user USER  rpcuser
  -p PASSWORD, --password PASSWORD
                        rpcpassword
  -e {bson,cbor,msgpack}, --encoding {bson,cbor,msgpack}
                        data encoding format
  --mainnet             use mainnet (default is testnet)
```

Example on testnet:

```
$ python3 show.py 37e2f5c744939db5653069b69effbce14df590a29c67c6c5206091434f9ecf21

{ 'address': 'mp47hZK2Auz2mLXumHnAhGuuAaV4L3Qwyk',
  'attributes': { 'index_parent': 'b46cba9869305934bb8387a6d6bbd5e6bac12f85ae6ea85edf64ed64cf0c1531',
                  'name': 'WHzrp'},
  'parent_txid': 'bb13460f570193bf71dcce4a2c6047dac65c3c264bfc2bb11113bcf15a2d37e9',
  'subprotocols': [ { 'artist': 'Paul Cézanne',
                      'content': b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01'
                                 b'\x01\x00\x00\x01\x00\x01\x00\x00'
```

## Data Encoding Formats

As an experiment, Metanet protocol and subprotocol data can be encoded with CBOR (by default), BSON or MsgPack.  These are binary-encoded serialization formats, similar to JSON, with support for storing binary data natively.

Developer benefits:
- drop-in replacement for JSON
- easily add Node attributes (key-value pairs)
- store binary data natively e.g. uint256, pubkeyhash, ciphertext
- no schema compilation and code generation required as part of build process, unlike Protobuf, Flatbuffers, etc
- many language implementations for back-end and front-end development

By encoding Metanet data with a general purpose data format and storing inside a single payload, application developers do not need to have knowledge of parsing Bitcoin Script, as seen with fixed order schemas such as [B://](https://github.com/unwriter/B).

For more information:
- https://cbor.io/
- https://www.slideshare.net/ChristophEngelbert/cbor-the-better-json
- https://en.wikipedia.org/wiki/Comparison_of_data-serialization_formats
- http://bsonspec.org/
- https://www.mongodb.com/json-and-bson
- https://msgpack.org/

## Discussion

- Data layout of an OP_RETURN single payload could include a limited amount of fixed fields after the `meta` magic bytes.  For example, [`meta`|`subprotocolid`] would enable a Metanet parser to quickly identify if the Metanet node is of interest, without having to deserialize the payload.
- Should 𝑃𝑛𝑜𝑑𝑒 and 𝑇𝑥𝐼𝐷𝑝𝑎𝑟𝑒𝑛𝑡 be stored in their binary form, 20 bytes (pubkeyhash) and 32 bytes respectively, or human readable form of ~30 bytes and 64 bytes?
- When computing the index/identity of a node, 𝐼𝐷𝑛𝑜𝑑𝑒:=𝐻(𝑃𝑛𝑜𝑑𝑒||𝑇𝑥𝐼𝐷𝑛𝑜𝑑𝑒), what format is the input data (raw bytes vs human readable string) and the output (raw bytes vs hex string)?
- The hash function 𝐻 is not currently specified so the scripts use `sha256d` which is commonly used throughout Bitcoin.  What criteria will determine the choice of hash function? 
- Where the parent txid does not exist, does NULL mean the literal string NULL, zero byte(s) or the absence of an attribute field?
- It is suggested that a node's index, 𝐼𝐷𝑛𝑜𝑑𝑒, be a fixed attribute of a node, however this cannot be calculated as 𝑇𝑥𝐼𝐷𝑛𝑜𝑑𝑒 is not known ahead of time.  Perhaps Metanet node APIs could be required to provide derived attributes.
- MURLs could experience naming collisions. In the given MURL example of `mnp://bobsblog/summer`, the path `summer` comes from the node attribute `name: summer` but the parent could create a sibling child node with the same attribute.

## Resources

Technical Summary https://nchain.com/app/uploads/2019/06/The-Metanet-Technical-Summary-v1.0.pdf

Blog Part 1 https://medium.com/nchain/edge-cases-the-metanet-blog-41b608c8fe67

Blog Part 2 https://medium.com/nchain/edge-cases-the-metanet-blog-92f43c48490d

https://twitter.com/JackD004/status/1143545683900862464

https://medium.com/@_unwriter/the-metanet-starts-84f255a65782

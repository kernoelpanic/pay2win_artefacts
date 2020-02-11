import web3
import util
import client
import pytest

import json

# --- test values ---
hdr = "020000007ef055e1674d2e6551dba41cd214debbee34aeb544c7ec670000000000000000d3998963f80c5bab43fe8c26228e98d030edf4dcbe48a666f5c39e2d7a885c9102c86d536c890019593a470d"
hdr_hex = int(hdr,16)
hdr_bytes = hdr_hex.to_bytes(80,"big")

hdr_hash = '000000000000000082ccf8f1557c5d40b21edabb18d2d691cfbf87118bac7254'

hdr_nVersion_int = 2
hdr_nVersion_raw_bytes = b'\x02\x00\x00\x00'

hdr_hashPrevBlock_str = '000000000000000067ecc744b5ae34eebbde14d21ca4db51652e4d67e155f07e'
hdr_hashPrevBlock_raw_bytes = b'~\xf0U\xe1gM.eQ\xdb\xa4\x1c\xd2\x14\xde\xbb\xee4\xae\xb5D\xc7\xecg\x00\x00\x00\x00\x00\x00\x00\x00'

hdr_hashMerkleRoot_str = '915c887a2d9ec3f566a648bedcf4ed30d0988e22268cfe43ab5b0cf8638999d3'
hdr_hashMerkleRoot_raw_bytes = b'\xd3\x99\x89c\xf8\x0c[\xabC\xfe\x8c&"\x8e\x98\xd00\xed\xf4\xdc\xbeH\xa6f\xf5\xc3\x9e-z\x88\\\x91'

hdr_nTime_int = 1399703554
hdr_nTime_raw_bytes = b'\x02\xc8mS'

hdr_nBits_int = 419465580
hdr_nBits_raw_bytes = b'l\x89\x00\x19'

hdr_nNonce_int = 222771801
hdr_nNonce_raw_bytes = b'Y:G\r'
# -------------------

def test_util():
    assert client.endSwap(b"\x01\x00") == b"\x00\x01"
    assert client.endSwap(bytearray(b"\x01\x00")) == bytearray(b"\x00\x01")
    assert client.dbytes_to_hexstr(hdr_hashPrevBlock_raw_bytes) == hdr_hashPrevBlock_str
    assert client.dbytes_to_hexstr(b"A\x0f") == "0f41"
    assert client.dbytes_to_hexstr(b"A\x0f",swap=False) == "410f"
    assert client.hexstr_to_dbytes(hdr_hashPrevBlock_str) == hdr_hashPrevBlock_raw_bytes
    assert client.hexstr_to_dbytes("0xf41") == b"A\x0f"
    assert client.hexstr_to_dbytes("f41") == b"A\x0f"
    assert client.hexstr_to_dbytes("0xf41",swap=False) == b"\x0fA"
    assert client.hexstr_to_dbytes("f41",swap=False) == b"\x0fA"
    assert client.dSHA256(hdr_bytes) == hdr_hash
    assert client.dSHA256(hdr_bytes,raw=True) == client.hexstr_to_dbytes(hdr_hash)
    assert client.dSHA256(hdr_bytes,raw=True,num=True) == client.dbytes_to_int(client.hexstr_to_dbytes(hdr_hash))

def test_init_hdr():
    bb = client.BtcBlk(hdr=hdr)

    assert bb.nVersion == hdr_nVersion_int
    assert bb.get_nVersion() == hdr_nVersion_int
    assert bb.get_nVersion(raw=True) == hdr_nVersion_raw_bytes

    assert bb.hashPrevBlock == hdr_hashPrevBlock_str
    assert bb.get_hashPrevBlock() == hdr_hashPrevBlock_str
    assert bb.get_hashPrevBlock(raw=True) == hdr_hashPrevBlock_raw_bytes

    assert bb.hashMerkleRoot == hdr_hashMerkleRoot_str
    assert bb.get_hashMerkleRoot() == hdr_hashMerkleRoot_str
    assert bb.get_hashMerkleRoot(raw=True) == hdr_hashMerkleRoot_raw_bytes

    assert bb.nTime == hdr_nTime_int
    assert bb.get_nTime() == hdr_nTime_int
    assert bb.get_nTime(raw=True) == hdr_nTime_raw_bytes

    assert bb.nBits == hdr_nBits_int
    assert bb.get_nBits() == hdr_nBits_int
    assert bb.get_nBits(raw=True) == hdr_nBits_raw_bytes

    assert bb.nNonce == hdr_nNonce_int
    assert bb.get_nNonce() == hdr_nNonce_int
    assert bb.get_nNonce(raw=True) == hdr_nNonce_raw_bytes

    assert hdr_hash == bb.hash
    assert str(bb) == hdr
    assert bb.get_hdr(outputformat="bytes") == hdr_bytes

def test_init_values():
    bb = client.BtcBlk(nVersion = hdr_nVersion_int,
                       hashPrevBlock = hdr_hashPrevBlock_str,
                       hashMerkleRoot = hdr_hashMerkleRoot_str,
                       nTime = hdr_nTime_int,
                       nBits = hdr_nBits_int,
                       nNonce = hdr_nNonce_int)

    assert bb.nVersion == hdr_nVersion_int
    assert bb.get_nVersion() == hdr_nVersion_int
    assert bb.get_nVersion(raw=True) == hdr_nVersion_raw_bytes

    assert bb.hashPrevBlock == hdr_hashPrevBlock_str
    assert bb.get_hashPrevBlock() == hdr_hashPrevBlock_str
    assert bb.get_hashPrevBlock(raw=True) == hdr_hashPrevBlock_raw_bytes

    assert bb.hashMerkleRoot == hdr_hashMerkleRoot_str
    assert bb.get_hashMerkleRoot() == hdr_hashMerkleRoot_str
    assert bb.get_hashMerkleRoot(raw=True) == hdr_hashMerkleRoot_raw_bytes

    assert bb.nTime == hdr_nTime_int
    assert bb.get_nTime() == hdr_nTime_int
    assert bb.get_nTime(raw=True) == hdr_nTime_raw_bytes

    assert bb.nBits == hdr_nBits_int
    assert bb.get_nBits() == hdr_nBits_int
    assert bb.get_nBits(raw=True) == hdr_nBits_raw_bytes

    assert bb.nNonce == hdr_nNonce_int
    assert bb.get_nNonce() == hdr_nNonce_int
    assert bb.get_nNonce(raw=True) == hdr_nNonce_raw_bytes

    assert hdr_hash == bb.hash
    assert str(bb) == hdr
    assert bb.get_hdr(outputformat="bytes") == hdr_bytes


def test_mrkl_root():
    with open('../testdata/btc_blocks_json_samples/300000') as json_file:
        data = json.load(json_file)

    hashMerkleRoot = data["mrkl_root"]
    txs = data["tx"]
    tx_hashes = list()
    for tx in txs:
        tx_hashes.append(tx["hash"])

    tx_hashes_bytes = client.tx_hashes_to_dbytes(tx_hashes)
    assert client.vrfy_mrkl_root(tx_hashes_bytes,hdr_hashMerkleRoot_str)

    with open('../testdata/btc_blocks_json_samples/100014') as json_file:
        data = json.load(json_file)

    hashMerkleRoot = data["mrkl_root"]
    txs = data["tx"]
    tx_hashes = list()
    for tx in txs:
        tx_hashes.append(tx["hash"])

    tx_hashes_bytes = client.tx_hashes_to_dbytes(tx_hashes)
    assert client.vrfy_mrkl_root(tx_hashes_bytes,hashMerkleRoot)


def test_vrfy_mrkl_block():
    hashes_hex_big = [ 0x3612262624047ee87660be1a707519a443b1c1ce3d248cbfc6c15870f6c5daa2,
               0x019f5b01d4195ecbc9398fbf3c3b1fa9bb3183301d7a1fb3bd174fcfa40a2b65,
               0x41ed70551dd7e841883ab8f0b16bf04176b7d1480e4f0af9f3d4c3595768d068,
               0x20d2a7bc994987302e5b1ac80fc425fe25f8b63169ea78e68fbaaefa59379bbf, ]

    hashes_bytes_big = list()
    for h in hashes_hex_big:
        hashes_bytes_big.append(h.to_bytes(32,"big"))

    hashes_bytes_big.reverse()
    mrkl_block={"hashMerkleRoot":"7f16c5962e8bd963659c793ce370d95f093bc7e367117b3c30c1f8fdd0d97287",
                "tx_count":0x7,
                "tx_hashes":hashes_bytes_big,
                "flag_bytes":1,
                "flags":[0,0,0,1,1,1,0,1]}

    tx_hash = 0x019f5b01d4195ecbc9398fbf3c3b1fa9bb3183301d7a1fb3bd174fcfa40a2b65.to_bytes(32,"big")
    assert client.vrfy_mrkl_block(tx_hash=tx_hash,mrkl_block=mrkl_block)

def test_verfy_mrkl_paths():
    with open('../testdata/btc_blocks_json_samples/100014') as json_file:
        data = json.load(json_file)

    hashMerkleRoot = data["mrkl_root"]
    txs = data["tx"]
    tx_hashes = list()
    for tx in txs:
        tx_hashes.append(tx["hash"])

    tx_hashes_bytes = client.tx_hashes_to_dbytes(tx_hashes)
    assert client.vrfy_mrkl_root(tx_hashes_bytes,hashMerkleRoot)

    # generate merkle path, consisting of mpath and flags
    # and check if the resulting hash during generation still
    # resembles the hashMerkleRoot
    mpath = list()
    flags = list()
    shash = "652b0aa4cf4f17bdb31f7a1d308331bba91f3b3cbf8f39c9cb5e19d4015b9f01"
    result = client.mrkl_root_path(tx_hashes_bytes,
                                   shash=shash,
                                   mpath=mpath,
                                   flags=flags)
    assert int(result["value"].hex(),16).to_bytes(32,"little").hex() == hashMerkleRoot


    # verify Merkle path
    shash='652b0aa4cf4f17bdb31f7a1d308331bba91f3b3cbf8f39c9cb5e19d4015b9f01'
    assert client.vrfy_root_path(hashMerkleRoot,shash,mpath.copy(),flags.copy())

def test_parse_blk_cb():
    with open('../testdata/btc_blocks_json_samples/603268.raw') as json_file:
        data = json.load(json_file)

    blk_raw_hex = data["rawblock"]
    blk_raw = bytes.fromhex(blk_raw_hex)

    assert blk_raw[:80].hex() == '00000020c39def44778136d6d70b610502449d7b77a94d4eff571100000000000000000074e2232b5c3121a3c8473c9db5269c9f39fd1a69e3dc37958b1670c0a24c82f4db0dc95dd12016176971f64f'

    bblk = client.BtcBlk(blk=blk_raw,tx_n=1)

    assert bblk.hdr == blk_raw[:80]
    assert bblk.data == blk_raw[80:]

    assert bblk.tx_count == 2312
    assert bblk.tx_count_raw.hex() == "fd0809"

    assert len(bblk.txs) == 1

    cbtx = bblk.txs[0]
    assert cbtx.nVersion == 1
    assert cbtx.nVersion_raw.hex() == '01000000'

    assert cbtx.flag == None

    assert cbtx.tx_in_cnt == 1 and cbtx.tx_in_cnt == len(cbtx.tx_in)
    assert cbtx.tx_in_cnt_raw.hex() == '01'

    assert cbtx.tx_out_cnt == 3 and cbtx.tx_out_cnt == len(cbtx.tx_out)
    assert cbtx.tx_out_cnt_raw.hex() == '03'

    assert cbtx.nLockTime == 1133291890
    assert cbtx.nLockTime_raw.hex() == '72a98c43'

    txin = cbtx.tx_in[0]
    assert txin.prev_output_raw.hex() == '0000000000000000000000000000000000000000000000000000000000000000ffffffff'
    assert txin.prev_txhash.hex() == '0000000000000000000000000000000000000000000000000000000000000000'
    assert txin.prev_txidx == 4294967295
    assert txin.prev_txidx_raw.hex() == 'ffffffff'

    assert txin.script_len == 95
    assert txin.script_len_raw.hex() == '5f'
    assert txin.script_sig.hex() == '0384340904d30dc95d2f706f6f6c696e2e636f6d2ffabe6d6d97e21604204ac2a8e72201137d16c82253498af55de5432ff9cbde84d5e63ba20100000000000000b578094a09af6006dbcc9db78000f0c20e8b0f355a003a0000fe00000000'
    assert txin.sequence == 4294967295
    assert txin.sequence_raw.hex() == 'ffffffff'

    txout = cbtx.tx_out[0]
    assert txout.value == 1272268104
    assert txout.value_raw.hex() == '4845d54b00000000'
    assert txout.script_len == 23
    assert txout.script_len_raw.hex() == '17'
    assert txout.script_pk.hex() == 'a914b111f00eed1a8123dd0a1fed50b0793229ed47e787'

    txout = cbtx.tx_out[1]
    assert txout.value == 0
    assert txout.value_raw.hex() == '0000000000000000'
    assert txout.script_len == 38
    assert txout.script_len_raw.hex() == '26'
    assert txout.script_pk.hex() == '6a24b9e11b6db0bac66f0f2a2714d384501c639ce147d1c61f482e5c98e43c9a6168d507aecc'

    txout = cbtx.tx_out[2]
    assert txout.value == 0
    assert txout.value_raw.hex() == '0000000000000000'
    assert txout.script_len == 38
    assert txout.script_len_raw.hex() == '26'
    assert txout.script_pk.hex() == '6a24aa21a9ed6b6dd1678f89692e705ec9de8c06a2a0a9fd58d437a39c2878433248aeee7a65'

    assert cbtx.txb.hex() == '01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff5f0384340904d30dc95d2f706f6f6c696e2e636f6d2ffabe6d6d97e21604204ac2a8e72201137d16c82253498af55de5432ff9cbde84d5e63ba20100000000000000b578094a09af6006dbcc9db78000f0c20e8b0f355a003a0000fe00000000ffffffff034845d54b0000000017a914b111f00eed1a8123dd0a1fed50b0793229ed47e7870000000000000000266a24b9e11b6db0bac66f0f2a2714d384501c639ce147d1c61f482e5c98e43c9a6168d507aecc0000000000000000266a24aa21a9ed6b6dd1678f89692e705ec9de8c06a2a0a9fd58d437a39c2878433248aeee7a6572a98c43'

    assert cbtx.txhash == "de612b874b23a78805ed022f55befbc94d12e2e78208d1d6d560df1d998451cb"


def test_parse_blk():
    with open('../testdata/btc_blocks_json_samples/603268.raw') as json_file:
        data = json.load(json_file)

    blk_raw_hex = data["rawblock"]
    blk_raw = bytes.fromhex(blk_raw_hex)

    assert blk_raw[:80].hex() == '00000020c39def44778136d6d70b610502449d7b77a94d4eff571100000000000000000074e2232b5c3121a3c8473c9db5269c9f39fd1a69e3dc37958b1670c0a24c82f4db0dc95dd12016176971f64f'

    bblk = client.BtcBlk(blk=blk_raw)

    txhashes = list()
    for tx in bblk.txs:
        txhashes.append(client.hexstr_to_dbytes(tx.txhash))

    assert client.vrfy_mrkl_root(txhashes,"f4824ca2c070168b9537dce3691afd399f9c26b59d3c47c8a321315c2b23e274")


def test_parse_coinbase():
    with open('../testdata/btc_blocks_json_samples/603268.raw') as json_file:
        data = json.load(json_file)


    blk_raw_hex = data["rawblock"]
    blk_raw = bytes.fromhex(blk_raw_hex)

    assert blk_raw[:80].hex() == '00000020c39def44778136d6d70b610502449d7b77a94d4eff571100000000000000000074e2232b5c3121a3c8473c9db5269c9f39fd1a69e3dc37958b1670c0a24c82f4db0dc95dd12016176971f64f'

    bblk = client.BtcBlk(blk=blk_raw,tx_n=1)
    cb = bblk.txs[0]

    rslt = cb.parse_coinbase()
    assert rslt is not None
    assert rslt["blk_height"] == 603268
    assert rslt["coinbase"] == b'\x04\xd3\r\xc9]/poolin.com/\xfa\xbemm\x97\xe2\x16\x04 J\xc2\xa8\xe7"\x01\x13}\x16\xc8"SI\x8a\xf5]\xe5C/\xf9\xcb\xde\x84\xd5\xe6;\xa2\x01\x00\x00\x00\x00\x00\x00\x00\xb5x\tJ\t\xaf`\x06\xdb\xcc\x9d\xb7\x80\x00\xf0\xc2\x0e\x8b\x0f5Z\x00:\x00\x00\xfe\x00\x00\x00\x00'

    cb_raw = cb.get_tx("bytes")
    cb_raw_hash = client.dSHA256(cb_raw)
    assert cb.txhash == cb_raw_hash

    cb_raw = rslt["coinbasetx_prefix"] + rslt["coinbase_full"] + rslt["coinbasetx_suffix"]
    cb_raw_hash = client.dSHA256(cb_raw)
    assert cb.txhash == cb_raw_hash

def test_nBits_to_Target():
    assert(client.nBits_to_Target(b"\x18\x1b\xc3\x30")  == 0x1bc330000000000000000000000000000000000000000000)
    assert(client.nBits_to_Target(b"\x05\x00\x92\x34")  == 0x92340000)
    assert(client.nBits_to_Target(b"\x01\x00\x34\x56")  == 0x00)
    assert(client.nBits_to_Target(b"\x01\x12\x34\x56")  == 0x12)
    assert(client.nBits_to_Target(b"\x02\x00\x80\x00")  == 0x80)
    assert(client.nBits_to_Target(b"\x04\x12\x34\x56")  == 0x12345600)
    assert(client.nBits_to_Target(b"\x02\x12\x34\x56")  == 0x1234)
    assert(client.nBits_to_Target(b"\x03\x12\x34\x56")  == 0x123456)
    assert(client.nBits_to_Target(b"\x04\x12\x34\x56")  == 0x12345600)
    assert(client.nBits_to_Target(b"\x20\x12\x34\x56")  == 0x1234560000000000000000000000000000000000000000000000000000000000)
    assert(client.nBits_to_Target(b"\x20\x7f\xff\xff")  == 0x7fffff0000000000000000000000000000000000000000000000000000000000)

    with pytest.raises(client.NBitsDecodingExcpetion):
        client.nBits_to_Target(b"\x04\x92\x34\x56") == 0x12345600

    with pytest.raises(client.NBitsDecodingExcpetion):
        client.nBits_to_Target(b"\x01\xfe\xdc\xba")  == 0x7e

    # encoding tests:
    #assert(client.nBits_to_Target(b"\x04\x92\x34\x56")  == 0x12345600) #8  # high bit set
    #assert(client.nBits_to_Target(b"\x01\xfe\xdc\xba")  == 0x7e) #9  # high bit set

def test_within_difficulty_period():
    assert client.within_difficulty_period(0,2015) == True
    assert client.within_difficulty_period(1,2015) == True
    assert client.within_difficulty_period(0,2016) == False
    assert client.within_difficulty_period(0,2017) == False
    assert client.within_difficulty_period(2015,2017) == False
    assert client.within_difficulty_period(2016,2017) == True

def test_replace_bytes():
    old_hdr = b'\x02\x00\x00\x00Tr\xac\x8b\x11\x87\xbf\xcf\x91\xd6\xd2\x18\xbb\xda\x1e\xb2@]|U\xf1\xf8\xcc\x82\x00\x00\x00\x00\x00\x00\x00\x00\xab\n\xaa7|\xa3\xf4\x9b\x15E\xe2\xaek\x06g\xa0\x8fB\xe7-\x8c$\xae#q@\xe2\x8f\x14\xf3\xbb|k\xccmSl\x89\x00\x19\xed\xd8<\xcf'

    assert client.dSHA256(old_hdr) == '000000000000000049a0914d83df36982c77ac1f65ade6a52bdced2ce312aba9'

    mroot = b'\xab\n\xaa7|\xa3\xf4\x9b\x15E\xe2\xaek\x06g\xa0\x8fB\xe7-\x8c$\xae#q@\xe2\x8f\x14\xf3\xbb|'

    new_hdr = client.replace_found_bytes(old_hdr,mroot)

    assert new_hdr == b'\x02\x00\x00\x00Tr\xac\x8b\x11\x87\xbf\xcf\x91\xd6\xd2\x18\xbb\xda\x1e\xb2@]|U\xf1\xf8\xcc\x82\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00k\xccmSl\x89\x00\x19\xed\xd8<\xcf'

    assert client.dSHA256(new_hdr) == '7bea60b080663b91ccc10ca231e72007eb6bc97c7e2626085a0594cbbb59e933'

    offset = client.NVERSION_LEN + client.HASHPREVBLOCK_LEN
    other_hdr = client.replace_at_offset(old_hdr,offset,replace=32)

    assert client.dSHA256(other_hdr) == '7bea60b080663b91ccc10ca231e72007eb6bc97c7e2626085a0594cbbb59e933'


    original_hdr = client.replace_at_offset(other_hdr,offset,replace=mroot)

    assert original_hdr == old_hdr

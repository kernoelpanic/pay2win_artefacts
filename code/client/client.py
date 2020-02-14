import struct
import hashlib
import math
import requests
import json

import web3
import util

""" Bitcoin header constants """
HDR_LEN=80
NVERSION_LEN=4
HASHPREVBLOCK_LEN=32
HASHMERKLEROOT_LEN=32
NTIME_LEN=4
NBITS_LEN=4
NNONCE_LEN=4
assert ( NVERSION_LEN +
         HASHPREVBLOCK_LEN +
         HASHMERKLEROOT_LEN +
         NTIME_LEN +
         NBITS_LEN +
         NNONCE_LEN ) == HDR_LEN

""" Coinbase transaction constants """
CB_TXHASH = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
CB_TXIDX = 0xffffffff

""" Difficulty constants """
# H(block_header) <= TARGET
# difficulty = MAX_TARGET / CURRENT_TARGET
# Therefore lowest difficulty is 1, at the largest possible target
MAX_PTARGET = 0x00000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF # biggest allowed value for TARGET in Bitcoin pooled mining
MAX_BTARGET = 0x00000000FFFF0000000000000000000000000000000000000000000000000000 # biggest allowed value for TARGET in Bitcoin because of nBits decoding to reconstruct target
MAX_REGTEST_TARGET = 0x7fffff0000000000000000000000000000000000000000000000000000000000 # biggest allowed value for TARGET in Bitcoin regtest mode, nBits = b"\x20\x7f\xff\xff"
MAX_TEST_TARGET = 1<<255 # even bigger value for testing, almost every hash will be below this value

DIFFICULTY_PERIOD = 2016

# === utility methods ===
def dSHA256(v,raw=False,num=False):
    """ Double SHA256 as for Bitcoin block hashses """
    assert type(v) is bytes, "argument must be bytes"
    h1 = hashlib.sha256()
    h1.update(v)
    d1 = h1.digest()
    h2 = hashlib.sha256()
    h2.update(d1)
    if raw:
        # big endian output ...
        if num:
            # ... as number
            #return int(h2.digest().hex(),16)
            return int.from_bytes(h2.digest(),"big")
        else:
            # ... as bytes
            return h2.digest()
    else:
        # ... as hex string, "normal" represenation of hash in Bitcoin
        #return int(h2.digest().hex(),16).to_bytes(32,"little").hex()
        return dbytes_to_hexstr(h2.digest())

def dbytes_to_hexstr(h,swap=True):
    """ conve rts and swaps bytes from digest to hex string representation of hash """
    #return int(h.hex(),16).to_bytes(32,"little").hex()  # also works
    #return int.from_bytes(h,"big").to_bytes(32,"little").hex() # also works
    if swap:
        return endSwap(h).hex()
    else:
        return h.hex()

def hexstr_to_dbytes(h,swap=True):
    """ converts and swaps hex string represenation of hash to bytes for generating digest """
    if h[:2] == "0x":
        h = h[2:]
    if len(h)%2 != 0:
        h = h.zfill(len(h)+1)
    num_bytes = len(h)//2
    if swap:
        return int(h,16).to_bytes(num_bytes,"little")
    else:
        return int(h,16).to_bytes(num_bytes,"big")

def int_to_dbytes(h):
    """ converts and swaps int representation of hash to bytes for generating digest """
    return h.to_bytes(32,"little")

def dbytes_to_int(h):
    """ converts bytes represenation of hash to int, without conversion """
    return int.from_bytes(h,"big")

def endSwap(b):
    """ change endianess of bytes """
    if type(b) is bytes:
        return bytes(reversed(b))
    elif type(b) is bytearray:
        return bytearray(reversed(b))
    else:
        assert False,"Type must be byte or bytearray!"

def tx_hashes_to_dbytes(tx_hashes):
    """ Convert list of transaction hashes to list of swaped bytes values to feed into digest """
    assert type(tx_hashes) is list,"Must be list of int or hex strings"
    tx_hashes_dbytes = list()
    for h in tx_hashes:
        if type(h) is str:
            tx_hashes_dbytes.append(hexstr_to_dbytes(h))
        elif type(h) is int:
            tx_hashes_dbytes.append(int_to_dbytes(h))
        else:
            assert False,"hashes must be int or hex string"
    return tx_hashes_dbytes

def vint_to_int(vint):
    """ parse bytes as var int an returns tuple of var int bytes to remove and var int value """
    assert type(vint) == bytes,"vint must be bytes in little endian!"
    if vint[0] < 0xFD:
        return (1,vint[0]) # uint8_t
    elif vint[0] == 0xFD:
        return (3,struct.unpack("<H",vint[1:3])[0]) # uint16_t
    elif vint[0] == 0xFE:
        return (5,struct.unpack("<L",vint[1:5])[0]) # uint32_t
    elif vint[0] == 0xFF:
        return (9,struct.unpack("<Q",vint[1:9])[0]) # uint64_t
    else:
        assert False,"Invalid var_int! maybe fucked up endianess?"

def int_to_vint(integer):
    """ return integer as bytes of var_int """
    assert type(integer) is int,"integer must be int!"
    if integer < 0xFD:
        return integer.to_bytes(1,"little")
    elif integer < 2**16:
        return b"\xFD" + integer.to_bytes(2,"little")
    elif integer < 2**32:
        return b"\xFE" + integer.to_bytes(4,"little")
    elif integer < 2**64:
        return b"\xFF" + integer.to_bytes(8,"little")
    else:
        assert False,"Integer overflow, var_int to small to hold python integer!"

class NBitsDecodingExcpetion(Exception):
    """ Class for custom nBits decoding excpetions """
    pass

def nBits_to_Target(nBits,big_endian=True,strict=True):
    """
    SetCompact handling in Bitcoin core:
    https://github.com/bitcoin/bitcoin/blob/78dae8caccd82cfbfd76557f1fb7d7557c7b5edb/src/pow.cpp#L74
    https://github.com/bitcoin/bitcoin/blob/46d6930f8c7ba7cbcd7d86dd5d0117642fcbc819/src/arith_uint256.h#L277
    https://github.com/bitcoin/bitcoin/blob/46d6930f8c7ba7cbcd7d86dd5d0117642fcbc819/src/arith_uint256.cpp#L203
    """
    assert type(nBits) is bytes, "Must be big-endian bytes or big_endian=False"
    if not big_endian:
        nBits = endSwap(nBits)
    nCompact = int.from_bytes(nBits,"big")
    exponent = nBits[0]
    mantissa = int.from_bytes(nBits[1:],"big")

    nWord = nCompact & 0x007fffff # remove exponent bits and sign bit, keep the rest as is
    if (exponent <= 3):
        nWord = nWord >> 8 * (3 - exponent)
    else:
        nWord = nWord << 8 * (exponent - 3)

    T = nWord
    #T = nWord % (2**256-1) # only needed if not strict
    if strict and nWord != 0 and ( exponent > 34 or ( nWord > 0xff and exponent > 33 ) or ( nWord > 0xffff and exponent > 32 )):
        # check if mantissa/significant is larger than what fits a 256 bit value,
        # if so this indicates and error during parseing
        raise NBitsDecodingExcpetion("Overflow! Recovered target > 256 bits!")

    if strict and nWord != 0 and nCompact & 0x00800000 != 0:
        # check if sign bit is set, if so this indicates an error during parsing
        raise NBitsDecodingExcpetion("nBits is negative!")

    return T

def within_difficulty_period(startBlkidx,endBlkidx):
    """ Helper script to check if attack interval is between two difficulty adjustments.
    i.e., no difficutly adjustments occures during attack
    """
    assert startBlkidx < endBlkidx, "start not smaller than end block index"
    delta = endBlkidx - startBlkidx
    start = startBlkidx % DIFFICULTY_PERIOD
    if start + delta < DIFFICULTY_PERIOD:
        return True
    else:
        return False

def replace_found_bytes(old_hdr,find,replace=None):
    """ Find and replace bytes, if replace is None they are  zeroed out """
    assert type(old_hdr) is bytes and type(find) is bytes, "Wrong input type"
    assert len(old_hdr) >= len(find),"Find must be smaller or equal input bytes"
    if (replace is None):
        replace = b"\x00"*len(find)
    else:
        assert type(replace) is bytes, "Wrong input type"
    assert len(find) == len(replace), "Find replace lenght not equal"
    new_hdr = old_hdr.replace(find,replace)
    return new_hdr

def replace_at_offset(hdr,offset,replace=None):
    """ Replace bytes at offset,  either with replacement bytes or given number of zero bytes """
    if (type(replace) is int):
        replace = b"\x00"*replace
    assert type(replace) is bytes, "Wrong input type"
    assert len(hdr) >= offset, "Offset to large"
    new_hdr = bytearray(hdr)
    for pos,octet in enumerate(replace):
        new_hdr[offset + pos] = octet
    return bytes(new_hdr)

# --- Merkle path generation and verification ---
def vrfy_mrkl_root(tx_hashes,hashMerkleRoot):
    """ verify given Merkle tree root hash by recomputing Merkle tree

    :param tx_hashes: List of tx hashes as baselayer of merkle tree
    :type tx_hashes: list[bytes]
    :param hashMerkleRoot: Merkle tree root hash
    :type hashMerkleRoot: str
    :return: True if the calculated hash matches the given one
    :rtype: bool
    """
    return mrkl_root(tx_hashes.copy()) == hashMerkleRoot

def mrkl_root(hashes):
    """ compute Merkle tree root hash """
    assert type(hashes[0]) is bytes,"tx_hashes must be little endian bytes"
    if len(hashes) == 1:
        #return int(hashes[0].hex(),16).to_bytes(32,"little").hex()
        return dbytes_to_hexstr(hashes[0])
    if len(hashes) % 2 != 0:
        hashes.append(hashes[-1])
    nextlevel=list()
    i=0
    while i < len(hashes):
        nextlevel.append(dSHA256(hashes[i] + hashes[i+1],raw=True))
        i+=2
    return mrkl_root(nextlevel)

def vrfy_root_path(hashMerkleRoot,shash,mpath,flags):
    """ Verify given tx search hash against given Merkle tree root hash """
    #if flags[0] == 1:
    mpath.insert(0,hexstr_to_dbytes(shash))
    #elif flags[0] == 0:
    #    mpath.insert(1,hexstr_to_dbytes(shash))
    #else:
    #    assert False,"Flags must be list of integers!"

    flags.reverse()
    while len(mpath)>1:
        flag = flags.pop()
        if flag == 0:
            calculated_hash = dSHA256(mpath[1] + mpath[0],raw=True)
        elif flag == 1:
            calculated_hash = dSHA256(mpath[0] + mpath[1],raw=True)
        else:
            assert False,"Falgs must be list of integers!"
        del mpath[0:2]
        mpath.insert(0,calculated_hash)
    return dbytes_to_hexstr(mpath[0]) == hashMerkleRoot

def mrkl_root_path(hashes,shash=None,mpath=None,flags=None):
    """ create Merkel inclusion proof
    """
    initlevel = list()
    for h in hashes:
        initlevel.append({"value":h,"hit":False})
    #print("init level: ",initlevel)
    return mrkl_path(initlevel,shash=shash,mpath=mpath,flags=flags)

def mrkl_path(level,shash=None,mpath=None,flags=None):
    assert type(level[0]["value"]) is bytes,"tx_hashes must be little endian bytes"
    if len(level) == 1:
        return level[0]
    if len(level) % 2 != 0:
        level.append({"value":level[-1]["value"],"hit":False})
    nextlevel=list()
    i=0
    while i < len(level):
        nextparent = dict()
        if dbytes_to_hexstr(level[i]["value"]) == shash:
            mpath.append(level[i+1]["value"])
            nextparent["hit"] = True
            flags.append(1)

        elif dbytes_to_hexstr(level[i+1]["value"]) == shash:
            mpath.append(level[i]["value"])
            nextparent["hit"] = True
            flags.append(0)

        elif level[i]["hit"] == True:
            nextparent["hit"] = True
            mpath.append(level[i+1]["value"])
            flags.append(1)

        elif level[i+1]["hit"] == True:
            nextparent["hit"] = True
            mpath.append(level[i]["value"])
            flags.append(0)
        else:
            nextparent["hit"] = False
        nextparent["value"] = dSHA256(level[i]["value"] + level[i+1]["value"],raw=True)
        nextlevel.append(nextparent)
        i+=2
    return mrkl_path(nextlevel,shash=shash,mpath=mpath,flags=flags)

# --- Bitcoin style Merkle Blocks verification  ---
class Node():
    """ Merkle Tree node """
    def __init__(self, value, left=None, right=None):
        self.value = value  # The node value
        self.left = left    # Left child
        self.right = right  # Right child

def gen_mrkl_block(tx_hash,tx_hashes):
    # TODO create Bitcoin style Merkle Blocks
    mrkl_block={"hashMerkleRoot":mrkl_root(tx_hashes),
                "tx_count":len(tx_hashes),
                "tx_hashes":hashes_bytes,
                "flag_bytes":math.ceil(len(flags)/8),
                "flags":[0,0,0,1,1,1,0,1]}
    return mrkl_block

def vrfy_mrkl_block(tx_hash,mrkl_block):
    """ Verfiy Bitcoin style Merkle Blocks """
    depth = math.ceil(math.log(mrkl_block["tx_count"],2))
    assert type(mrkl_block["tx_hashes"]) is list,"tx_hashes must be list"
    assert type(mrkl_block["tx_hashes"][0]) is bytes,"tx_hashes must be list of bytes objects"
    hashes = mrkl_block["tx_hashes"]
    assert type(mrkl_block["flags"]) is list,"Flags must be list"
    assert type(mrkl_block["flags"][0]) is int,"Flags must be list of int"
    flags = mrkl_block["flags"]

    height = 0
    flag = flags.pop()
    if depth > 0 and flag == 1:
        node = Node(1)
        height += 1
        node.left = build_tree(height,flags,hashes,depth,tx_hash)
        node.right = build_tree(height,flags,hashes,depth,tx_hash)
        node.value = dSHA256(node.left.value + node.right.value,raw=True)
    elif depth == 0 and flag == 1:
        node = Node(hashes.pop())
        print("Only coinbase hash")
    else:
        print("Invalid merkle block")
        return None
    #print("Node value: ",node.value.hex())
    #print("Shoudl be : ",mrkl_block["hashMerkleRoot"])
    return mrkl_block["hashMerkleRoot"] == node.value.hex()

def build_tree(height,flags,hashes,depth,tx_hash=None):
    if height < depth:
        if flags.pop() is 1:
            node = Node(1)
            height += 1
            node.left = build_tree(height,flags,hashes,depth,tx_hash)
            node.right = build_tree(height,flags,hashes,depth,tx_hash)
            node.value = dSHA256(node.left.value + node.right.value,raw=True)
            return node
        else:
            node = Node(hashes.pop())
            return node
    if height == depth:
        if flags.pop() is 1:
            if tx_hash is not None:
                assert tx_hash == hashes[-1]
        node = Node(hashes.pop())
        return node


# --- Prepare input blocks calldata ---
def fetch_input_blocks(startHeight,n,blks):
    """ Fetch some full bitcoin blocks from the interwebz """
    for h in range(startHeight,startHeight + n):
        url = "https://blockchain.info/block-height/" + str(h) + "?format=json"
        r1 = requests.get(url)
        blocks = r1.json()
        assert len(blocks["blocks"]) == 1,"fork at height" # check if there was a fork at height
        block = blocks["blocks"][0]
        blks.append(block)

        # get raw block
        url = "https://insight.bitpay.com/api/rawblock/" + block["hash"]
        r2 = requests.get(url)
        block_raw = r2.json()["rawblock"]
        blks[-1]["rawblock"] = block_raw
    return blks

def store_input_blocks(path,blks):
    """ Store fetched blocks on disk e.g,
    store_input_blocks(./testdata/btc_blocks_json_samples/')
    """
    startHeight = blks[0]["height"]
    endHeight = blks[-1]["height"]
    with open(path + str(startHeight) + '--' + str(endHeight) , 'w') as outfile:
        json.dump(blks, outfile)
    return True

def load_input_blocks(path):
    """ Load stored blocks from disk e.g.,
    load_input_blocks('./testdata/btc_blocks_json_samples/300000--300007')
    """
    with open(path) as json_file:
        blks = json.load(json_file)
    return blks

def get_input_block_calldata(blks,n):
    # hash
    blockHash_str = blks[n]["hash"]
    blockHash_bytes_little = hexstr_to_dbytes(blockHash_str,swap=False)
    blockHash_bytes_big = hexstr_to_dbytes(blockHash_str)

    # header
    blockHeader_bytes_big = hexstr_to_dbytes(blks[n]["rawblock"][:80*2],swap=False)
    assert dSHA256(blockHeader_bytes_big) == blockHash_str, "Invalid block header or hash"
    assert endSwap(dSHA256(blockHeader_bytes_big,raw=True)) == blockHash_bytes_little, "Invalid block hash in bytes"
    assert dSHA256(blockHeader_bytes_big,raw=True) == blockHash_bytes_big, "Invalid block hash in bytes"


    # coinbase
    block_str = blks[n]["rawblock"]
    block_bytes_big = hexstr_to_dbytes(block_str,swap=False)
    #b = BtcBlk(blk=blk_bytes,tx_n=1) # parse only coinbase
    block = BtcBlk(blk=block_bytes_big) # parse whole block
    coinbaseTx = block.txs[0]
    coinbase = coinbaseTx.parse_coinbase()
    # get parsed block height from coinbase
    blockHeight = coinbase["blk_height"]
    assert blks[n]["height"] == blockHeight
    # get previous block hash
    blockHashPrevBlock_str = block.hashPrevBlock
    blockHashPrevBlock_bytes_big = hexstr_to_dbytes(block.hashPrevBlock)
    blockHashPrevBlock_bytes_little = hexstr_to_dbytes(block.hashPrevBlock,swap=False)
    # get coinbase prefix,suffix and coinbase
    cb_pfx = coinbase["coinbasetx_prefix"]
    cb = coinbase["coinbase_full"]
    cb_sfx = coinbase["coinbasetx_suffix"]
    cb_hash = coinbaseTx.txhash
    cb_tx = b"".join([ cb_pfx, cb, cb_sfx])
    assert hexstr_to_dbytes(blks[n]["tx"][0]["inputs"][0]["script"],swap=False) == cb
    assert dSHA256(cb_tx) == coinbaseTx.txhash # check if coinbaseTx is valid, also in slices
    assert coinbaseTx.txhash == blks[n]["tx"][0]["hash"]
    # hashMerkleRoot
    blockHashMerkleRoot_str = block.hashMerkleRoot
    blockHashMerkleRoot_bytes_big = hexstr_to_dbytes(block.hashMerkleRoot)
    assert blockHashMerkleRoot_str == blks[n]["mrkl_root"]

    # tx hashes of block
    block_txhash_list_str = list()
    for t in block.txs:
        block_txhash_list_str.append(t.txhash)

    # verify all hashes sum up to merkle path again
    block_txhash_list_bytes = tx_hashes_to_dbytes(block_txhash_list_str)
    assert vrfy_mrkl_root(block_txhash_list_bytes,blockHashMerkleRoot_str)

    # merkle path to coinbase
    # input data:
    mpath = list()
    flags = list()
    shash = coinbaseTx.txhash

    result = mrkl_root_path(block_txhash_list_bytes,
                               shash=shash,
                               mpath=mpath,
                               flags=flags)
    assert dbytes_to_hexstr(result["value"]) == blockHashMerkleRoot_str
    assert vrfy_root_path(blockHashMerkleRoot_str,
                          coinbaseTx.txhash,
                          mpath.copy(),
                          flags.copy()) # copy because call-by-ref. and gets deleted
    mp_hashes_bytes_big = b''.join(mpath) # concat all merkle path hashes, they are fixed size this is good

    # prepare tblock
    # replace Merkle tree root hash
    tblockHeader_bytes_big = replace_found_bytes(blockHeader_bytes_big,hexstr_to_dbytes(blockHashMerkleRoot_str))
    # replace previous block hash
    tblockHeader_bytes_big = replace_found_bytes(tblockHeader_bytes_big,hexstr_to_dbytes(blockHashPrevBlock_str))
    # calculate new tblock hash
    tblockHash_str = dSHA256(tblockHeader_bytes_big)
    tblockHash_bytes_big = hexstr_to_dbytes(tblockHash_str)

    offset = NVERSION_LEN + HASHPREVBLOCK_LEN
    undo_replace = replace_at_offset(tblockHeader_bytes_big,offset,replace=blockHashMerkleRoot_bytes_big)
    offset = NVERSION_LEN
    undo_replace = replace_at_offset(undo_replace,offset,replace=blockHashPrevBlock_bytes_big)
    assert undo_replace == blockHeader_bytes_big
    assert dSHA256(undo_replace) == blockHash_str

    # check if previous block hash fits
    if n > 0:
        assert blks[n-1]["hash"] == blockHashPrevBlock_str

    return {"blockHash_str": blockHash_str,
            "blockHash_bytes_little":  blockHash_bytes_little,
            "blockHash_bytes_big": blockHash_bytes_big,
            "blockHeader_bytes_big": blockHeader_bytes_big,
            "blockHashMerkleRoot_str": blockHashMerkleRoot_str,
            "blockHashMerkleRoot_bytes_big": blockHashMerkleRoot_bytes_big,
            "blockHashPrevBlock_str": blockHashPrevBlock_str,
            "blockHashPrevBlock_bytes_big": blockHashPrevBlock_bytes_big,
            "blockHashPrevBlock_bytes_little": blockHashPrevBlock_bytes_little,
            "blockHeight": blockHeight,
            "tblockHeader_bytes_big": tblockHeader_bytes_big,
            "tblockHash_bytes_big": tblockHash_bytes_big,
            "cb_pfx": cb_pfx,
            "cb": cb,
            "cb_sfx": cb_sfx,
            "cb_hash": cb_hash,
            "mp_hashes_list": mpath,
            "mp_hashes_bytes_big": mp_hashes_bytes_big,
            "mp_flags": flags}

# === Classes ===
class BtcHdrException(Exception):
    """ Class for custom Bitcoin header related excptions """
    pass

class BtcBlk:
    """ Bitcoin block data class
    Fields defined as in source code:
    https://github.com/bitcoin/bitcoin/blob/master/src/primitives/block.h
    """
    def __init__(self,nVersion=None,
                      hashPrevBlock=None,
                      hashMerkleRoot=None,
                      nTime=None,
                      nBits=None,
                      nNonce=None,
                      hdr=None,
                      blk=None,
                      height=None,
                      tx_n=None,
                      strict=True):
        if hdr is not None:
            self.hdr = self.parse_btc_hdr(hdr)

            self.tx_count=None
            self.txs=None
        elif blk is not None:
            self.blk = self.parse_btc_blk(blk,tx_n=tx_n)
        else:
            self.nVersion=nVersion # int
            self.hashPrevBlock=hashPrevBlock # str
            self.hashMerkleRoot=hashMerkleRoot # str
            self.nTime=nTime # int
            self.nBits=nBits # int
            self.nNonce=nNonce # int

            # compleate header as bytes in little endian
            hdr = struct.pack("<l",self.nVersion)
            hdr += int(self.hashPrevBlock,16).to_bytes(HASHPREVBLOCK_LEN,"little")
            hdr += int(self.hashMerkleRoot,16).to_bytes(HASHMERKLEROOT_LEN,"little")
            hdr += struct.pack("<l",self.nTime)
            hdr += struct.pack("<l",self.nBits)
            hdr += struct.pack("<l",self.nNonce)
            assert len(hdr) == HDR_LEN
            self.hdr = hdr

            self.tx_count=None
            self.txs=None

        # Other relevant Bitcoin block information that is not in the header:
        self.hash=dSHA256(self.hdr)
        self.height=height

        self.target = nBits_to_Target( struct.pack("<l",self.nBits),False )
        self.bdifficulty=MAX_BTARGET/self.target
        self.pdifficutly=MAX_PTARGET/self.target
        self.tdifficutly=MAX_REGTEST_TARGET/self.target
        #print("nBits:   : ",self.nBits)
        #print("nBits_raw: ",struct.pack("<l",self.nBits))
        #print("hash      : ",self.hash)
        #print("target    : ",hex(self.target)[2:].zfill(64))
        #print("difficulty: ",self.bdifficulty)
        if strict:
            # check if block meets target
            assert int(self.hash,16) <= self.target

    def check_btc_hdr(self,hdr):
        if type(hdr) is bytes:
            #print("bytes hdr")
            assert len(hdr) == 80, "Header length not 80 bytes"
            hdr_bytes_little = hdr
        elif type(hdr) is str:
            #print("str hdr")
            if hdr[:2] == "0x":
                hdr = hdr[2:]
            assert len(hdr) == 80*2 or len(hdr) == (80*2)-1, "Header length not 80*2 chars"
            hdr_bytes_little = int(hdr,16).to_bytes(80,"big")
        elif type(hdr) is int:
            #print("int hdr")
            assert hdr < 1<<80*8  and hdr > 1<<79*8, "Header length not in 80 bytes range"
            hdr_bytes_little = hdr.to_bytes(80,"big")
        else:
            raise BtcHdrException("Invalid BTC header type!")
            return None

        return hdr_bytes_little

    def parse_btc_hdr(self,hdr):
        hdr = self.check_btc_hdr(hdr)
        self.nVersion = self.getNVersionFromHeader(hdr)
        self.hashPrevBlock = self.getHashPrevBlockFromHeader(hdr)
        self.hashMerkleRoot = self.getHashMerkleRootFromHeader(hdr)
        self.nTime = self.getNTimeFromHeader(hdr)
        self.nBits = self.getNBitsFromHeader(hdr)
        self.nBits_raw = self.getNBitsFromHeader(hdr,raw=True)
        self.nNonce = self.getNNonceFromHeader(hdr)
        return hdr

    def _getXFromHeader(self,hdr,offset_start,offset_end):
        """ extract bytes from header """
        hdr_bytes_little = self.check_btc_hdr(hdr)
        #print("Hdr: ",bytes.hex(hrd_bytes_little))
        return hdr_bytes_little[offset_start:offset_end]

    def getNVersionFromHeader(self,hdr,raw=False):
        nVersion_little = self._getXFromHeader(hdr,
                             offset_start=0,
                             offset_end=NVERSION_LEN)
        if raw:
            # returns little endian raw bytes
            return nVersion_little
        else:
            return struct.unpack("<l",nVersion_little)[0] # int32_t

    def getHashPrevBlockFromHeader(self,hdr,raw=False):
        hashPrevBlock_little = self._getXFromHeader(hdr,
                             offset_start=NVERSION_LEN,
                             offset_end=NVERSION_LEN + HASHPREVBLOCK_LEN)
        if raw:
            # returns little endian raw bytes
            return hashPrevBlock_little
        else:
            return int(hashPrevBlock_little.hex(),16).to_bytes(32,"little").hex()

    def getHashMerkleRootFromHeader(self,hdr,raw=False):
        hashMerkleRoot_little = self._getXFromHeader(hdr,
                             offset_start=NVERSION_LEN + HASHPREVBLOCK_LEN,
                             offset_end=NVERSION_LEN + HASHPREVBLOCK_LEN + HASHMERKLEROOT_LEN)
        if raw:
            # returns little endian raw bytes
            return hashMerkleRoot_little
        else:
            return int(hashMerkleRoot_little.hex(),16).to_bytes(32,"little").hex()

    def getNTimeFromHeader(self,hdr,raw=False):
        nTime_little = self._getXFromHeader(hdr,
                             offset_start=NVERSION_LEN + HASHPREVBLOCK_LEN + HASHMERKLEROOT_LEN,
                             offset_end=NVERSION_LEN + HASHPREVBLOCK_LEN + HASHMERKLEROOT_LEN + NTIME_LEN)
        if raw:
            # returns little endian raw bytes
            return nTime_little
        else:
            return struct.unpack("<L",nTime_little)[0] # uint32_t

    def getNBitsFromHeader(self,hdr,raw=False):
        nBits_little = self._getXFromHeader(hdr,
                             offset_start=NVERSION_LEN + HASHPREVBLOCK_LEN + HASHMERKLEROOT_LEN + NTIME_LEN,
                             offset_end=NVERSION_LEN + HASHPREVBLOCK_LEN + HASHMERKLEROOT_LEN + NTIME_LEN + NBITS_LEN)
        if raw:
            # returns little endian raw bytes
            return nBits_little
        else:
            return struct.unpack("<L",nBits_little)[0] # uint32_t

    def getNNonceFromHeader(self,hdr,raw=False):
        nNonce_little = self._getXFromHeader(hdr,
                             offset_start=NVERSION_LEN + HASHPREVBLOCK_LEN + HASHMERKLEROOT_LEN + NTIME_LEN + NBITS_LEN,
                             offset_end=NVERSION_LEN + HASHPREVBLOCK_LEN + HASHMERKLEROOT_LEN + NTIME_LEN + NBITS_LEN + NNONCE_LEN)
        if raw:
            # returns little endian raw bytes
            return nNonce_little
        else:
            return struct.unpack("<L",nNonce_little)[0] # uint32_t

    def get_hdr(self,outputformat="dict"):
        """ return btc header in specified format """
        if outputformat=="bytes":
            return self.hdr

        elif outputformat=="dict":
            return {"nVersion":self.nVersion,
                "hashPrevBlock":self.hashPrevBlock,
                "hashMerkleRoot":self.hashMerkleRoot,
                "nTime":self.nTime,
                "nBits":self.nBits,
                "nBits_raw":self.nBits_raw,
                "nNonce":self.nNonce}

        elif outputformat=="string":
            # little endian string
            hdr = bytes.hex(struct.pack("<l",self.nVersion))
            hdr += bytes.hex(int(self.hashPrevBlock,16).to_bytes(HASHPREVBLOCK_LEN,"little"))
            hdr += bytes.hex(int(self.hashMerkleRoot,16).to_bytes(HASHMERKLEROOT_LEN,"little"))
            hdr += bytes.hex(struct.pack("<l",self.nTime))
            hdr += bytes.hex(struct.pack("<l",self.nBits))
            hdr += bytes.hex(struct.pack("<l",self.nNonce))
            return hdr
        else:
            assert False, "Wrong output format given, must be either 'dict', 'bytes' or 'string'"

    def __str__(self):
        """ String represenation of class is the header as hex string """
        return self.get_hdr(outputformat="string")

    # --- nVersion ---
    @property
    def nVersion(self):
        """ Default nVersion getter """
        return self.__nVersion

    @nVersion.setter
    def nVersion(self,nVersion):
        assert type(nVersion) is int, "nVersion must be type int!"
        assert nVersion < 2**(NVERSION_LEN*8)-1, "nVersion must be at most 4 byte"
        self.__nVersion=nVersion

    def get_nVersion(self,raw=False):
        if raw:
            # returns little endian raw bytes
            return struct.pack("<l",self.nVersion)
        else:
            return self.nVersion

    # --- hashPrevBlock ---
    @property
    def hashPrevBlock(self):
        """ Defautl hashPrevBlock getter """
        return self.__hashPrevBlock

    @hashPrevBlock.setter
    def hashPrevBlock(self,hashPrevBlock):
        if type(hashPrevBlock) is bytes:
            assert len(hashPrevBlock) == HASHPREVBLOCK_LEN, "hashPrevBlock invalid length"
            self.__hashPrevBlock = hashPrevBlock.hex().to_bytes(HASHPREVBLOCK_LEN,"little").hex()
        elif type(hashPrevBlock) is str:
            assert len(hashPrevBlock) == HASHPREVBLOCK_LEN*2 or len(hashPrevBlock) == (HASHPREVBLOCK_LEN*2)-1, "hashPrevBlock invalid length"
            self.__hashPrevBlock = hashPrevBlock
        elif type(hashPrevBlock) is int:
            assert ( hashPrevBlock < 1<<HASHPREVBLOCK_LEN*8  and
                     hashPrevBlock > 1<<(HASHPREVBLOCK_LEN-1)*8 ), "hashPrevBlcok invalid length"
            self.__hashPrevBlock = hex(hashPrevBlock)[2:]
        else:
            assert False, "Wrong type of hashPrevBlock"

    def get_hashPrevBlock(self,raw=False):
        if raw:
            # return little endian representation of hash as bytes
            return int(self.hashPrevBlock,16).to_bytes(HASHPREVBLOCK_LEN,"little")
        else:
            # return big endian (standard) represenatioan of hash as hex string
            return self.hashPrevBlock

    # --- hashMerkleRoot ---
    @property
    def hashMerkleRoot(self):
        """ Defautl hashMerkleRoot getter """
        return self.__hashMerkleRoot

    @hashMerkleRoot.setter
    def hashMerkleRoot(self,hashMerkleRoot):
        if type(hashMerkleRoot) is bytes:
            assert len(hashMerkleRoot) == HASHMERKLEROOT_LEN, "hashMerkleRoot invalid length"
            self.__hashMerkleRoot = hashMerkleRoot.hex().to_bytes(HASHMERKLEROOT_LEN,"little").hex()
        elif type(hashMerkleRoot) is str:
            assert len(hashMerkleRoot) == HASHMERKLEROOT_LEN*2 or len(hashMerkleRoot) == (HASHMERKLEROOT_LEN*2)-1, "hashMerkleRoot invalid length"
            self.__hashMerkleRoot = hashMerkleRoot
        elif type(hashMerkleRoot) is int:
            assert ( hashMerkleRoot < 1<<HASHMERKLEROOT_LEN*8  and
                     hashMerkleRoot > 1<<(HASHMERKLEROOT_LEN-1)*8 ), "hashPrevBlcok invalid length"
            self.__hashMerkleRoot = hex(hashMerkleRoot)[2:]
        else:
            assert False, "Wrong type of hashMerkleRoot"

    def get_hashMerkleRoot(self,raw=False):
        if raw:
            # return little endian representation of hash as bytes
            return int(self.hashMerkleRoot,16).to_bytes(HASHMERKLEROOT_LEN,"little")
        else:
            # return big endian (standard) represenatioan of hash as hex string
            return self.hashMerkleRoot

    # --- nTime ---
    @property
    def nTime(self):
        """ Default nTime getter """
        return self.__nTime

    @nTime.setter
    def nTime(self,nTime):
        assert type(nTime) is int, "nTime must be type int!"
        assert nTime < 2**(NVERSION_LEN*8)-1, "nTime must be at most 4 byte"
        self.__nTime=nTime

    def get_nTime(self,raw=False):
        if raw:
            # returns little endian raw bytes
             return struct.pack("<l",self.nTime)
        else:
             return self.nTime

    # --- nBits ---
    @property
    def nBits(self):
        """ Default nBits getter """
        return self.__nBits

    @nBits.setter
    def nBits(self,nBits):
        assert type(nBits) is int, "nBits must be type int!"
        assert nBits < 2**(NVERSION_LEN*8)-1, "nBits must be at most 4 byte"
        self.__nBits=nBits

    def get_nBits(self,raw=False):
        if raw:
            # returns little endian raw bytes
             return struct.pack("<l",self.nBits)
        else:
             return self.nBits

    # --- nNonce ---
    @property
    def nNonce(self):
        """ Default nNonce getter """
        return self.__nNonce

    @nNonce.setter
    def nNonce(self,nNonce):
        assert type(nNonce) is int, "nNonce must be type int!"
        assert nNonce < 2**(NVERSION_LEN*8)-1, "nNonce must be at most 4 byte"
        self.__nNonce=nNonce

    def get_nNonce(self,raw=False):
        if raw:
            # returns little endian raw bytes
             return struct.pack("<l",self.nNonce)
        else:
             return self.nNonce

    # --- block parseing ---
    def parse_btc_blk(self,blk,tx_n=None):
        assert type(blk) is bytes, "blk must be bytes!"
        self.blk = blk
        self.hdr = self.parse_btc_hdr(hdr=blk[:80])
        self.data = blk[80:]
        blk = blk[80:]
        # tx_count, var_int
        #print("blk bytes start = ",blk[:9].hex())
        var_int = vint_to_int(blk[:9])
        #print("tx_count var_int = ",var_int)
        self.tx_count = var_int[1]
        self.tx_count_raw = blk[0:var_int[0]]
        blk = blk[var_int[0]:]
        #print("tx_n = ",tx_n)
        if tx_n is None:
            tx_n = self.tx_count
        assert tx_n <= self.tx_count,"Number of tx to parse higher than available tx!"
        #print("tx_count = ",self.tx_count)

        # txs, Bitcoin transactions
        self.txs = list()
        i = 0
        for i in range(0,tx_n):
            tx = BtcTx(rawbytes=blk)
            self.txs.append(tx)
            blk = blk[ tx.tx_len: ]
        return

class BtcTx:
    def __init__(self,rawbytes=None,
                      nVersion=None,
                      flag=None,
                      tx_in_cnt=None,
                      tx_in=None,
                      tx_out_cnt=None,
                      tx_out=None,
                      tx_wit=None,
                      nLockTime=None):
        if rawbytes is not None:
            self.parse_btc_tx(tx=rawbytes)
        else:
            self.nVersion=nVersion
            self.nVersion_raw=struct.pack("<l",nVersion) # int32_t
            self.flag=flag # 2 bytes
            self.tx_in_cnt=tx_in_cnt
            self.tx_in_cnt_raw=int_to_vint(tx_in_cnt) # var_int
            self.tx_in=tx_in
            self.tx_out_cnt=tx_out_cnt
            self.tx_out_cnt_raw=int_to_vint(tx_out_cnt) # var_int
            self.tx_out=tx_out
            self.tx_wit=tx_wit # TODO
            self.nLockTime=nLockTime
            self.nLockTime_raw=struct.pack("<L",nLockTime)
            self.txb = self.get_tx("bytes")
        self.txhash = dSHA256(self.txb)

    def parse_coinbase(self):
        """ Chekcs if this transaction is a valid coinbase transaction, and if so returns
        the block height encoded in the coinbase and the rest of the coinbase
        https://bitcoin.stackexchange.com/questions/20721/what-is-the-format-of-the-coinbase-transaction
        """
        assert len(self.tx_in) == 1, "Invalid number of tx inputs!"
        cb = self.tx_in[0]
        assert cb.prev_txhash == CB_TXHASH and cb.prev_txidx == CB_TXIDX, "Invalid tx input values!"
        blk_height_len = cb.script_sig[0]
        blk_height = int.from_bytes(cb.script_sig[1:1+blk_height_len],"little")
        assert 2 <= len(cb.script_sig) and len(cb.script_sig) <= 100, "Invalid coinbase length, must be between 2 and 100 bytes"

        # extract the raw coinbase transaction up to, but not including the coinbase
        assert self.flag is None and self.tx_wit is None, "Only works for non segwit coinbases"
        coinbasetx_prefix = ( self.nVersion_raw +
                              self.tx_in_cnt_raw +
                              cb.prev_output_raw +
                              cb.script_len_raw )

        # extract the rest of the raw coinbase transaction after the coinbase
        tx_out_raw = b""
        for tx in self.tx_out:
            tx_out_raw = tx_out_raw + tx.get_txout("bytes")
        coinbasetx_suffix = ( cb.sequence_raw +
                              self.tx_out_cnt_raw +
                              tx_out_raw +
                              self.nLockTime_raw )

        return {"blk_height":blk_height,
                "coinbase":cb.script_sig[1+blk_height_len:],
                "coinbase_full":cb.script_sig,
                "coinbasetx_prefix": coinbasetx_prefix,
                "coinbasetx_suffix": coinbasetx_suffix}

    def get_tx(self,outputformat="dict"):
        """ return tx data in specified format """
        tx_out_raw = b""
        for tx in self.tx_out:
            tx_out_raw = tx_out_raw + tx.get_txout("bytes")

        tx_in_raw = b""
        for tx in self.tx_in:
            tx_in_raw = tx_in_raw + tx.get_txin("bytes")


        if outputformat=="bytes":
            if self.flag is not None:
                return ( self.nVersion_raw +
                         self.flag +
                         self.tx_in_cnt_raw +
                         tx_in_raw +
                         self.tx_out_cnt_raw +
                         tx_out_raw +
                         self.tx_wit +
                         self.nLockTime_raw )
            else:
                return ( self.nVersion_raw +
                         self.tx_in_cnt_raw +
                         tx_in_raw +
                         self.tx_out_cnt_raw +
                         tx_out_raw +
                         self.nLockTime_raw )

        elif outputformat=="dict":
            return {"nVersion":self.nVersion,
                    "nVersion_raw":self.nVersion_raw,
                    "flag":self.flag,
                    "tx_in_cnt":self.tx_in_cnt,
                    "tx_in_cnt_raw":self.tx_in_cnt_raw,
                    "tx_in":self.tx_in,
                    "tx_out_cnt":self.tx_out_cnt,
                    "tx_out_cnt_raw":self.tx_out_cnt_raw,
                    "tx_out":self.tx_out,
                    "tx_wit":self.tx_wit,
                    "nLockTime":self.nLockTime,
                    "nLockTime_raw":self.nLockTime_raw,
                    "txb":self.txb,
                    "txhash":self.txhash
                   }
        else:
            assert False, "Wrong output format given, must be either 'dict' or 'bytes'"

    def parse_btc_tx(self,tx,tx_n=None):
        if type(tx) is bytes:
            tx_bytes_little = tx
        elif type(tx) is str:
            if tx[:2] == "0x":
                tx = tx[2:]
            tx_bytes_little = bytes.fromhex(tx)
        elif type(tx) is int:
            tx_bytes_little = tx.to_bytes(math.ceil(len(hex(tx)[2:])/2),"big")
        else:
            assert False,"Invalid tx type, must be bytes,str or int!"

        txb = tx_bytes_little
        # nVerison, 4 bytes
        self.nVersion = struct.unpack("<l",txb[0:4])[0] # int32_t
        self.nVersion_raw = txb[0:4]
        txb = txb[4:]
        self.tx_len = 4
        #print("nVersion = ",self.nVersion)
        #print("nVersion_raw = ",self.nVersion_raw)

        # flag if available, 0 or 2 bytes, if set must be \x00\x01 uint8_t[2]
        if txb[:2] == b"\x00\x01":
            self.flag_raw = txb[:2]
            self.flag = 1
            txb = txb[2:]
            self.tx_len += 2
            #print("Falg_raw = ",self.flag_raw)
        else:
            self.flag = None
            self.tx_wit = None

        # tx_in_cnt, var_int
        var_int = vint_to_int(txb[:9])
        self.tx_in_cnt = var_int[1]
        self.tx_in_cnt_raw = txb[ :var_int[0] ]
        txb = txb[ var_int[0]: ]
        self.tx_len += var_int[0]
        #print("tx_in_cnt = ",self.tx_in_cnt)
        #print("tx_in_cnt_raw = ",self.tx_in_cnt_raw)

        # tx_in, transaction input(s)
        self.tx_in = list()
        i = 0
        prev_txin_len = 0
        #print("tx_len = ",self.tx_len)
        for i in range(0,self.tx_in_cnt):
            txin = BtcTxIn(rawbytes=txb)
            self.tx_len += txin.tx_in_len
            self.tx_in.append(txin)
            prev_txin_len = txin.tx_in_len
            txb = txb[ prev_txin_len: ]

        #print("tx_len = ",self.tx_len)

        # tx_out_cnt, var_int
        var_int = vint_to_int(txb[:9])
        self.tx_out_cnt = var_int[1]
        self.tx_out_cnt_raw = txb[ :var_int[0] ]
        txb = txb[var_int[0]:]
        self.tx_len += var_int[0]
        #print("tx_out_cnt = ",self.tx_out_cnt)
        #print("tx_out_cnt_raw = ",self.tx_out_cnt)

        # tx_out, transaction output(s)
        self.tx_out = list()
        i = 0
        prev_txout_len = 0
        for i in range(0,self.tx_out_cnt):
            txout = BtcTxOut(rawbytes=txb)
            self.tx_len += txout.tx_out_len
            self.tx_out.append(txout)
            prev_txout_len = txout.tx_out_len
            txb = txb[ prev_txout_len: ]

        # tx_witnesses, if flag
        if self.flag is not None:
            # TODO witnesses
            assert False,"Witnesses not implemented"

        # lock_time, 4 bytes
        self.nLockTime = struct.unpack("<L",txb[0:4])[0]
        self.nLockTime_raw = txb[0:4]
        txb = txb[4:]
        self.tx_len += 4

        self.txb = tx_bytes_little[0:self.tx_len]
        return

class BtcTxIn:
    def __init__(self,rawbytes=None,
                      prev_txhash=None,
                      prev_txidx=None,
                      script_len=None,
                      script_sig=None,
                      sequence=None):
        if rawbytes is not None:
            self.parse_btc_txin(rawbytes=rawbytes)
        else:
            self.prev_txhash = prev_txhash
            self.prev_txidx = prev_txidx
            self.prev_output_raw = self.prev_txhash + struct.pack("<L",self.prev_txidx)
            self.script_len = script_len
            self.script_len_raw = int_to_vint(self.script_len)
            self.script_sig = script_sig
            self.sequence = sequence
            self.sequence_raw = struct.pack("<L",self.sequence)

    def get_txin(self,outputformat="dict"):
        """ return tx output in specified format """
        if outputformat=="bytes":
            return self.prev_output_raw + self.script_len_raw + self.script_sig + self.sequence_raw

        elif outputformat=="dict":
            return {"prev_txhash":self.prev_txhash,
                    "prev_txidx":self.prev_txidx,
                    "script_len":self.script_len,
                    "script_len_raw":self.script_len_raw,
                    "script_sig":self.script_sig,
                    "sequence":self.sequence,
                    "sequence_raw":self.sequence_raw,
                   }
        else:
            assert False, "Wrong output format given, must be either 'dict' or 'bytes'"

    def parse_btc_txin(self,rawbytes=None):
        assert rawbytes is not None,"rawbytes must not be None!"

        # prev_output, 32 + 4 bytes
        self.prev_output_raw = rawbytes[0:36]
        self.prev_txhash = rawbytes[0:32] # char[32]
        self.prev_txidx = struct.unpack("<L",rawbytes[32:36])[0] # uint32_t
        self.prev_txidx_raw = rawbytes[32:36]
        rawbytes = rawbytes[36:]
        self.tx_in_len = 36
        #print("prev_txhash = ",self.prev_txhash)
        #print("prev_txidx = ",self.prev_txidx)
        #print("prev_txidx_raw = ",self.prev_txidx_raw)

        # script lenght, var_int
        var_int = vint_to_int(rawbytes[0:9])
        self.script_len = var_int[1]
        self.script_len_raw = rawbytes[0:var_int[0]]
        rawbytes = rawbytes[var_int[0]:]
        self.tx_in_len += var_int[0] + var_int[1]
        #print("script_len = ",self.script_len)
        #print("script_len_raw = ",self.script_len_raw)

        # script signature, uchar[]
        self.script_sig = rawbytes[0:self.script_len]
        rawbytes = rawbytes[self.script_len:]
        #print("script_sig = ",self.script_sig)

        # sequence
        self.sequence = struct.unpack("<L",rawbytes[0:4])[0]
        self.sequence_raw = rawbytes[0:4]
        rawbytes = rawbytes[4:]
        self.tx_in_len += 4
        #print("sequence = ",self.sequence)
        #print("sequence_raw = ",self.sequence_raw)

        return rawbytes

class BtcTxOut:
    def __init__(self,rawbytes=None,
                  value=None,
                  script_len=None,
                  script_pk=None):

        if rawbytes is not None:
            self.parse_btc_txout(rawbytes=rawbytes)
        else:
            self.value = value
            self.value_raw = struct.pack("<Q",value)
            self.script_len = script_len
            self.script_len_raw = int_to_vint(self.script_len)
            self.script_pk = script_pk

    def get_txout(self,outputformat="dict"):
        """ return tx output in specified format """
        if outputformat=="bytes":
            return self.value_raw + self.script_len_raw + self.script_pk

        elif outputformat=="dict":
            return {"value":self.value,
                    "value_raw":self.value_raw,
                    "script_len":script_len,
                    "script_len_raw":script_len_raw,
                    "script_pk":script_pk,
                   }
        else:
            assert False, "Wrong output format given, must be either 'dict' or 'bytes'"

    def parse_btc_txout(self,rawbytes=None):
        assert rawbytes is not None,"rawbytes must not be None!"

        # value, 8 bytes
        self.value = struct.unpack("<Q",rawbytes[0:8])[0] # int64_t
        self.value_raw = rawbytes[0:8]
        rawbytes = rawbytes[8:]
        self.tx_out_len = 8

        # script length, var_int
        var_int = vint_to_int(rawbytes[0:9])
        self.script_len = var_int[1]
        self.script_len_raw = rawbytes[0:var_int[0]]
        rawbytes = rawbytes[var_int[0]:]
        self.tx_out_len += var_int[0] + var_int[1]

        # script pub. key, uchar[]
        self.script_pk = rawbytes[0:self.script_len]
        rawbytes = rawbytes[self.script_len:]
        return rawbytes

# --- Client ---
class EMRC:
    """ Ephemeral Mining Relay Client
    Deploys and manages an EMR
    """
    def __init__(self,host="172.18.0.2",port="8545"):
        self.host = host
        self.port = port
        self.w3 = None
        self.address = None
        self.instance = None

        self.gas_total = 0

        self.gas_deploy = 0
        self.gas_init = 0
        self.gas_attack = 0
        self.gas_payout = 0

        self.gas_submit_cblock = 0
        self.gas_number_cblocks = 0

        self.gas_submit_tblock = 0
        self.gas_number_tblocks = 0

        self.gas_submit_rblock = 0
        self.gas_number_rblocks = 0

        self.gas_number_payouts = 0

    def connect(self,path,compiler="/smartcode/contracts/solc",poa=False):
        """ connect to deployed contract """
        self.w3 = util.connect(host=self.host,
                     port=self.port,
                     poa=poa)
        # TODO connect to contract

    def deploy(self,path,compiler="solc",poa=False):
        """ connect and deploy contract """
        self.w3 = util.connect(host=self.host,
                     port=self.port,
                     poa=poa)
        assert self.w3.isConnected()
        tx_hash = util.compile_and_deploy_contract(path,
                                        compiler=compiler,
                                        wait=False,
                                        concise=False,
                                        patch_api=False,
                                        concise_events=False)
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        self.gas_total += tx_receipt["gasUsed"]
        self.gas_deploy += tx_receipt["gasUsed"]

        address = tx_receipt["contractAddress"]

        instance = util.get_contract_instance(address,None,path=path)
        assert address == instance.address
        self.instance = instance
        self.address = instance.address
        print("Deployed at: ",instance.address)
        return instance

    def init(self,startHeight,kV,kB,startHash):
        tx_hash = self.instance.functions.initEMR(startHeight,
                                                  kV,
                                                  kB,
                                                  startHash).transact(
            {"from":self.w3.eth.accounts[0],
             "value":0,
             "gas":1_000_000})
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        self.gas_total += tx_receipt["gasUsed"]
        self.gas_init += tx_receipt["gasUsed"]

        return self.check(1,startHeight,kV,kB,startHash,kV,kV+1)

    def submit_cblock(self,
                      blockHeader,
                      blockHeight,
                      blockReward,
                      blockMiner,
                      validityChecks=False):
        # TODO: implement validity checks
        r = self.instance.functions._remaining_init_cblocks().call()

        tx_hash = self.instance.functions.submit_cblock(blockHeader,
                                               blockHeight,
                                               blockReward,
                                               blockMiner).transact(
                {"from":self.w3.eth.accounts[0],
                 "value":blockReward})

        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        self.gas_total += tx_receipt["gasUsed"]
        self.gas_init += tx_receipt["gasUsed"]
        self.gas_submit_cblock += tx_receipt["gasUsed"]
        self.gas_number_cblocks += 1

        return self.check(1,remaining_init_cblocks=r-1)

    def submit_tblock(self,
                      blockHeader,
                      blockCoinbase_pfx,
                      blockHeight,
                      blockCoinbase_sfx,
                      merklePath,
                      blockReward,
                      blockBribe,
                      validityChecks=False):
        # TODO: implement validity checks
        ntb = self.instance.functions._number_tblocks().call()

        tx_hash = self.instance.functions.submit_tblock(blockHeader,
                                               blockCoinbase_pfx,
                                               blockHeight,
                                               blockCoinbase_sfx,
                                               merklePath,
                                               blockReward,
                                               blockBribe).transact(
                {"from":self.w3.eth.accounts[0],
                 "value":blockReward + blockBribe})
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        self.gas_total += tx_receipt["gasUsed"]
        if self.instance.functions._remaining_init_cblocks().call() > 0:
            self.gas_init += tx_receipt["gasUsed"]
        else:
            self.gas_attack += tx_receipt["gasUsed"]
        self.gas_submit_tblock += tx_receipt["gasUsed"]
        self.gas_number_tblocks += 1

        new_ntb = self.instance.functions._number_tblocks().call()
        if new_ntb == ntb+1:
            return True
        else:
            return False

    def get_tblock_data(self,blockHeight):
        return self.instance.functions.get_tblock_data(blockHeight).call()

    def submit_rblock(self,
                      blockHeader,
                      blockCoinbase,
                      blockCoinbase_pfx,
                      blockCoinbase_sfx,
                      merklePath,
                      account=None):
        if account is None:
            account = self.w3.eth.accounts[0]

        event_filter = self.instance.events.New_rblock.createFilter(fromBlock='latest')
        tx_hash = self.instance.functions.submit_rblock(blockHeader,
                                               blockCoinbase,
                                               blockCoinbase_pfx,
                                               blockCoinbase_sfx,
                                               merklePath).transact(
                {"from":account,
                 "value":0})
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)

        #print(tx_receipt)

        events = event_filter.get_new_entries()
        assert len(events) == 1 # only one event on this instance has occured
        e = events[0]
        assert e.event == 'New_rblock'
        assert e.args._rblockHash == endSwap(dSHA256(blockHeader,raw=True))

        self.gas_total += tx_receipt["gasUsed"]
        self.gas_attack += tx_receipt["gasUsed"]
        self.gas_submit_rblock += tx_receipt["gasUsed"]
        self.gas_number_rblocks += 1

        return True

    def payout(self,account=None):
        if ( account is None):
            account = self.w3.eth.accounts[0]
        balance_account_before = self.w3.eth.getBalance(account)
        balance_contract_before = self.w3.eth.getBalance(self.instance.address)

        tx_hash = self.instance.functions.payout().transact(
                {"from":account,
                 "value":0})
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        tx_info = self.w3.eth.getTransaction(tx_hash)

        balance_account_after = self.w3.eth.getBalance(account)
        balance_contract_after = self.w3.eth.getBalance(self.instance.address)

        self.gas_total += tx_receipt["gasUsed"]
        self.gas_payout += tx_receipt["gasUsed"]
        self.gas_number_payouts += 1

        #assert balance_account_before < balance_account_after
        #assert balance_contract_before > balance_contract_after
        return balance_account_after - balance_account_before + tx_receipt["gasUsed"]*tx_info["gasPrice"]

    def check(self,
              currentState=None,
              startHeight=None,
              kV=None,
              kB=None,
              startHash=None,
              remaining_init_cblocks=None,
              remaining_init_tblocks=None,
              printvalues=False):
        """ Helper function the gets and checks state of contract """
        r = self.instance.functions.get_currentState().call()
        if printvalues:
            print("currentState = ",r)
        if currentState is not None:
            assert r == currentState

        r = self.instance.functions._startHeight().call()
        if startHash is not None:
            assert r == startHeight

        r = self.instance.functions._kV().call()
        if kV is not None:
            assert r == kV

        r = self.instance.functions._kB().call()
        if kB is not None:
            assert r == kB

        r = self.instance.functions._startHash().call()
        if startHash is not None:
            assert r == startHash

        r = self.instance.functions._remaining_init_cblocks().call()
        if remaining_init_cblocks is not None:
            assert r == remaining_init_cblocks

        r = self.instance.functions._remaining_init_tblocks().call()
        if remaining_init_tblocks is not None:
            assert r == remaining_init_tblocks

        return True

    def printGasStats(self,gwei=12*10**9,exr=160.53):
        # gwei = gasPrice in Gwei
        # exr = exchangeRate 1 ETH -> USD
        print()
        print("Gas stats:")
        print("\tdeploy  = {:10,d}  gas  {:10,.2f}  USD".format(self.gas_deploy,
                                                                self.gas_deploy*gwei*(10**-18)*exr))
        print("\tinit    = {:10,d}  gas  {:10,.2f}  USD".format(self.gas_init,
                                                                self.gas_init*gwei*(10**-18)*exr))
        print("\tattack  = {:10,d}  gas  {:10,.2f}  USD".format(self.gas_attack,
                                                                self.gas_attack*gwei*(10**-18)*exr))
        print("\tpayout  = {:10,d}  gas  {:10,.2f}  USD".format(self.gas_payout,
                                                                self.gas_payout*gwei*(10**-18)*exr))
        print("\t--------------------")
        print("\ttotal   = {:10,d}  gas  {:10,.2f}  USD".format(self.gas_total,
                                                                self.gas_total*gwei*(10**-18)*exr))
        print()
        print("\tcblocks = {:10,d}  gas  {:10,.2f}  USD".format(self.gas_submit_cblock,
                                                                self.gas_submit_cblock*gwei*(10**-18)*exr))
        print("\tn_c     = {:10,d}  ".format(self.gas_number_cblocks))
        if self.gas_number_cblocks > 0:
            print("\tcblock  = {:10,.0f}  gas  {:10,.2f}  USD".format(self.gas_submit_cblock / self.gas_number_cblocks,
                                                                      (self.gas_submit_cblock / self.gas_number_cblocks)*gwei*(10**-18)*exr))
        print()
        print("\ttblocks = {:10,d}  gas  {:10,.2f}  USD".format(self.gas_submit_tblock,
                                                                self.gas_submit_tblock*gwei*(10**-18)*exr))
        print("\tn_t     = {:10,d}".format(self.gas_number_tblocks))
        if self.gas_number_tblocks > 0:
            print("\ttblock  = {:10,.0f}  gas  {:10,.2f}  USD".format(self.gas_submit_tblock / self.gas_number_tblocks,
                                                                      (self.gas_submit_tblock / self.gas_number_tblocks)*gwei*(10**-18)*exr))
        print()
        print("\trblocks = {:10,d}  gas  {:10,.2f}  USD".format(self.gas_submit_rblock,
                                                                self.gas_submit_rblock*gwei*(10**-18)*exr))
        print("\tn_r     = {:10,d}".format(self.gas_number_rblocks,grouping=True))
        if self.gas_number_rblocks > 0:
            print("\trblock  = {:10,.0f}  gas  {:10,.2f}  USD".format(self.gas_submit_rblock / self.gas_number_rblocks,
                                                                      (self.gas_submit_rblock / self.gas_number_rblocks)*gwei*(10**-18)*exr))

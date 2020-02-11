import web3
import util
import client
import pytest

def test_deploy():
    EMRC = client.EMRC()
    inst = EMRC.deploy("/smartcode/contracts/EMR.sol")
    print("Tmp instance: ", inst.address)

@pytest.fixture(scope="module") # only execute once for this module
def emrc():
    EMRC = client.EMRC()
    inst = EMRC.deploy("/smartcode/contracts/EMR.sol")
    print("Test instance: ",inst.address)
    assert EMRC.instance.address == inst.address
    assert inst.functions.get_currentState().call() == 0
    return EMRC
    #return EMRC.instance

def test_getVersionFromHeader(emrc):
    blkhdr_300000 = 0x020000007ef055e1674d2e6551dba41cd214debbee34aeb544c7ec670000000000000000d3998963f80c5bab43fe8c26228e98d030edf4dcbe48a666f5c39e2d7a885c9102c86d536c890019593a470d
    blkhdr_300000_big = blkhdr_300000.to_bytes(80,"big")

    #print("Chk instance: ",emrc.instance.address)
    hdrversion = emrc.instance.functions.getVersionFromHeader(blkhdr_300000_big).call()
    print("Parsed version: ",hdrversion)
    assert 2 == hdrversion

def test_getPrevBlockHash(emrc):
    blkhdr_300000 = 0x020000007ef055e1674d2e6551dba41cd214debbee34aeb544c7ec670000000000000000d3998963f80c5bab43fe8c26228e98d030edf4dcbe48a666f5c39e2d7a885c9102c86d536c890019593a470d
    blkhdr_300000_big = blkhdr_300000.to_bytes(80,"big")

    #print("Chk instance: ",emrc.instance.address)
    hdrPrevBlockHash = emrc.instance.functions.getPrevBlockHash(blkhdr_300000_big).call()
    print("Parsed PrevBlockHash: ",hdrPrevBlockHash)
    assert b'\x00\x00\x00\x00\x00\x00\x00\x00g\xec\xc7D\xb5\xae4\xee\xbb\xde\x14\xd2\x1c\xa4\xdbQe.Mg\xe1U\xf0~' == hdrPrevBlockHash

def test_getMerkleRoot(emrc):
    blkhdr_300000 = 0x020000007ef055e1674d2e6551dba41cd214debbee34aeb544c7ec670000000000000000d3998963f80c5bab43fe8c26228e98d030edf4dcbe48a666f5c39e2d7a885c9102c86d536c890019593a470d
    blkhdr_300000_big = blkhdr_300000.to_bytes(80,"big")

    #print("Chk instance: ",emrc.instance.address)
    hdrmkr = emrc.instance.functions.getMerkleRoot(blkhdr_300000_big).call()
    print("Parsed Merkle root: ",hdrmkr)
    assert b'\x91\\\x88z-\x9e\xc3\xf5f\xa6H\xbe\xdc\xf4\xed0\xd0\x98\x8e"&\x8c\xfeC\xab[\x0c\xf8c\x89\x99\xd3' == hdrmkr

def test_getTimeFromHeader(emrc):
    blkhdr_300000 = 0x020000007ef055e1674d2e6551dba41cd214debbee34aeb544c7ec670000000000000000d3998963f80c5bab43fe8c26228e98d030edf4dcbe48a666f5c39e2d7a885c9102c86d536c890019593a470d
    blkhdr_300000_big = blkhdr_300000.to_bytes(80,"big")

    #print("Chk instance: ",emrc.instance.address)
    hdrtime = emrc.instance.functions.getTimeFromHeader(blkhdr_300000_big).call()
    print("Parsed time: ",hdrtime)
    assert 1399703554 == hdrtime

def test_getNBitsFromHeader(emrc):
    blkhdr_300000 = 0x020000007ef055e1674d2e6551dba41cd214debbee34aeb544c7ec670000000000000000d3998963f80c5bab43fe8c26228e98d030edf4dcbe48a666f5c39e2d7a885c9102c86d536c890019593a470d
    blkhdr_300000_big = blkhdr_300000.to_bytes(80,"big")

    #print("Chk instance: ",emrc.instance.address)
    hdrNBits = emrc.instance.functions.getNBitsFromHeader(blkhdr_300000_big).call()
    print("Parsed nbits: ",hdrNBits)
    assert 419465580 == hdrNBits

def test_getNNonceFromHeader(emrc):
    blkhdr_300000 = 0x020000007ef055e1674d2e6551dba41cd214debbee34aeb544c7ec670000000000000000d3998963f80c5bab43fe8c26228e98d030edf4dcbe48a666f5c39e2d7a885c9102c86d536c890019593a470d
    blkhdr_300000_big = blkhdr_300000.to_bytes(80,"big")

    #print("Chk instance: ",emrc.instance.address)
    hdrNNonce = emrc.instance.functions.getNNonceFromHeader(blkhdr_300000_big).call()
    print("Parsed nonce: ",hdrNNonce)
    assert 222771801 == hdrNNonce

def test_getTargetFromHeader(emrc):
    blkhdr_300000 = 0x020000007ef055e1674d2e6551dba41cd214debbee34aeb544c7ec670000000000000000d3998963f80c5bab43fe8c26228e98d030edf4dcbe48a666f5c39e2d7a885c9102c86d536c890019593a470d
    blkhdr_300000_big = blkhdr_300000.to_bytes(80,"big")

    hdrTarget = emrc.instance.functions.getTargetFromHeader(blkhdr_300000_big).call()
    assert 3369574570478873127315415525946742317481702644901195284480 == hdrTarget

def test_getHeightFromCoinbase(emrc):
    cb = b'\x03\xe0\x93\x04\x06/P2SH/\x04\x03\xc8mS\x08|\xec\xa1A)Z\x00\x00.R,\xfa\xbemmua\xcf&#\x13\xda\x11D\x02l\x8fzC\xe3\x89\x9cD\xf6\x14_9\xa3e\x07\xd3fy\xa8\xb7\x00a\x04\x00\x00\x00\x00\x00\x00\x00'
    # 0x0493e0 = 300000
    assert 300000 == emrc.instance.functions.getHeightFromCoinbase(cb).call()

def test_getAddressFromCoinbase(emrc):
    cb = b'\x03\xe0\x93\x04\xf0\t\xc4iW\xef^\xb3($T\\\x1b\xc1*\xe7\xde\x8f\xcf\xff'
    #assert b'\xf0\t\xc4iW\xef^\xb3($T\\\x1b\xc1*\xe7\xde\x8f\xcf\xff' == emrc.instance.functions.getAddressFromCoinbase(cb).call()
    assert '0xFFcf8FDEE72ac11b5c542428B35EEF5769C409f0' == emrc.instance.functions.getAddressFromCoinbase(cb).call()

def test_setMerkleRoot(emrc):
    hdr = b'\x02\x00\x00\x00~\xf0U\xe1gM.eQ\xdb\xa4\x1c\xd2\x14\xde\xbb\xee4\xae\xb5D\xc7\xecg\x00\x00\x00\x00\x00\x00\x00\x00\xd3\x99\x89c\xf8\x0c[\xabC\xfe\x8c&"\x8e\x98\xd00\xed\xf4\xdc\xbeH\xa6f\xf5\xc3\x9e-z\x88\\\x91\x02\xc8mSl\x89\x00\x19Y:G\r'
    hdr_new = b'\x02\x00\x00\x00~\xf0U\xe1gM.eQ\xdb\xa4\x1c\xd2\x14\xde\xbb\xee4\xae\xb5D\xc7\xecg\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xc8mSl\x89\x00\x19Y:G\r'

    assert hdr_new == emrc.instance.functions.setMerkleRoot(hdr).call()

def test_dblSha(emrc):
    blkhdr_300000 = 0x020000007ef055e1674d2e6551dba41cd214debbee34aeb544c7ec670000000000000000d3998963f80c5bab43fe8c26228e98d030edf4dcbe48a666f5c39e2d7a885c9102c86d536c890019593a470d

    blkhdr_300000_bytes_big = blkhdr_300000.to_bytes(80,"big")

    dsha_contract = emrc.instance.functions.dblSha( blkhdr_300000_bytes_big ).call()
    print("dSHA contract: ",dsha_contract)
    dsha_client = client.dSHA256( blkhdr_300000_bytes_big )
    print("dSHA client  : ",dsha_client)
    assert dsha_client == "000000000000000082ccf8f1557c5d40b21edabb18d2d691cfbf87118bac7254"
    assert dsha_contract ==  client.dSHA256( blkhdr_300000_bytes_big, raw=True )

def test_init_manually(emrc):
    hash_1_str = '000000000000000082ccf8f1557c5d40b21edabb18d2d691cfbf87118bac7254'
    #hash_1_bytes = client.hexstr_to_dbytes(hash_1_str,swap=True)
    hash_1_bytes = client.hexstr_to_dbytes(hash_1_str,swap=False)

    # test manual init
    tx_hash = emrc.instance.functions.initEMR(300000,2,6,hash_1_bytes).transact(
        {"from":emrc.w3.eth.accounts[0],
         "value":0,
         "gas":1_000_000})
    tx_receipt = emrc.w3.eth.waitForTransactionReceipt(tx_hash)

    emrc.check(1,300000,2,6,hash_1_bytes,2,3)

    event_filter = emrc.instance.events.Init_start.createFilter(fromBlock='latest')
    events = emrc.instance.events.Init_start().processReceipt(tx_receipt)
    assert len(events) == 1 # only one event on this instance has occured
    e = events[0]
    assert e.event == 'Init_start'
    assert e.args["_startHeight"] == 300000
    assert e.args["_kV"] == 2
    assert e.args["_startHash"] == hash_1_bytes

    # negative test, reinitialized contract
    with pytest.raises(ValueError):
        tx_hash = emrc.instance.functions.initEMR(300000,2,6,hash_1_bytes).transact(
            {"from":emrc.w3.eth.accounts[0],
             "value":0,
             "gas":1_000_000})

def test_submit_cblocks_manually(emrc):
    blockHeader_1 = b'\x02\x00\x00\x00Tr\xac\x8b\x11\x87\xbf\xcf\x91\xd6\xd2\x18\xbb\xda\x1e\xb2@]|U\xf1\xf8\xcc\x82\x00\x00\x00\x00\x00\x00\x00\x00\xab\n\xaa7|\xa3\xf4\x9b\x15E\xe2\xaek\x06g\xa0\x8fB\xe7-\x8c$\xae#q@\xe2\x8f\x14\xf3\xbb|k\xccmSl\x89\x00\x19\xed\xd8<\xcf'

    hdrPrevBlockHash = emrc.instance.functions.getPrevBlockHash(blockHeader_1).call()
    print("Parsed PrevBlockHash: ",hdrPrevBlockHash.hex())
    assert hdrPrevBlockHash == b'\x00\x00\x00\x00\x00\x00\x00\x00\x82\xcc\xf8\xf1U|]@\xb2\x1e\xda\xbb\x18\xd2\xd6\x91\xcf\xbf\x87\x11\x8b\xacrT'

    blockHeight_1 = 300001
    blockReward_1 = 1250000000
    blockMiner_1 = '0x22d491Bde2303f2f43325b2108D26f1eAbA1e32b'

    blockHeader_2 = b'\x02\x00\x00\x00\xa9\xab\x12\xe3,\xed\xdc+\xa5\xe6\xade\x1f\xacw,\x986\xdf\x83M\x91\xa0I\x00\x00\x00\x00\x00\x00\x00\x00\xdfuu\xc7\x8f\x83\x1f \xaf\x14~\xa7T\xe5\x84\xaa\xd9Yeiic-\xa9x\xd2\xddq\x86#\xfd0\xc5\xccmSl\x89\x00\x19\xe6Q\x07\xe9'

    hdrPrevBlockHash = emrc.instance.functions.getPrevBlockHash(blockHeader_2).call()
    print("Parsed PrevBlockHash: ",hdrPrevBlockHash.hex())
    assert hdrPrevBlockHash == b'\x00\x00\x00\x00\x00\x00\x00\x00I\xa0\x91M\x83\xdf6\x98,w\xac\x1fe\xad\xe6\xa5+\xdc\xed,\xe3\x12\xab\xa9'

    blockHeight_2 = 300002
    blockReward_2 = 1250000000
    blockMiner_2 = '0x22d491Bde2303f2f43325b2108D26f1eAbA1e32b'

    assert emrc.instance.functions.submit_cblock(blockHeader_1,
                                                 blockHeight_1,
                                                 blockReward_1,
                                                 blockMiner_1).transact(
            {"from":emrc.w3.eth.accounts[0],
             "value":blockReward_1,
             "gas":1_000_000})


    assert emrc.instance.functions.submit_cblock(blockHeader_2,
                                                 blockHeight_2,
                                                 blockReward_2,
                                                 blockMiner_2).transact(
            {"from":emrc.w3.eth.accounts[0],
             "value":blockReward_2,
             "gas":1_000_000})


def test_submit_tblocks_manually(emrc):
    #tblockHeader_1 = b'\x02\x00\x00\x00Tr\xac\x8b\x11\x87\xbf\xcf\x91\xd6\xd2\x18\xbb\xda\x1e\xb2@]|U\xf1\xf8\xcc\x82\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00k\xccmSl\x89\x00\x19\xed\xd8<\xcf'
    tblockHeader_1 = b'\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00k\xccmSl\x89\x00\x19\xed\xd8<\xcf'

    hdrPrevBlockHash = emrc.instance.functions.getPrevBlockHash(tblockHeader_1).call()
    print("Parsed PrevBlockHash: ",hdrPrevBlockHash.hex())
    assert hdrPrevBlockHash == b'\x00'*32

    # cheack hash value
    mroot = b'\xab\n\xaa7|\xa3\xf4\x9b\x15E\xe2\xaek\x06g\xa0\x8fB\xe7-\x8c$\xae#q@\xe2\x8f\x14\xf3\xbb|'
    offset = client.NVERSION_LEN + client.HASHPREVBLOCK_LEN
    undone_header = client.replace_at_offset(tblockHeader_1,offset,replace=mroot)
    offset = client.NVERSION_LEN
    phash = b'Tr\xac\x8b\x11\x87\xbf\xcf\x91\xd6\xd2\x18\xbb\xda\x1e\xb2@]|U\xf1\xf8\xcc\x82\x00\x00\x00\x00\x00\x00\x00\x00'
    undone_header = client.replace_at_offset(undone_header,offset,replace=phash)
    assert client.dSHA256(undone_header,raw=True) == b'\xa9\xab\x12\xe3,\xed\xdc+\xa5\xe6\xade\x1f\xacw,\x986\xdf\x83M\x91\xa0I\x00\x00\x00\x00\x00\x00\x00\x00'

    tblockHeight_1 = 300001
    tblockCoinbase_pfx_1 = b'\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\x11'
    tblockCoinbase = b'\x03\xe1\x93\x04\x04Sm\xcckG\r\x00\x005J\x03\x00'
    tblockCoinbase_sfx_1 = b'\xff\xff\xff\xff\x02\x01\x00\x00\x00\x00\x00\x00\x00\x19v\xa9\x14p\xa4\x193j\xe6\x04\xdd\xf7>O\x81\x99\xf1\xd0;</&\x0b\x88\xac\x1a;\x91\x95\x00\x00\x00\x00\x19v\xa9\x14c\xdd\x7f\x90\xe9I\xf8\xe3TAR3\xe5\x1d3\x92\xd4\xd8\xf5R\x88\xac\x00\x00\x00\x00'
    merklePath_1 = [b'\x89\xc8\xad\xae\xdd\xf41\xd7\x07\x99=\xb7$\x1b\\o]\x9a\xd1\x0e\xdeKg\xa6~\xc6\x01\xf9\x14\xbe\xe6I',
                    b'TR\xca\\\xf6\xc6\xaf}\x8bjIS\x1d\x990Q\xd3\x97\xfa\x96\xe64]\x0b\x8cro\x15X]\xb3\xf0',
                    b'.A\x86\x19\\\xf0\x8fV0\xf0\x89\xcc\n\x89\xb1x]m\xb6r u\xca\xcc\x82\x19\x16\xb4\xdb\xd52U',
                    b'lq=+\x8ezd\xe1E\x1e0\xff\x0ckM\x82\x84#\x81]3\xcc\xe3\xc8e\xe5\xc6\xb4\xd7\x83M*',
                    b' \xa9\x8b\xe5\xe0\x81\x86sc\xea\x1095\xa5\xc9\xcf\xd0T\x1e\x19^\xc5\xee\xc79;\xa3~\xe3\xbd*\x84',
                    b'\x87\xbe"P1\xff\xf8\xcaN\x04\xfd\x15iQ\xbc\xf9\x1e\t\xae\xbb\xb8\xd7\x83`\xa4\xdbX\r9l\x08\xb1',
                    b'^\x97a\xb6\xc9\xcc\xb3\xb7\xbd\x16/\xdc\xe7\xdc\xde\x96\xb5C\xea/l\xfc^\xe8\xc8\xb2\xc8\x94X\xb6i\xe0',
                    b'K$0%\xc0\x7f\x17\xb5\x17\xfa=\xe6\xb3\xd0Z?7\xf5\xd5\xce\x85\x92\rYo\xd5\xfeGV\xe3\xc7\xb8',
                    b'#\xc4_\xe0\xbe\xc9\xbe0\xa5\xff"\x11X\xeb\xaf\xf4\xfdc\x85M_h~h\x9c\x17\x95\xcf9\n\x1b\x8e']
    tblock_merklePath_1 = b''.join(merklePath_1)

    # check hash from coinbase, and if its in merkle path
    cb_tx = b"".join([ tblockCoinbase_pfx_1, tblockCoinbase, tblockCoinbase_sfx_1])

    cb_tx_hash = client.dSHA256(cb_tx,raw=True)
    assert client.dSHA256(cb_tx) == "6e7bdd5347d6603f58125b76a5ae48a6575ec44f6942d91290a1473972f5aec6"

    assert client.dbytes_to_hexstr(b'\xab\n\xaa7|\xa3\xf4\x9b\x15E\xe2\xaek\x06g\xa0\x8fB\xe7-\x8c$\xae#q@\xe2\x8f\x14\xf3\xbb|') == '7cbbf3148fe2407123ae248c2de7428fa067066baee245159bf4a37c37aa0aab'
    mroot = '7cbbf3148fe2407123ae248c2de7428fa067066baee245159bf4a37c37aa0aab'
    # create list of all ones for verify coinbase, length is given by merklPath
    assert client.vrfy_root_path(mroot,
                                 client.dSHA256(cb_tx),
                                 merklePath_1.copy(),
                                 flags=[ 1 for i in range(0,len(merklePath_1)) ])

    tblockReward_1=1*10**18
    tblockBribe_1=1*10**18



    event_filter = emrc.instance.events.New_tblock.createFilter(fromBlock='latest')

    assert emrc.submit_tblock(tblockHeader_1,
                       tblockCoinbase_pfx_1,
                       tblockHeight_1,
                       tblockCoinbase_sfx_1,
                       tblock_merklePath_1,
                       tblockReward_1,
                       tblockBribe_1)

    # Check data stored in contract
    tblock_data = emrc.get_tblock_data(tblockHeight_1)
    assert tblock_data[0] == False # mined
    assert tblock_data[1] == tblockReward_1
    assert tblock_data[2] == tblockBribe_1
    # endianness of alls stored hashes is inverted because returned like that form header parseing functions
    assert tblock_data[3] == client.endSwap(client.dSHA256(tblockHeader_1,raw=True))
    assert tblock_data[4] == client.endSwap(client.dSHA256(tblock_merklePath_1,raw=True))
    assert tblock_data[5] == client.endSwap(client.dSHA256(tblockCoinbase_pfx_1,raw=True))
    assert tblock_data[6] == client.endSwap(client.dSHA256(tblockCoinbase_sfx_1,raw=True))

    # Check event data, only submitted not stored
    events = event_filter.get_new_entries()
    assert len(events) == 1 # only one event on this instance has occured
    e = events[0]
    assert e.event == 'New_tblock'
    assert e.args["_blockHeight"] == tblockHeight_1
    assert e.args["_blockReward"] == tblockReward_1
    assert e.args["_blockBribe"] == tblockBribe_1

    # Data not stored only emitted:
    assert e.args._tblockHeader == tblockHeader_1
    assert e.args["_blockCoinbase_prefix"] == tblockCoinbase_pfx_1
    assert e.args["_blockCoinbase_suffix"] == tblockCoinbase_sfx_1
    assert e.args["_merklePath"] == tblock_merklePath_1

    assert emrc.instance.functions._currentState().call() == 1
    assert emrc.instance.functions._remaining_init_tblocks().call() == 2
    assert emrc.instance.functions._number_tblocks().call() == 1

    #Submit two more tblocks
    #tblockHeader_2 = b'\x02\x00\x00\x00\xa9\xab\x12\xe3,\xed\xdc+\xa5\xe6\xade\x1f\xacw,\x986\xdf\x83M\x91\xa0I\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc5\xccmSl\x89\x00\x19\xe6Q\x07\xe9'
    tblockHeader_2 = b'\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc5\xccmSl\x89\x00\x19\xe6Q\x07\xe9'

    tblockCoinbase_pfx_2 = b'\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xffH'
    tblockHeight_2 = 300002
    tblockCoinbase_sfx_2 = b'\x00\x00\x00\x00\x01\x0f\x84+\x95\x00\x00\x00\x00\x19v\xa9\x14\x80\xad\x90\xd4\x03X\x1f\xa3\xbfF\x08j\x91\xb2\xd9\xd4\x12]\xb6\xc1\x88\xac\x00\x00\x00\x00'
    tblock_merklePath_2 = b'\x92\xa1\x18\xcf5\xa6\xc4Qz5\xc5M\xd2[Z\x18\xd9\x8e\x82\x1c\xf4\x18\xfcW9\xc2\xcb\xe1\xc5F\x13\x13\xc6\xcd\xeb\xf5H\x12\x01R\xf7l>h\xd7\xe0\xbe\x91~f\x98\xd6\x82\xce\xb4\x0ecOJ\x05\xdcHE\xeb\x9e<a*\xad\r\x9c"b(Oft6\xe7\xe8J\x89U\x94\x08eN\xc6\x07\xb0\xa8V\xb5\xc0b\x0b(\x81\xdd\xa5\x1e8\xc4^i>6\xec\xd3\xe2\x08`\xb9\xb4x\xf6g{\xf8\x1b3\x7f\xa8\xc1b\x11\x88\xd0\xab\x9a\xfdi\xaal\xf1\xa5\xb7\x9a\xd1\xde\x7f\x8d\x8eq\xbf^&\xb6hig{\'t\xb2\xfd\xfc\xbf\xe9\x91\x11\xfc\x86){R\x1f\x9b\xd0\x0e\xd7\x02\xa5\x1b\xf22\xe4R\xba\xfb-4\x10\xbb\xdf\xb4\xc62\\\x94\x1b\xfb\x88j=\xd5\x9e\x84\xaf\x04\x89\x1f\xde{v\x12\xc7\xe6T\xe9\x15\xf6;:\xb1\r#\xcb,\xb8O\xe85G'
    tblockReward_2 = 10**18
    tblockBribe_2 = 10**18

    event_filter = emrc.instance.events.New_tblock.createFilter(fromBlock='latest')
    assert emrc.submit_tblock(tblockHeader_2,
                       tblockCoinbase_pfx_2,
                       tblockHeight_2,
                       tblockCoinbase_sfx_2,
                       tblock_merklePath_2,
                       tblockReward_2,
                       tblockBribe_2)
    events = event_filter.get_new_entries()
    assert len(events) == 1 # only one event on this instance has occured
    e = events[0]
    assert e.event == 'New_tblock'
    assert e.args._tblockHeader == tblockHeader_2

    assert emrc.instance.functions._currentState().call() == 1
    assert emrc.instance.functions._remaining_init_tblocks().call() == 1
    assert emrc.instance.functions._number_tblocks().call() == 2

    #tblockHeader_3 = b"\x02\x00\x00\x00,P\x1f\xc0\xb0\xfd\xe9\xb3\xc1\x0e#S\xc1TI*5k\x1a\x02)^+\x86\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\xcemSl\x89\x00\x19\xa4\xa0<{"
    tblockHeader_3 = b"\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\xcemSl\x89\x00\x19\xa4\xa0<{"
    tblockCoinbase_pfx_3 = b'\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff('
    tblockHeight_3 = 300003
    tblockCoinbase_sfx_3 = b'\x00\x00\x00\x00\x01\x99/-\x95\x00\x00\x00\x00\x19v\xa9\x14k\xe3\x18\xf5|\xcd[\x85\xd7\xee\x9c\xc1Z<]\xa4\xf9\x80d\xaf\x88\xac\x00\x00\x00\x00'
    tblock_merklePath_3 = b'\x14\xb7\x8f\xbc\xf5\x07\x17.\xa4\x92\x1c\xffJ8\xac\x16\xaf\xd3t\xadm-s\xefe\x89\xa6\xb2\xa2\x07\xbd\xe8y\x82\x1b\x92\x83o\xf1\x10\xd1P\xd0\x16=7e\x1f\x1e\xe0X\x18\x8d\x99\xb1D"\xa4:N-\xb8#\xc4\x06\xd9\xe3\xf2\xd7\x15\x8c\xda\xe5\xf0\x1b\xdd\x05\xff\xf6\xbea\x1d\xfb\xbd6\x1e\'\xba\xf2\x17$W\xdb\x9a%\x1e\xbe\x1d\xf2M1\xfe\xc1)\xddE\xe4\xa5A@3\xa3\xf1\xcd\x9dOi:\x18Y\xfc\xbd\x8b\xed\r3@r\x13\xf4A\x80\xa75\xc4\xeer\x92\x10\xae\x92`\xd8u\xb5|p\xce2\xcawr<u\xbf\x0f\xcd\xb0V.S\x83\x93\xee\xc1\xc4\xe2.\x18\np\x1d\xfc\x99\x8f\xc8\xb6(@n\xd2{\xf6\x13\xb0=\xdb\xf7N-\xf18\xb7aoxD1\xec\x96}\xba\x81\x8f);\xe4\xa7/\xb8\xac\xea\x1eS\x9e\xd3\xdf\xd1?K9\x11O\xe1\x15,\xea)eMz\x872\xc5\xad\xec\x9e\xcfR2@\xb4LQ\xd9`r\xfe\x0c\xed\xb1\x8c}\xefL\xee'
    tblockReward_3 = 10**18
    tblockBribe_3 = 10**18

    event_filter = emrc.instance.events.New_tblock.createFilter(fromBlock='latest')
    assert emrc.submit_tblock(tblockHeader_3,
                       tblockCoinbase_pfx_3,
                       tblockHeight_3,
                       tblockCoinbase_sfx_3,
                       tblock_merklePath_3,
                       tblockReward_3,
                       tblockBribe_3)
    events = event_filter.get_new_entries()
    assert len(events) == 1 # only one event on this instance has occured
    e = events[0]
    assert e.event == 'New_tblock'
    assert e.args._tblockHeader == tblockHeader_3

    assert emrc.instance.functions._currentState().call() == 2
    assert emrc.instance.functions._remaining_init_tblocks().call() == 0
    assert emrc.instance.functions._number_tblocks().call() == 3


def test_submit_rblocks_manually(emrc):
    assert emrc.instance.functions._currentState().call() == 2

    blks_3K_9 = client.load_input_blocks("../testdata/btc_blocks_json_samples/300000--300015")
    b0 = client.get_input_block_calldata(blks_3K_9,0)
    b1 = client.get_input_block_calldata(blks_3K_9,1)
    b2 = client.get_input_block_calldata(blks_3K_9,2)
    b3 = client.get_input_block_calldata(blks_3K_9,3)
    b4 = client.get_input_block_calldata(blks_3K_9,4)
    b5 = client.get_input_block_calldata(blks_3K_9,5)
    b6 = client.get_input_block_calldata(blks_3K_9,6)
    b7 = client.get_input_block_calldata(blks_3K_9,7)
    b8 = client.get_input_block_calldata(blks_3K_9,8)
    b9 = client.get_input_block_calldata(blks_3K_9,9)
    b10 = client.get_input_block_calldata(blks_3K_9,10)
    b11 = client.get_input_block_calldata(blks_3K_9,11)
    b12 = client.get_input_block_calldata(blks_3K_9,12)

    BLOCK_REWARD=int(12.5*10**18)
    BLOCK_BRIBE=int(1*10**18)

    briber = emrc.w3.eth.accounts[0]
    bribee = emrc.w3.eth.accounts[1]
    mainchainminer = emrc.w3.eth.accounts[2]

    rblockHeader_1 = b1["blockHeader_bytes_big"]
    rblockCoinbase_1 = b1["cb"]
    rblockCoinbase_pfx_1 = b1["cb_pfx"]
    rblockCoinbase_sfx_1 = b1["cb_sfx"]
    rblock_merklePath_1 = b1["mp_hashes_bytes_big"]
    event_filter = emrc.instance.events.New_rblock.createFilter(fromBlock='latest')
    assert emrc.submit_rblock(rblockHeader_1,
                              rblockCoinbase_1,
                              rblockCoinbase_pfx_1,
                              rblockCoinbase_sfx_1,
                              rblock_merklePath_1,
                              bribee)

    #event_filter.get_all_entries()
    events = event_filter.get_new_entries()
    assert len(events) == 1 # only one event on this instance has occured
    e = events[0]
    assert e.event == 'New_rblock'
    assert e.args._rblockHash == client.endSwap(client.dSHA256(rblockHeader_1,raw=True))
    assert e.args._blockHeight == b1["blockHeight"]
    #assert e.args._tblockHash ==
    assert emrc.instance.functions._currentState().call() == 2
    #assert emrc.w3.eth.getBalance(emrc.instance.address) ==  BLOCK_REWARD + BLOCK_BRIBE


    rblockHeader_2 = b2["blockHeader_bytes_big"]
    rblockCoinbase_2 = b2["cb"]
    rblockCoinbase_pfx_2 = b2["cb_pfx"]
    rblockCoinbase_sfx_2 = b2["cb_sfx"]
    rblock_merklePath_2 = b2["mp_hashes_bytes_big"]
    event_filter = emrc.instance.events.New_rblock.createFilter(fromBlock='latest')
    assert emrc.submit_rblock(rblockHeader_2,
                              rblockCoinbase_2,
                              rblockCoinbase_pfx_2,
                              rblockCoinbase_sfx_2,
                              rblock_merklePath_2,
                              bribee)
    events = event_filter.get_new_entries()
    assert len(events) == 1 # only one event on this instance has occured
    e = events[0]
    assert e.event == 'New_rblock'
    assert e.args._rblockHash == client.endSwap(client.dSHA256(rblockHeader_2,raw=True))
    assert e.args._blockHeight == b2["blockHeight"]
    #assert e.args._tblockHash ==
    assert emrc.instance.functions._currentState().call() == 2

    with pytest.raises(ValueError):
        emrc.submit_rblock(rblockHeader_2,
                           rblockCoinbase_2,
                           rblockCoinbase_pfx_2,
                           rblockCoinbase_sfx_2,
                           rblock_merklePath_2,
                           bribee)



    rblockHeader_3 = b3["blockHeader_bytes_big"]
    rblockCoinbase_3 = b3["cb"]
    rblockCoinbase_pfx_3 = b3["cb_pfx"]
    rblockCoinbase_sfx_3 = b3["cb_sfx"]
    rblock_merklePath_3= b3["mp_hashes_bytes_big"]
    event_filter = emrc.instance.events.New_rblock.createFilter(fromBlock='latest')

    with pytest.raises(ValueError):
        emrc.submit_rblock(rblockHeader_2,
                           rblockCoinbase_3,
                           rblockCoinbase_pfx_3,
                           rblockCoinbase_sfx_3,
                           rblock_merklePath_3,
                           bribee)

    with pytest.raises(ValueError):
        emrc.submit_rblock(rblockHeader_3,
                           rblockCoinbase_2,
                           rblockCoinbase_pfx_3,
                           rblockCoinbase_sfx_3,
                           rblock_merklePath_3,
                           bribee)

    with pytest.raises(ValueError):
        emrc.submit_rblock(rblockHeader_3,
                           rblockCoinbase_3,
                           rblockCoinbase_pfx_3,
                           rblockCoinbase_sfx_3,
                           rblock_merklePath_2,
                           bribee)

    with pytest.raises(ValueError):
        emrc.submit_rblock(rblockHeader_3,
                           rblockCoinbase_3,
                           rblockCoinbase_pfx_2,
                           rblockCoinbase_sfx_3,
                           rblock_merklePath_3,
                           bribee)

    with pytest.raises(ValueError):
        emrc.submit_rblock(rblockHeader_3,
                           rblockCoinbase_3,
                           rblockCoinbase_pfx_3,
                           rblockCoinbase_sfx_2,
                           rblock_merklePath_3,
                           bribee)

    events = event_filter.get_new_entries()
    assert len(events) == 0 # no event should have fired
    assert emrc.submit_rblock(rblockHeader_3,
                              rblockCoinbase_3,
                              rblockCoinbase_pfx_3,
                              rblockCoinbase_sfx_3,
                              rblock_merklePath_3,
                              bribee)
    events = event_filter.get_new_entries()
    assert len(events) == 1 # only one event on this instance has occured
    e = events[0]
    assert e.event == 'New_rblock'
    assert e.args._rblockHash == client.endSwap(client.dSHA256(rblockHeader_3,raw=True))
    assert e.args._blockHeight == b3["blockHeight"]
    #assert e.args._tblockHash ==
    assert emrc.instance.functions._currentState().call() == 2


    event_filter = emrc.instance.events.New_rblock.createFilter(fromBlock='latest')
    assert emrc.submit_rblock(b4["blockHeader_bytes_big"],
                              b4["cb"],
                              b4["cb_pfx"],
                              b4["cb_sfx"],
                              b4["mp_hashes_bytes_big"],
                              bribee)
    events = event_filter.get_new_entries()
    assert len(events) == 1 # only one event on this instance has occured
    e = events[0]
    assert e.event == 'New_rblock'
    assert e.args._rblockHash == client.endSwap(client.dSHA256(b4["blockHeader_bytes_big"],raw=True))
    assert e.args._blockHeight == b4["blockHeight"]
    #assert e.args._tblockHash ==
    assert emrc.instance.functions._currentState().call() == 2

    event_filter = emrc.instance.events.New_rblock.createFilter(fromBlock='latest')
    assert emrc.submit_rblock(b5["blockHeader_bytes_big"],
                              b5["cb"],
                              b5["cb_pfx"],
                              b5["cb_sfx"],
                              b5["mp_hashes_bytes_big"],
                              bribee)
    events = event_filter.get_new_entries()
    assert len(events) == 1 # only one event on this instance has occured
    e = events[0]
    assert e.event == 'New_rblock'
    assert e.args._rblockHash == client.endSwap(client.dSHA256(b5["blockHeader_bytes_big"],raw=True))
    assert e.args._blockHeight == b5["blockHeight"]
    #assert e.args._tblockHash ==
    assert emrc.instance.functions._currentState().call() == 2

    event_filter = emrc.instance.events.New_rblock.createFilter(fromBlock='latest')
    assert emrc.submit_rblock(b6["blockHeader_bytes_big"],
                              b6["cb"],
                              b6["cb_pfx"],
                              b6["cb_sfx"],
                              b6["mp_hashes_bytes_big"],
                              bribee)
    events = event_filter.get_new_entries()
    assert len(events) == 1 # only one event on this instance has occured
    e = events[0]
    assert e.event == 'New_rblock'
    assert e.args._rblockHash == client.endSwap(client.dSHA256(b6["blockHeader_bytes_big"],raw=True))
    assert e.args._blockHeight == b6["blockHeight"]
    #assert e.args._tblockHash ==
    assert emrc.instance.functions._currentState().call() == 2

    event_filter = emrc.instance.events.New_rblock.createFilter(fromBlock='latest')
    assert emrc.submit_rblock(b7["blockHeader_bytes_big"],
                              b7["cb"],
                              b7["cb_pfx"],
                              b7["cb_sfx"],
                              b7["mp_hashes_bytes_big"],
                              bribee)
    events = event_filter.get_new_entries()
    assert len(events) == 1 # only one event on this instance has occured
    e = events[0]
    assert e.event == 'New_rblock'
    assert e.args._rblockHash == client.endSwap(client.dSHA256(b7["blockHeader_bytes_big"],raw=True))
    assert e.args._blockHeight == b7["blockHeight"]
    assert emrc.instance.functions._currentState().call() == 2

    event_filter = emrc.instance.events.New_rblock.createFilter(fromBlock='latest')
    assert emrc.submit_rblock(b8["blockHeader_bytes_big"],
                              b8["cb"],
                              b8["cb_pfx"],
                              b8["cb_sfx"],
                              b8["mp_hashes_bytes_big"],
                              bribee)
    events = event_filter.get_new_entries()
    assert len(events) == 1 # only one event on this instance has occured
    e = events[0]
    assert e.event == 'New_rblock'
    assert e.args._rblockHash == client.endSwap(client.dSHA256(b8["blockHeader_bytes_big"],raw=True))
    assert e.args._blockHeight == b8["blockHeight"]
    assert emrc.instance.functions._currentState().call() == 2

    event_filter = emrc.instance.events.New_rblock.createFilter(fromBlock='latest')
    assert emrc.submit_rblock(b9["blockHeader_bytes_big"],
                              b9["cb"],
                              b9["cb_pfx"],
                              b9["cb_sfx"],
                              b9["mp_hashes_bytes_big"],
                              bribee)
    events = event_filter.get_new_entries()
    assert len(events) == 1 # only one event on this instance has occured
    e = events[0]
    assert e.event == 'New_rblock'
    assert e.args._rblockHash == client.endSwap(client.dSHA256(b9["blockHeader_bytes_big"],raw=True))
    assert e.args._blockHeight == b9["blockHeight"]
    assert emrc.instance.functions._currentState().call() == 3

    with pytest.raises(ValueError):
        emrc.submit_rblock(b10["blockHeader_bytes_big"],
                           b10["cb"],
                           b10["cb_pfx"],
                           b10["cb_sfx"],
                           b10["mp_hashes_bytes_big"],
                           bribee)

def test_payout(emrc):
    bribee = emrc.w3.eth.accounts[1]
    balance_contract_before = emrc.w3.eth.getBalance(emrc.instance.address)
    balance_account_before = emrc.w3.eth.getBalance(bribee)
    tx_hash = emrc.instance.functions.payout().transact(
        {"from":bribee,
         "value":0,
         "gas": 2_500_000})
    tx_info = emrc.w3.eth.getTransaction(tx_hash)
    tx_receipt = emrc.w3.eth.waitForTransactionReceipt(tx_hash)
    balance_contract_after = emrc.w3.eth.getBalance(emrc.instance.address)
    balance_account_after = emrc.w3.eth.getBalance(bribee)
    assert balance_account_after - balance_account_before + tx_receipt["gasUsed"]*tx_info["gasPrice"] == ( 10**18 + 10**18 ) * 3
    print("BALANCE ",balance_contract_after)

# --- useing exclusively the client ---

def test_init():
    hash_1_str = '000000000000000082ccf8f1557c5d40b21edabb18d2d691cfbf87118bac7254'
    hash_1_bytes = client.hexstr_to_dbytes(hash_1_str,swap=False)

    EMRC = client.EMRC()
    emrc = EMRC.deploy("/smartcode/contracts/EMR.sol")
    assert EMRC.init(300000,1,6,hash_1_bytes)

    with pytest.raises(ValueError):
        EMRC.init(300000,2,6,hash_1_bytes)

def test_init2():
    hash_1_str = '000000000000000082ccf8f1557c5d40b21edabb18d2d691cfbf87118bac7254'
    hash_1_bytes = client.hexstr_to_dbytes(hash_1_str,swap=False)

    EMRC = client.EMRC()
    emrc = EMRC.deploy("/smartcode/contracts/EMR.sol")
    assert EMRC.init(300000,0,6,hash_1_bytes)


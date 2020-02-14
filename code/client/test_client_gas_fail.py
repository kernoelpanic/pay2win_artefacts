import web3
import util
import client
import pytest

def test_gas_fail():
    """ Use blocks 300_000 to ... """
    blks_3K = client.load_input_blocks("../testdata/btc_blocks_json_samples/300000--300022")

    b = list()
    for i in range(0,len(blks_3K)):
        b.append(client.get_input_block_calldata(blks_3K,i))

    assert len(b) == len(blks_3K)

    BLOCK_REWARD=int(12.5*10**18)
    BLOCK_BRIBE=int(1*10**18)


    startHeight = 300000
    kV = 6
    kB = 6

    EMRC = client.EMRC()
    emrc = EMRC.deploy("/smartcode/contracts/EMR.sol")
    assert EMRC.instance.functions._currentState().call() == 0

    assert EMRC.init(startHeight,kV,kB,b[0]["blockHash_bytes_little"])
    assert EMRC.instance.functions._currentState().call() == 1

    briber = EMRC.w3.eth.accounts[0]
    bribee = EMRC.w3.eth.accounts[1]
    mainchainminer = EMRC.w3.eth.accounts[2]

    for i in range(1,kV+1):
        assert EMRC.submit_cblock(b[i]["blockHeader_bytes_big"],
                                  b[i]["blockHeight"],
                                  BLOCK_REWARD,
                                  mainchainminer)

    for i in range(1,kV+2):
        #print("Header: ",b[i]["tblockHeader_bytes_big"].hex())
        offset_start = client.NVERSION_LEN
        offset_end = client.NVERSION_LEN + client.HASHPREVBLOCK_LEN
        #print("Header phash: ",b[i]["tblockHeader_bytes_big"][offset_start:offset_end].hex())
        offset_start = client.NVERSION_LEN + client.HASHPREVBLOCK_LEN
        offset_end = client.NVERSION_LEN + client.HASHPREVBLOCK_LEN + client.HASHMERKLEROOT_LEN
        #print("Header mroot: ",b[i]["tblockHeader_bytes_big"][offset_start:offset_end].hex())
        invalid_block = bytearray(b[i]["tblockHeader_bytes_big"])
        invalid_block[0] = 3
        assert EMRC.submit_tblock(bytes(invalid_block),
                                  b[i]["cb_pfx"],
                                  b[i]["blockHeight"],
                                  b[i]["cb_sfx"],
                                  b[i]["mp_hashes_bytes_big"],
                                  BLOCK_REWARD,
                                  BLOCK_BRIBE)
    assert EMRC.instance.functions._currentState().call() == 2


    i = 1
    invalid_block = bytearray(b[i]["blockHeader_bytes_big"])
    invalid_block[0] = 3
    invalid_block = bytes(invalid_block)
    assert EMRC.submit_rblock(invalid_block,
                              b[i]["cb"],
                              b[i]["cb_pfx"],
                              b[i]["cb_sfx"],
                              b[i]["mp_hashes_bytes_big"],
                              bribee)
    i = 2
    offset=client.NVERSION_LEN
    previous_hash = client.dSHA256(invalid_block,raw=True)
    invalid_block = bytearray(b[i]["blockHeader_bytes_big"])
    invalid_block[0] = 3
    invalid_block = bytes(invalid_block)
    invalid_block = client.replace_at_offset(invalid_block,offset,previous_hash)
    assert EMRC.submit_rblock(invalid_block,
                              b[i]["cb"],
                              b[i]["cb_pfx"],
                              b[i]["cb_sfx"],
                              b[i]["mp_hashes_bytes_big"],
                              bribee)

    with pytest.raises(ValueError):
        # block already mined
        EMRC.submit_rblock(invalid_block,
                              b[i]["cb"],
                              b[i]["cb_pfx"],
                              b[i]["cb_sfx"],
                              b[i]["mp_hashes_bytes_big"],
                              bribee)

    i = 3
    offset=client.NVERSION_LEN
    previous_hash = client.dSHA256(invalid_block,raw=True)
    invalid_block = bytearray(b[i]["blockHeader_bytes_big"])
    invalid_block[0] = 3
    invalid_block = bytes(invalid_block)
    invalid_block = client.replace_at_offset(invalid_block,offset,previous_hash)
    assert EMRC.submit_rblock(invalid_block,
                              b[i]["cb"],
                              b[i]["cb_pfx"],
                              b[i]["cb_sfx"],
                              b[i]["mp_hashes_bytes_big"],
                              bribee)

    # main chain is gona win
    for i in range(1,kV+2+kB):
        assert EMRC.submit_rblock(b[i]["blockHeader_bytes_big"],
                                  b[i]["cb"],
                                  b[i]["cb_pfx"],
                                  b[i]["cb_sfx"],
                                  b[i]["mp_hashes_bytes_big"],
                                  mainchainminer)
    assert EMRC.instance.functions._currentState().call() == 3

    reward = EMRC.payout(mainchainminer)
    assert reward == 0

    reward = EMRC.payout(briber)
    assert reward == 0

    reward = EMRC.payout(bribee)
    assert reward == BLOCK_REWARD * 3


    print()
    print("SUCCESS = ",EMRC.instance.functions._attackSuccessful().call() )
    EMRC.printGasStats()


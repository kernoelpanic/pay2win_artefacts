import web3
import util
import client
import pytest
import os

def test_gas_success():
    """ Execute example attack for certain block range ... """
    blockrange = os.environ.get('BLOCKRANGE')
    if blockrange is None:
        blks = client.load_input_blocks("../testdata/btc_blocks_json_samples/617000--617022")
    else:
        blks = client.load_input_blocks("../testdata/btc_blocks_json_samples/" + str(blockrange))

    gwei = os.environ.get('GWEI')
    if gwei is None:
        gwei = 27*10**9
    else:
        gwei = int(gwei)

    exr = os.environ.get('EXR')
    if exr is None:
        exr = 389.20
    else:
        exr = float(exr)


    b = list()
    for i in range(0,len(blks)):
        b.append(client.get_input_block_calldata(blks,i))

    assert len(b) == len(blks)

    BLOCK_REWARD=int(12.5*10**18)
    BLOCK_BRIBE=int(1*10**18)

    startHeight = blks[0]["height"]
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
        assert EMRC.submit_tblock(b[i]["tblockHeader_bytes_big"],
                                  b[i]["cb_pfx"],
                                  b[i]["blockHeight"],
                                  b[i]["cb_sfx"],
                                  b[i]["mp_hashes_bytes_big"],
                                  BLOCK_REWARD,
                                  BLOCK_BRIBE)
    assert EMRC.instance.functions._currentState().call() == 2

    for i in range(1,kV+2+kB):
        assert EMRC.submit_rblock(b[i]["blockHeader_bytes_big"],
                                  b[i]["cb"],
                                  b[i]["cb_pfx"],
                                  b[i]["cb_sfx"],
                                  b[i]["mp_hashes_bytes_big"],
                                  bribee)
    assert EMRC.instance.functions._currentState().call() == 3


    reward = EMRC.payout(bribee)
    assert reward == (BLOCK_REWARD + BLOCK_BRIBE) * (kV+1)

    reward = EMRC.payout(mainchainminer)
    assert reward == BLOCK_REWARD * kV

    reward = EMRC.payout(briber)
    assert reward == 0

    print()
    print("SUCCESS = ",EMRC.instance.functions._attackSuccessful().call() )
    EMRC.printGasStats(gwei,exr)


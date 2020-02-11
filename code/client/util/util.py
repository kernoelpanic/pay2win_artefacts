import web3
import web3.auto as web3auto
from web3.middleware import geth_poa_middleware

import time
import threading
import hashlib
import os
import subprocess
import json
from sha3 import keccak_256

w3 = None
HOST="127.0.0.1"
PORT="8545"

def connect(host=None,port=None,poa=False):
    global w3
    if host is None:
        host=HOST
    if port is None:
        port=PORT
    if w3 is None or not w3.isConnected():
        w3 = web3.Web3(web3.HTTPProvider(f"http://{host}:{port}", request_kwargs={"timeout": 60 * 1000}))
        if poa:
            # inject PoA compatibility
            # the new way
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            # inject the old way:
            #w3.middleware_stack.inject(geth_poa_middleware, layer=0)
    assert w3.isConnected(), "Connecting to local Ethereum node failed!"
    return w3


def compile_contract_with_libs(compiler_path,src_path,account=None,gas=None):
    """ compile a single contract file (with libraries) and manually call the compiler.
    Use only absolute paths its better.
    """
    c_abi = ""
    c_bin = ""
    c_dep = dict() # contract dependencies

    # Manually call solc
    output = subprocess.run([compiler_path,"--optimize","--combined-json","abi,bin",src_path],capture_output=True)
    if output.returncode != 0:
        print("Error: Compiling contract")
        print(output)
        return None
    compiler_output = json.loads(output.stdout)

    # We have compiled a contract with dependencies e.g., on libs
    for sfile in compiler_output["contracts"]:
        if sfile.split(":")[0] == src_path:
            # First identify the base contract
            c_abi = compiler_output["contracts"][sfile]["abi"]
            c_bin = compiler_output["contracts"][sfile]["bin"]
        else:
            # all other contract are either libs or inheritted contracts,
            # the latter can be ignored since they have to be included in the
            # base contracts bytecode anyway (see ABI of base contract for inheritted functions)
            # To identify which is which we translate *all* source file path/name
            # to their replacement hash and later check the base contracts bytecode if this
            # replacement hash occures
            c_dep[sfile] = { "replace_str": "__$" + keccak_256(bytes(sfile, "utf-8")).hexdigest()[:34] + "$__",
                             "address_str": "",
                             "bin_str": compiler_output["contracts"][sfile]["bin"],
                             "abi_str": compiler_output["contracts"][sfile]["abi"] }

    #print(c_bin)
    #print()
    for sfile,sdata in c_dep.items():
        if c_bin.find(sdata["replace_str"]) != -1:
            # replacement string found in compile binary base contract.
            # Deploy that contract and get its address to replace occurances
            #print(sfile)

            #print("placeholder address: " + sdata["replace_str"]) # print placeholder address

            #print(sdata["abi_str"])
            #print()
            #print(sdata["bin_str"])
            tx_receipt = deploy_contract(
                                       cabi=sdata["abi_str"],
                                       cbin=sdata["bin_str"],
                                       account=account,
                                       gas=gas,
                                       argument=None,
                                       argument2=None,
                                       wait=True,
                                       value=0)
            c_dep[sfile]["address_str"] = tx_receipt['contractAddress'].replace("0x","")
            #print("lib address        : " + c_dep[sfile]["address_str"])  # print libary address
            c_bin = c_bin.replace(sdata["replace_str"],c_dep[sfile]["address_str"])

    #print()
    #print(c_bin)
    #print()
    #print(c_abi)
    return { "abi": c_abi, "bin": c_bin }.copy()

def deploy_contract(
        cabi,
        cbin,
        account=None,
        gas=None,
        argument=None,
        argument2=None,
        wait=True,
        value=0):
    """ deploy contract from JSON ABI and binary hex string (bin)
        which includes deployment constructor.
        Optinal arguments:
            account from which deployment tx is sent
            gas limit for deployment
            argument to the constructor
    """
    if account is None:
        account = w3.eth.accounts[0]
        w3.eth.defaultAccount = account
    if gas is None:
        # somewhere around max gas
        #gas = 5_000_000 # this is too large for some default chain configs
        #gas = 4_500_000
        #gas = 8_000_000
        gas = 10_000_000

    contract=w3.eth.contract(abi=cabi,
                             bytecode=cbin)

    if argument is not None:
        if argument2 is not None:
            tx_hash = contract.constructor(argument,argument2).transact(
                {"from":account,
                 "gas":gas,
                 "value":value})
        else:
            tx_hash = contract.constructor(argument).transact(
                {"from":account,
                 "gas":gas,
                 "value":value})
    else:
        tx_hash = contract.constructor().transact(
                {"from":account,
                 "gas":gas,
                 "value":value})
    if wait:
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        return tx_receipt
    else:
        return tx_hash

def get_contract_instance(
        caddress,
        cabi,
        account=None,
        concise=False,
        patch_api=False,
        concise_events=False,
        path=None):
    """ get contract instance from address and abi """

    if cabi is None and path is None:
        print("No ABI or path to source given")
        return None
    elif path is not None:
        cabi=compile_contract_with_libs("solc",path)["abi"]

    if concise:
        instance = w3.eth.contract(
            address=caddress,
            abi=cabi,
            ContractFactoryClass=web3.contract.ConciseContract)
    else:
        instance = w3.eth.contract(
            address=caddress,
            abi=cabi)

    if concise and patch_api:
        #if concise and patch_api:
        # patch API s.t. all transactions are automatically waited for
        # until tx_receipt is received
        for name, func in instance.__dict__.items():
            if isinstance(func, web3.contract.ConciseMethod):
                instance.__dict__[name] = _tx_executor(func)

    return instance

def _tx_executor(contract_function):
    """ modifies the contract instance interface function such that whenever a transaction is performed
        it automatically waits until the transaction in included in the blockchain
        (unless wait=False is specified, in the case the default the api acts as usual)
    """
    def f(*args, **kwargs):
        #print(args,kwargs)
        wait = kwargs.pop("wait", True)
        txwait = kwargs.pop("txwait", False)
        #print(args,kwargs)
        #print(wait,txwait)
        if ("transact" in kwargs and wait) or txwait:
            tx_hash = contract_function(*args, **kwargs)
            tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
            return tx_receipt
        return contract_function(*args, **kwargs)
    return f


def compile_and_deploy_contract(path,
        account=None,
        concise=True,
        patch_api=True,
        concise_events=True,
        argument=None,
        argument2=None,
        wait=True,
        value=0,
        gas=None,
        compiler="solc"):
    """ compiles and deploy the given contract (from the ./contracts folder)
        returns the contract instance

        Changed default behaviour to use the installed solc compiler
        with custom flags per default: compiler="solc"
        Change to custom path to compiler location if necessary.
    """
    if not w3 or not w3.isConnected():
        connect()
    if account is None:
        if w3.isAddress(w3.eth.defaultAccount):
            account = w3.eth.defaultAccount
        else:
            account = w3.eth.accounts[0]
            w3.eth.defaultAccount = account

    # compile manually
    interface = compile_contract_with_libs(compiler_path=compiler,
                                           src_path=path,
                                           account=account,
                                           gas=gas)

    ret = deploy_contract(
                cabi=interface["abi"],
                cbin=interface["bin"],
                account=account,
                gas=gas,
                argument=argument,
                argument2=argument2,
                wait=wait,
                value=value)
    if wait:
        tx_receipt = ret
        contract = get_contract_instance(
            caddress=tx_receipt['contractAddress'],
            cabi=interface["abi"],
            patch_api=patch_api,
            concise=concise,
            concise_events=concise_events)
        return contract
    else:
        tx_hash = ret
        return tx_hash


def get_events(contract_instance, event_name):
    # eventFilter = contract.eventFilter(event_name, {"fromBlock": 0})
    eventFilter = contract_instance.events.__dict__[event_name].createFilter(fromBlock=0)
    return [e for e in eventFilter.get_all_entries() if e.address == contract_instance.address]


# -----------
# w3 helper

def mine_block():
    w3.providers[0].make_request('evm_mine', params='')


def mine_blocks_until(predicate):
    while not predicate():
        mine_block()

def getBalance(address):
    return w3.fromWei(w3.eth.getBalance(address),'ether')

# -----------

def flatten(list_of_lists):
    return [y for x in list_of_lists for y in x]


def wait_for(predicate, check_interval=1.0):
    while not predicate():
        time.sleep(check_interval)

# -----------

def run(func_or_funcs, args=()):
    """ executes the given functions in parallel and waits
        until all execution have finished
    """
    threads = []
    if isinstance(func_or_funcs, list):
        funcs = func_or_funcs
        for i, f in enumerate(funcs):
            arg = args[i] if isinstance(args, list) else args
            if (arg is not None) and (not isinstance(arg, tuple)):
                arg = (arg, )
            threads.append(threading.Thread(target=f, args=arg))
    else:
        func = func_or_funcs
        assert isinstance(args, list)
        for arg in args:
            xarg = arg if isinstance(arg, tuple) else (arg, )
            threads.append(threading.Thread(target=func, args=xarg))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

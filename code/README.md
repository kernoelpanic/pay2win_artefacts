# PoC and gas measurments 

This folder contains a PoC of the Ephemeral Mining Relay described in the paper. 
The gas measurements can be performed by running the unit tests. 

The code uses the `SafeMath` library 
from [openzeppelin](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/math/SafeMath.sol)
and parts of a `utils` library for manipulating `bytes` with solidity. 

## Environment

To setup the environment use the shell script [docker_build_smartcode.sh](docker_build_smartcode.sh) to create
two docker containers. 

```bash
$ bash docker_build_smartcode.sh
```

### Ganache 
All tests are carried out on a ganache test chain. We use the official latest ganache docker image which is pulled by the setup script automatically. 

### Smartcode
The development environment used [web3py](https://web3py.readthedocs.io/en/stable/) which is installed in the smartcode docker image during the build process. 

The docker file for setting up the image is [smartcode.python.p2w.Dockerfile](smartcode.python.p2w.Dockerfile).

All python requirements automatically installed in the container are defined int [smartcode.python.p2w.requirements.txt](smartcode.python.p2w.requirements.txt)


## Run test cases 

First start the two containers in two different shells and keep them running.

```bash
$ bash docker_run_ganache.sh
```
You see the output of ganache spawning a deterministic testnet setup with a series of accounts initialized with ether. 

```bash
$ bash docker_run_smartcode.sh
```
You see the smartcode environment which also launches jupyter for convenient interactive testing.  

Now you can login to the `smartcode` container and run all test cases using `pytest` like so: 

```bash
$ bash docker_exec_smartcode.sh
$ make all 
...
test_client_gas_success.py Deployed at:  0x5b1869D9A4C187F2EAa108f3062412ecf0526b24

SUCCESS =  True

Gas stats:
	deploy  =  6,156,688  gas       11.86  USD
	init    =  1,364,193  gas        2.63  USD
	attack  =  7,575,073  gas       14.59  USD
	payout  =     64,511  gas        0.12  USD
	--------------------
	total   = 15,160,465  gas       29.20  USD

	cblocks =  1,129,139  gas        2.18  USD
	n_c     =          6  
	cblock  =    188,190  gas        0.36  USD

	tblocks =  2,071,520  gas        3.99  USD
	n_t     =          7
	tblock  =    295,931  gas        0.57  USD

	rblocks =  5,503,553  gas       10.60  USD
	n_r     =         13
	rblock  =    423,350  gas        0.82  USD

...

test_client_gas_fail.py Deployed at:  0x6eD79Aa1c71FD7BdBC515EfdA3Bd4e26394435cC

SUCCESS =  False

Gas stats:
	deploy  =  6,156,688  gas       11.86  USD
	init    =  1,364,193  gas        2.63  USD
	attack  =  7,356,844  gas       14.17  USD
	payout  =     66,949  gas        0.13  USD
	--------------------
	total   = 14,944,674  gas       28.79  USD

	cblocks =  1,129,139  gas        2.18  USD
	n_c     =          6  
	cblock  =    188,190  gas        0.36  USD

	tblocks =  2,071,520  gas        3.99  USD
	n_t     =          7
	tblock  =    295,931  gas        0.57  USD

	rblocks =  5,285,324  gas       10.18  USD
	n_r     =         16
	rblock  =    330,333  gas        0.64  USD
```

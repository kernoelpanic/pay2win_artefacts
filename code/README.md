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
	init    =  1,364,277  gas        2.63  USD
	attack  =  8,203,136  gas       15.80  USD
	payout  =     64,511  gas        0.12  USD
	--------------------
	total   = 15,788,612  gas       30.41  USD

	cblocks =  1,129,235  gas        2.18  USD
	n_c     =          6  
	cblock  =    188,206  gas        0.36  USD

	tblocks =  2,115,593  gas        4.08  USD
	n_t     =          7
	tblock  =    302,228  gas        0.58  USD

	rblocks =  6,087,543  gas       11.73  USD
	n_r     =         13
	rblock  =    468,273  gas        0.90  USD

...

test_client_gas_fail.py Deployed at:  0x6AB47d47cF45C4aaA5c7F33c6632390674EfA294

SUCCESS =  False

Gas stats:
	deploy  =  6,156,688  gas       11.86  USD
	init    =  1,364,277  gas        2.63  USD
	attack  =  7,701,821  gas       14.84  USD
	payout  =     66,949  gas        0.13  USD
	--------------------
	total   = 15,289,735  gas       29.45  USD

	cblocks =  1,129,235  gas        2.18  USD
	n_c     =          6  
	cblock  =    188,206  gas        0.36  USD

	tblocks =  2,115,677  gas        4.08  USD
	n_t     =          7
	tblock  =    302,240  gas        0.58  USD

	rblocks =  5,586,144  gas       10.76  USD
	n_r     =         16
	rblock  =    349,134  gas        0.67  USD
```

ETHPORT?=8545 # RPC prot of the ganache image
ETHHOST?=172.18.0.2  # IP of the ganache image 

all: client btcblk gas_success gas_fail

allverbose:
	(\
		cd ./client/ && \
		ETHPORT=$(ETHPORT) ETHHOST=$(ETHHOST) BLOCKRANGE=617000--617022 python -m pytest -s test_*.py; \
	)

client:
	(\
		cd ./client/ && \
		ETHPORT=$(ETHPORT) ETHHOST=$(ETHHOST) python -m pytest test_client.py; \
	)

btcblk:
	(\
		cd ./client/ && \
		ETHPORT=$(ETHPORT) ETHHOST=$(ETHHOST) python -m pytest test_BtcBlk.py; \
	)

gas_success:
	(\
		cd ./client/ && \
		ETHPORT=$(ETHPORT) ETHHOST=$(ETHHOST) BLOCKRANGE=617000--617022 python -m pytest -s test_client_gas_success.py; \
	)

gas_fail:
	(\
		cd ./client/ && \
		ETHPORT=$(ETHPORT) ETHHOST=$(ETHHOST) BLOCKRANGE=617000--617022 python -m pytest -s test_client_gas_fail.py; \
	)


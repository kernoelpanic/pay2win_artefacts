
ETHPORT?=8545 # RPC prot of the ganache image
ETHHOST?=172.18.0.2  # IP of the ganache image 

all: client btcblk gas_success gas_fail

allverbose:
	(\
		ETHPORT=$(ETHPORT) ETHHOST=$(ETHHOST) cd ./client && python -m pytest -s test_*.py; \
	)

client:
	(\
		ETHPORT=$(ETHPORT) ETHHOST=$(ETHHOST) cd ./client && python -m pytest test_client.py; \
		#ETHPORT=$(ETHPORT) ETHHOST=$(ETHHOST) python -m pytest test_client.py -k 'not test_gas_success or test_gas_fail'; \
	)

btcblk:
	(\
		ETHPORT=$(ETHPORT) ETHHOST=$(ETHHOST) cd ./client && python -m pytest test_BtcBlk.py; \
	)

gas_success:
	(\
                ETHPORT=$(ETHPORT) ETHHOST=$(ETHHOST) cd ./client && python -m pytest -s test_client_gas_success.py; \
                #ETHPORT=$(ETHPORT) ETHHOST=$(ETHHOST) python -m pytest -s test_client.py -k 'test_gas_success' \
        )

gas_fail:
	(\
		ETHPORT=$(ETHPORT) ETHHOST=$(ETHHOST) cd ./client && python -m pytest -s test_client_gas_fail.py; \
                #ETHPORT=$(ETHPORT) ETHHOST=$(ETHHOST) python -m pytest -s test_client.py -k 'test_gas_fail' \
        )


#!/bin/bash

docker run \
  -p 127.0.0.1:8545:8545 \
  --net smartnet \
  --hostname ganache \
  --ip 172.18.0.2 \
  -it trufflesuite/ganache-cli:latest -d --gasLimit 80000000 --allowUnlimitedContractSize --defaultBalanceEther 100000 
  #-it trufflesuite/ganache-cli:latest -d --gasLimit 80000000 --allowUnlimitedContractSize --defaultBalanceEther 200  
  #-it trufflesuite/ganache-cli:latest --gasLimit 8000000 --allowUnlimitedContractSize  

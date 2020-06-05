#!/usr/bin/env bash
rm crc_bank.db logs/crc_bank.log

python crc_bank.py insert proposal sam --smp=10000 --mpi=10000 --gpu=10000 --htc=10000

python crc_bank.py investor sam --mpi=10000
python crc_bank.py investor sam --mpi=10000
python crc_bank.py investor sam --mpi=10000

python crc_bank.py withdraw sam --mpi=8000
python crc_bank.py withdraw sam --mpi=8000
python crc_bank.py withdraw sam --mpi=8000

python crc_bank.py info sam

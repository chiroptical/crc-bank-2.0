#!/usr/bin/env bash
rm crc_bank.db logs/crc_bank.log proposal.json investor.json proposal_archive.json investor_archive.json

python crc_bank.py insert proposal sam --smp=10000

python crc_bank.py investor sam --mpi=10000
python crc_bank.py investor sam --mpi=10000
python crc_bank.py investor sam --mpi=10000

# python crc_bank.py withdraw sam --mpi=8000
# python crc_bank.py withdraw sam --mpi=8000
# python crc_bank.py withdraw sam --mpi=8000

python crc_bank.py renewal sam --smp=5000 --mpi=5000 --gpu=5000 --htc=5000

#python crc_bank.py dump proposal.json investor.json proposal_archive.json investor_archive.json

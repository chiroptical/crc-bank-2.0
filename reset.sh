#!/usr/bin/env bash
rm crc_bank.db logs/crc_bank.log

python crc_bank.py insert proposal sam 10000 0 0 0
python crc_bank.py investor sam 10000 0 0 0

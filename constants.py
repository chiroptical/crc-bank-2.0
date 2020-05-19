#!/usr/bin/env python
import dataset

CLUSTERS = ["smp", "mpi", "gpu", "htc"]

db = dataset.connect("sqlite:///crc_bank.db")
proposal_table = db["proposal"]
investor_table = db["investor"]

date_format = "%m/%d/%y"

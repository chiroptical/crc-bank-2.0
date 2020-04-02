#!/usr/bin/env python
""" crc-bank.py -- Deal with bank.db
Usage:
    crc-bank.py insert <account> <type> <smp> <mpi> <gpu> <htc>
    crc-bank.py -h | --help
    crc-bank.py -v | --version

Positional Arguments:
    <account>       The associated slurm account
    <type>          The proposal type: proposal or class
    <smp>           The limit in CPU Hours (e.g. 10,000)
    <mpi>           The limit in CPU Hours (e.g. 10,000)
    <gpu>           The limit in GPU Hours (e.g. 10,000)
    <htc>           The limit in CPU Hours (e.g. 10,000)

Options:
    -h --help       Print this screen and exit
    -v --version    Print the version of crc-bank.py

Descriptions:
    crc-bank.py insert # insert for the first time
"""


CLUSTERS = ["smp", "mpi", "gpu", "htc"]


import dataset
from docopt import docopt
from datetime import date, timedelta
import utils

args = docopt(__doc__, version="crc-bank.py version 0.0.1")


db = dataset.connect("sqlite:///crc-bank.db")
proposal_table = db["proposal"]

if args["insert"]:
    # Account shouldn't exist in the proposal table already
    x = utils.account_exists_in_table(proposal_table, args["<account>"])
    if isinstance(x, utils.Right):
        exit(f"Proposal for account `{args['<account>']}` already exists. Exiting...")

    # Account associations better exist!
    _ = utils.unwrap_if_right(
        utils.account_and_cluster_associations_exists(args["<account>"], CLUSTERS)
    )

    # Make sure we understand the proposal type
    proposal_type = utils.unwrap_if_right(utils.parse_proposal_type(args["<type>"]))
    proposal_duration = (
        timedelta(days=365)
        if proposal_type == utils.ProposalType.Proposal
        else timedelta(days=122)
    )
    end_date = date.today() + proposal_duration

    # Service units should be a valid number
    sus = utils.unwrap_if_right(utils.check_service_units_valid(args, CLUSTERS))

    to_insert = {
        "account": args["<account>"],
        "proposal_type": proposal_type.value,
        "percent_notified": utils.PercentNotified.Zero.value,
        "start_date": date.today(),
        "end_date": end_date,
    }
    for c in CLUSTERS:
        to_insert[c] = sus[c]
    proposal_table.insert(to_insert)

    utils.log_action(
        f"Inserted proposal with type {proposal_type.name} for {args['<account>']} with `{sus['smp']}` on SMP, `{sus['mpi']}` on MPI, `{sus['gpu']}` on GPU, and `{sus['htc']}` on HTC"
    )

else:
    print("Unrecognized command, you probably shouldn't see this...")

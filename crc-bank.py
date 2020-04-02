#!/usr/bin/env python
""" crc-bank.py -- Deal with bank.db
Usage:
    crc-bank.py insert <account> <type> <smp> <mpi> <gpu> <htc>
    crc-bank.py modify <account> <smp> <mpi> <gpu> <htc>
    crc-bank.py info <account>
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
    crc-bank.py modify # change to new limits, update proposal date
"""


CLUSTERS = ["smp", "mpi", "gpu", "htc"]


import dataset
from docopt import docopt
from datetime import date, timedelta
import utils
import json

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
    proposal_duration = utils.get_proposal_duration(proposal_type)
    start_date = date.today()
    end_date = start_date + proposal_duration

    # Service units should be a valid number
    sus = utils.unwrap_if_right(utils.check_service_units_valid(args, CLUSTERS))

    to_insert = {
        "account": args["<account>"],
        "proposal_type": proposal_type.value,
        "percent_notified": utils.PercentNotified.Zero.value,
        "start_date": start_date,
        "end_date": end_date,
    }
    for c in CLUSTERS:
        to_insert[c] = sus[c]
    proposal_table.insert(to_insert)

    utils.log_action(
        f"Inserted proposal with type {proposal_type.name} for {args['<account>']} with `{sus['smp']}` on SMP, `{sus['mpi']}` on MPI, `{sus['gpu']}` on GPU, and `{sus['htc']}` on HTC"
    )

elif args["info"]:
    # Account must exist in database
    _ = utils.unwrap_if_right(
        utils.account_exists_in_table(proposal_table, args["<account>"])
    )

    # Get entire row, convert to human readable columns
    od = proposal_table.find_one(account=args["<account>"])
    od["proposal_type"] = utils.ProposalType(od["proposal_type"]).name
    od["percent_notified"] = utils.PercentNotified(od["percent_notified"]).name
    od["start_date"] = od["start_date"].strftime("%d/%m/%y")
    od["end_date"] = od["end_date"].strftime("%d/%m/%y")

    print(json.dumps(od, indent=2))

elif args["modify"]:
    # Account must exist in database
    _ = utils.unwrap_if_right(
        utils.account_exists_in_table(proposal_table, args["<account>"])
    )

    # Service units should be a valid number
    sus = utils.unwrap_if_right(utils.check_service_units_valid(args, CLUSTERS))

    # Update row in database
    od = proposal_table.find_one(account=args["<account>"])
    proposal_duration = utils.get_proposal_duration(
        utils.ProposalType(od["proposal_type"])
    )
    start_date = date.today()
    end_date = start_date + proposal_duration
    od["start_date"] = start_date
    od["end_date"] = end_date
    for clus in CLUSTERS:
        od[clus] = sus[clus]
    proposal_table.update(od, ["id", "account"])

    utils.log_action(
        f"Modified proposal for {args['<account>']} with `{sus['smp']}` on SMP, `{sus['mpi']}` on MPI, `{sus['gpu']}` on GPU, and `{sus['htc']}` on HTC"
    )

else:
    print("Unrecognized command, you probably shouldn't see this...")

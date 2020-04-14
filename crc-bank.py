#!/usr/bin/env python
""" crc-bank.py -- Deal with bank.db
Usage:
    crc-bank.py insert <type> <account> <smp> <mpi> <gpu> <htc>
    crc-bank.py modify <account> <smp> <mpi> <gpu> <htc>
    crc-bank.py add <account> <smp> <mpi> <gpu> <htc>
    crc-bank.py change <account> <smp> <mpi> <gpu> <htc>
    crc-bank.py date <account> <date>
    crc-bank.py investor <account> <smp> <mpi> <gpu> <htc>
    crc-bank.py info <account>
    crc-bank.py check_sus_limit <account>
    crc-bank.py -h | --help
    crc-bank.py -v | --version

Positional Arguments:
    <account>       The associated slurm account
    <type>          The proposal type: proposal or class
    <smp>           The limit in CPU Hours (e.g. 10000)
    <mpi>           The limit in CPU Hours (e.g. 10000)
    <gpu>           The limit in GPU Hours (e.g. 10000)
    <htc>           The limit in CPU Hours (e.g. 10000)
    <date>          Change proposal start date (e.g 12/01/19)

Options:
    -h --help       Print this screen and exit
    -v --version    Print the version of crc-bank.py

Additional Documentation:
    crc-bank.py insert # insert for the first time
    crc-bank.py modify # change to new limits, update proposal date
    crc-bank.py add    # add SUs on top of current values
    crc-bank.py change # change to new limits, don't change proposal date
"""


CLUSTERS = ["smp", "mpi", "gpu", "htc"]


import dataset
from docopt import docopt
from datetime import date, timedelta
import utils
import json
from math import ceil


args = docopt(__doc__, version="crc-bank.py version 0.0.1")


db = dataset.connect("sqlite:///crc-bank.db")
proposal_table = db["proposal"]
investor_table = db["investor"]

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

elif args["investor"]:
    # Account must exist in database
    _ = utils.unwrap_if_right(
        utils.account_exists_in_table(proposal_table, args["<account>"])
    )

    # Account associations better exist!
    _ = utils.unwrap_if_right(
        utils.account_and_cluster_associations_exists(args["<account>"], CLUSTERS)
    )

    # Investor accounts last 5 years
    proposal_type = utils.ProposalType.Investor
    start_date = date.today()
    end_date = start_date + timedelta(days=1825)

    # Service units should be a valid number
    sus = utils.unwrap_if_right(utils.check_service_units_valid(args, CLUSTERS))

    to_insert = {
        "account": args["<account>"],
        "proposal_type": proposal_type.value,
        "start_date": start_date,
        "end_date": end_date,
        "years": 1,
    }
    for c in CLUSTERS:
        to_insert[c] = sus[c]
        to_insert[f"per_year_{c}"] = ceil(sus[c] / 5)
        to_insert[f"current_{c}"] = ceil(sus[c] / 5)
        to_insert[f"withdrawn_{c}"] = 0

    investor_table.insert(to_insert)

    utils.log_action(
        f"Inserted investment for {args['<account>']} with per year allocations of `{to_insert['per_year_smp']}` on SMP, `{to_insert['per_year_mpi']}` on MPI, `{to_insert['per_year_gpu']}` on GPU, and `{to_insert['per_year_htc']}` on HTC"
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
    od["start_date"] = od["start_date"].strftime("%m/%d/%y")
    od["end_date"] = od["end_date"].strftime("%m/%d/%y")

    print("Proposal")
    print("--------")
    print(json.dumps(od, indent=2))
    print()

    ods = investor_table.find(account=args["<account>"])
    for idx, od in enumerate(ods):
        od["proposal_type"] = utils.ProposalType(od["proposal_type"]).name
        od["start_date"] = od["start_date"].strftime("%m/%d/%y")
        od["end_date"] = od["end_date"].strftime("%m/%d/%y")

        print(f"Investment: {idx:3}")
        print(f"---------------")
        print(json.dumps(od, indent=2))
        print()

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
    proposal_table.update(od, ["id"])

    utils.log_action(
        f"Modified proposal for {args['<account>']} with `{sus['smp']}` on SMP, `{sus['mpi']}` on MPI, `{sus['gpu']}` on GPU, and `{sus['htc']}` on HTC"
    )

elif args["add"]:
    # Account must exist in database
    _ = utils.unwrap_if_right(
        utils.account_exists_in_table(proposal_table, args["<account>"])
    )

    # Service units should be a valid number
    sus = utils.unwrap_if_right(
        utils.check_service_units_valid(args, CLUSTERS, greater_than_ten_thousand=False)
    )

    # Update row in database
    od = proposal_table.find_one(account=args["<account>"])
    for clus in CLUSTERS:
        od[clus] += sus[clus]
    proposal_table.update(od, ["id"])

    utils.log_action(
        f"Added SUs to proposal for {args['<account>']}, new limits are `{od['smp']}` on SMP, `{od['mpi']}` on MPI, `{od['gpu']}` on GPU, and `{od['htc']}` on HTC"
    )

elif args["change"]:
    # Account must exist in database
    _ = utils.unwrap_if_right(
        utils.account_exists_in_table(proposal_table, args["<account>"])
    )

    # Service units should be a valid number
    sus = utils.unwrap_if_right(utils.check_service_units_valid(args, CLUSTERS))

    # Update row in database
    od = proposal_table.find_one(account=args["<account>"])
    for clus in CLUSTERS:
        od[clus] = sus[clus]
    proposal_table.update(od, ["id"])

    utils.log_action(
        f"Changed proposal for {args['<account>']} with `{sus['smp']}` on SMP, `{sus['mpi']}` on MPI, `{sus['gpu']}` on GPU, and `{sus['htc']}` on HTC"
    )

elif args["date"]:
    # Account must exist in database
    _ = utils.unwrap_if_right(
        utils.account_exists_in_table(proposal_table, args["<account>"])
    )

    # Date should be valid
    start_date = utils.unwrap_if_right(utils.check_date_valid(args["<date>"]))

    # Update row in database
    od = proposal_table.find_one(account=args["<account>"])
    proposal_duration = utils.get_proposal_duration(
        utils.ProposalType(od["proposal_type"])
    )
    end_date = start_date + proposal_duration
    od["start_date"] = start_date
    od["end_date"] = end_date
    proposal_table.update(od, ["id"])

    utils.log_action(
        f"Modify proposal start date for {args['<account>']} to {start_date}"
    )

elif args["check_sus_limit"]:
    # Account must exist in database
    _ = utils.unwrap_if_right(
        utils.account_exists_in_table(proposal_table, args["<account>"])
    )

    # Compute the Total SUs for the proposal period
    proposal_row = proposal_table.find_one(account=args["<account>"])
    total_sus = sum([proposal_row[cluster] for cluster in CLUSTERS])

    investor_rows = investor_table.find(account=args["<account>"])
    for investor_row in investor_rows:
        total_sus += sum([investor_row[f"current_{cluster}"] for cluster in CLUSTERS])

    # Parse the used SUs for the proposal period
    used_sus = 0
    for cluster in CLUSTERS:
        used_sus += utils.get_raw_usage_in_hours(args["<account>"], cluster)

    # TODO: Finish this functionality
    if used_sus > total_sus:
        utils.lock_account(args["<account>"])
        utils.notify_sus_limit(args["<account>"])

else:
    raise NotImplementedError("The requested command isn't implemented yet.")

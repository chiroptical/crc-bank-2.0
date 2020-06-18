#!/usr/bin/env /ihome/sam/cluster/scripts/python3.7_wrap.sh
""" crc_bank.py -- Deal with crc_bank.db
Usage:
    crc_bank.py insert <type> <account> [-s <sus>] [-m <sus>] [-g <sus>] [-c <sus>]
    crc_bank.py modify <account> [-s <sus>] [-m <sus>] [-g <sus>] [-c <sus>]
    crc_bank.py add <account> [-s <sus>] [-m <sus>] [-g <sus>] [-c <sus>]
    crc_bank.py change <account> [-s <sus>] [-m <sus>] [-g <sus>] [-c <sus>]
    crc_bank.py date <account> <date>
    crc_bank.py investor <account> [-s <sus>] [-m <sus>] [-g <sus>] [-c <sus>]
    crc_bank.py withdraw <account> [-s <sus>] [-m <sus>] [-g <sus>] [-c <sus>]
    crc_bank.py renewal <account> [-s <sus>] [-m <sus>] [-g <sus>] [-c <sus>]
    crc_bank.py info <account>
    crc_bank.py usage <account>
    crc_bank.py check_sus_limit <account>
    crc_bank.py check_proposal_end_date <account>
    crc_bank.py check_proposal_violations
    crc_bank.py get_sus <account>
    crc_bank.py dump <proposal.json> <investor.json> <proposal_archive.json> <investor_archive.json>
    crc_bank.py -h | --help
    crc_bank.py -v | --version

Options:
    -h --help               Print this screen and exit
    -v --version            Print the version of crc_bank.py
    -s --smp <sus>          The smp limit in CPU Hours [default: 0]
    -m --mpi <sus>          The mpi limit in CPU Hours [default: 0]
    -g --gpu <sus>          The gpu limit in CPU Hours [default: 0]
    -c --htc <sus>          The htc limit in CPU Hours [default: 0]

Positional Arguments:
    <account>               The associated slurm account
    <type>                  The proposal type: proposal or class
    <date>                  Change proposal start date (e.g 12/01/19)
    <proposal.json>         The proposal table in JSON format
    <investor.json>         The investor table in JSON format
    <investor_archive.json> The investor archival table in JSON format

Additional Documentation:
    crc_bank.py insert # insert for the first time
    crc_bank.py modify # change to new limits, update proposal date
    crc_bank.py add    # add SUs on top of current values
    crc_bank.py change # change to new limits, don't change proposal date
"""


from docopt import docopt
from datetime import date, timedelta
import utils
import json
from math import ceil
from pathlib import Path
from constants import (
    CLUSTERS,
    proposal_table,
    investor_table,
    proposal_archive_table,
    investor_archive_table,
)
from copy import copy
from io import StringIO


args = docopt(__doc__, version="crc_bank.py version 0.0.1")


if args["insert"]:
    # Account shouldn't exist in the proposal table already
    x = utils.account_exists_in_table(proposal_table, args["<account>"])
    if isinstance(x, utils.Right):
        exit(f"Proposal for account `{args['<account>']}` already exists. Exiting...")

    # Account associations better exist!
    _ = utils.unwrap_if_right(
        utils.account_and_cluster_associations_exists(args["<account>"])
    )

    # Make sure we understand the proposal type
    proposal_type = utils.unwrap_if_right(utils.parse_proposal_type(args["<type>"]))
    proposal_duration = utils.get_proposal_duration(proposal_type)
    start_date = date.today()
    end_date = start_date + proposal_duration

    # Service units should be a valid number
    sus = utils.unwrap_if_right(utils.check_service_units_valid(args))

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
        utils.account_and_cluster_associations_exists(args["<account>"])
    )

    # Investor accounts last 5 years
    proposal_type = utils.ProposalType.Investor
    start_date = date.today()
    end_date = start_date + timedelta(days=1825)

    # Service units should be a valid number
    sus = utils.unwrap_if_right(utils.check_service_units_valid(args))

    to_insert = {
        "account": args["<account>"],
        "proposal_type": proposal_type.value,
        "start_date": start_date,
        "end_date": end_date,
        "years": 1,
    }
    for c in CLUSTERS:
        to_insert[c] = sus[c]
        to_insert[f"current_{c}"] = ceil(sus[c] / 5)
        to_insert[f"withdrawn_{c}"] = ceil(sus[c] / 5)
        to_insert[f"rollover_{c}"] = 0

    investor_table.insert(to_insert)

    current_sus = {c: to_insert[f"current_{c}"] for c in CLUSTERS}

    utils.log_action(
        f"Inserted investment for {args['<account>']} with per year allocations of `{current_sus['smp']}` on SMP, `{current_sus['mpi']}` on MPI, `{current_sus['gpu']}` on GPU, and `{current_sus['htc']}` on HTC"
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
    for od in ods:
        od["proposal_type"] = utils.ProposalType(od["proposal_type"]).name
        od["start_date"] = od["start_date"].strftime("%m/%d/%y")
        od["end_date"] = od["end_date"].strftime("%m/%d/%y")

        print(f"Investment: {od['id']:3}")
        print(f"---------------")
        print(json.dumps(od, indent=2))
        print()

elif args["modify"]:
    # Account must exist in database
    _ = utils.unwrap_if_right(
        utils.account_exists_in_table(proposal_table, args["<account>"])
    )

    # Service units should be a valid number
    sus = utils.unwrap_if_right(utils.check_service_units_valid(args))

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
        utils.check_service_units_valid(args, greater_than_ten_thousand=False)
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
    sus = utils.unwrap_if_right(utils.check_service_units_valid(args))

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
    # This is a complicated function, the steps:
    # 1. Get proposal for account and compute the total SUs from proposal
    # 2. Determine the current usage for the user across clusters
    # 3. Add any investment SUs to the total, archiving any exhausted investments
    # 4. Add archived investments associated to the current proposal

    # Account must exist in database
    _ = utils.unwrap_if_right(
        utils.account_exists_in_table(proposal_table, args["<account>"])
    )

    # Compute the Total SUs for the proposal period
    proposal_row = proposal_table.find_one(account=args["<account>"])
    total_sus = sum([proposal_row[cluster] for cluster in CLUSTERS])

    # Parse the used SUs for the proposal period
    used_sus_per_cluster = {c: 0 for c in CLUSTERS}
    for cluster in CLUSTERS:
        used_sus_per_cluster[cluster] = utils.get_raw_usage_in_hours(
            args["<account>"], cluster
        )
    used_sus = sum(used_sus_per_cluster.values())

    # Compute the sum of investment SUs, archiving any exhausted proposals
    investor_rows = investor_table.find(account=args["<account>"])
    sum_investment_sus = 0
    for investor_row in investor_rows:
        # Check if investment is exhausted
        exhausted = {c: False for c in CLUSTERS}
        for cluster in CLUSTERS:
            if investor_row[cluster] - investor_row[f"withdrawn_{cluster}"] == 0 and (
                used_sus_per_cluster[cluster]
                >= (
                    proposal_row[cluster]
                    + sum_investment_sus
                    + investor_row[f"current_{cluster}"]
                )
                or investor_row[f"current_{cluster}"] == 0
            ):
                exhausted[cluster] = True
        if all(exhausted.values()):
            to_insert = {}
            for cluster in CLUSTERS:
                to_insert[cluster] = investor_row[cluster]
                to_insert[f"current_{cluster}"] = investor_row[f"current_{cluster}"]
            to_insert["start_date"] = investor_row["start_date"]
            to_insert["end_date"] = investor_row["end_date"]
            to_insert["exhaustion_date"] = date.today()
            to_insert["account"] = args["<account>"]
            to_insert["proposal_id"] = proposal_row["id"]
            to_insert["investment_id"] = investor_row["id"]
            investor_archive_table.insert(to_insert)
            investor_table.delete(id=investor_row["id"])
        else:
            sum_investment_sus += sum(
                [investor_row[f"current_{cluster}"] for cluster in CLUSTERS]
            )

    total_sus += sum_investment_sus

    # Compute the sum of any archived investments associated with this proposal
    investor_archive_rows = investor_archive_table.find(proposal_id=proposal_row["id"])
    sum_investor_archive_sus = 0
    for investor_archive_row in investor_archive_rows:
        sum_investor_archive_sus += sum(
            [investor_archive_row[f"current_{c}"] for c in CLUSTERS]
        )

    total_sus += sum_investor_archive_sus

    notification_percent = utils.PercentNotified(proposal_row["percent_notified"])
    if notification_percent == utils.PercentNotified.Hundred:
        exit(
            f"Skipping account {args['<account>']} because it should have already been notified and locked"
        )

    percent_usage = 100.0 * used_sus / total_sus

    # Update percent_notified in the table and notify account owner if necessary
    updated_notification_percent = utils.find_next_notification(percent_usage)
    if updated_notification_percent != notification_percent:
        proposal_row["percent_notified"] = updated_notification_percent.value
        proposal_table.update(proposal_row, ["id"])
        utils.notify_sus_limit(args["<account>"])

        utils.log_action(
            f"Updated proposal percent_notified to {updated_notification_percent} for {args['<account>']}"
        )

    # Lock the account if necessary
    if updated_notification_percent == utils.PercentNotified.Hundred:
        utils.lock_account(args["<account>"])

        utils.log_action(
            f"The account for {args['<account>']} was locked due to SUs limit"
        )

elif args["check_proposal_end_date"]:
    # Account must exist in database
    _ = utils.unwrap_if_right(
        utils.account_exists_in_table(proposal_table, args["<account>"])
    )

    proposal_row = proposal_table.find_one(account=args["<account>"])
    today = date.today()
    three_months_before_end_date = proposal_row["end_date"] - timedelta(days=90)

    if today == three_months_before_end_date:
        utils.three_month_proposal_expiry_notification(args["<account>"])
    elif today == proposal_row["end_date"]:
        utils.proposal_expires_notification(args["<account>"])
        utils.lock_account(args["<account>"])
        utils.log_action(
            f"The account for {args['<account>']} was locked because it reached the end date {proposal_row['end_date']}"
        )

elif args["get_sus"]:
    # Account must exist in database
    _ = utils.unwrap_if_right(
        utils.account_exists_in_table(proposal_table, args["<account>"])
    )

    proposal_row = proposal_table.find_one(account=args["<account>"])

    print(f"type,{','.join(CLUSTERS)}")
    sus = [str(proposal_row[c]) for c in CLUSTERS]
    print(f"proposal,{','.join(sus)}")

    investor_sus = utils.get_current_investor_sus(args["<account>"])
    for row in investor_sus:
        sus = [str(row[c]) for c in CLUSTERS]
        print(f"investment,{','.join(sus)}")

elif args["dump"]:
    proposal_p = Path(args["<proposal.json>"])
    investor_p = Path(args["<investor.json>"])
    proposal_archive_p = Path(args["<proposal_archive.json>"])
    investor_archive_p = Path(args["<investor_archive.json>"])
    if (
        proposal_p.exists()
        or investor_p.exists()
        or investor_archive_p.exists()
        or proposal_archive_p.exists()
    ):
        exit(
            f"ERROR: Neither {proposal_p}, {investor_p}, {proposal_archive_p}, nor {investor_archive_p} can exist."
        )
    else:
        utils.freeze_if_not_empty(proposal_table.all(), proposal_p)
        utils.freeze_if_not_empty(investor_table.all(), investor_p)
        utils.freeze_if_not_empty(proposal_archive_table.all(), proposal_archive_p)
        utils.freeze_if_not_empty(investor_archive_table.all(), investor_archive_p)

elif args["withdraw"]:
    # Account must exist in database
    _ = utils.unwrap_if_right(
        utils.account_exists_in_table(proposal_table, args["<account>"])
    )

    # Service units should be a valid number
    sus_to_withdraw = utils.unwrap_if_right(
        utils.check_service_units_valid(args, greater_than_ten_thousand=False)
    )

    # First check if the user has enough SUs to withdraw
    available_investments = utils.sum_investments(
        utils.get_available_investor_sus(args["<account>"])
    )

    should_exit = False
    for c in CLUSTERS:
        if sus_to_withdraw[c] > available_investments[c]:
            should_exit = True
            print(
                f"Requested to withdraw {sus_to_withdraw[c]} on cluster {c} but the account only has {available_investments[c]} SUs to withdraw from on this cluster!"
            )
    if should_exit:
        exit()

    # Go through investments, oldest first and start withdrawing
    investments = investor_table.find(account=args["<account>"])
    for idx, investment in enumerate(investments):
        to_withdraw = {c: 0 for x in CLUSTERS}
        investment_remaining = {
            c: investment[c] - investment[f"withdrawn_{c}"] for c in CLUSTERS
        }

        # If not SUs to withdraw, skip the proposal entirely
        if sum(investment_remaining.values()) == 0:
            print(
                f"No service units can be withdrawn from investment {investment['id']}"
            )
            continue

        # Determine what we can withdraw from current investment
        for cluster in CLUSTERS:
            if sus_to_withdraw[cluster] > investment_remaining[cluster]:
                to_withdraw[cluster] = investment_remaining[cluster]
                sus_to_withdraw[cluster] -= investment_remaining[cluster]
            else:
                to_withdraw[cluster] = sus_to_withdraw[cluster]
                sus_to_withdraw[cluster] = 0

        # Update the current investment and log withdrawal
        for cluster in CLUSTERS:
            investment[f"current_{cluster}"] += to_withdraw[cluster]
            investment[f"withdrawn_{cluster}"] += to_withdraw[cluster]
        investor_table.update(investment, ["id"])
        values = ",".join([f"{c}: {to_withdraw[c]}" for c in CLUSTERS])
        utils.log_action(
            f"Withdrew from investment {investment['id']} for account {args['<account>']} with values {values}"
        )

        # Determine if we are done processing investments
        if sum(sus_to_withdraw.values()) == 0:
            print(f"Finished withdrawing after {idx} iterations")
            break

elif args["check_proposal_violations"]:
    # Iterate over all of the proposals looking for proposal violations
    proposals = proposal_table.find()
    for proposal in proposals:
        investments = utils.sum_investments(
            utils.get_available_investor_sus(proposal["account"])
        )

        for cluster in CLUSTERS:
            avail_sus = proposal[cluster]
            used_sus = utils.get_raw_usage_in_hours(proposal["account"], cluster)
            if used_sus > (avail_sus + investments[cluster]):
                print(
                    f"Account {proposal['account']}, Cluster {cluster}, Used SUs {used_sus}, Avail SUs {avail_sus}, Investment SUs {investments[cluster]}"
                )

elif args["usage"]:
    print(utils.usage_string(args["<account>"]))

elif args["renewal"]:
    # Account must exist in database
    _ = utils.unwrap_if_right(
        utils.account_exists_in_table(proposal_table, args["<account>"])
    )

    # Account associations better exist!
    _ = utils.unwrap_if_right(
        utils.account_and_cluster_associations_exists(args["<account>"])
    )

    # Make sure SUs are valid
    sus = utils.unwrap_if_right(utils.check_service_units_valid(args))

    # Archive current proposal, recording the usage on each cluster
    current_proposal = proposal_table.find_one(account=args["<account>"])
    current_usage = {
        c: utils.get_raw_usage_in_hours(args["<account>"], c) for c in CLUSTERS
    }
    to_insert = {f"{c}_usage": current_usage[c] for c in CLUSTERS}
    for key in ["account", "start_date", "end_date"] + CLUSTERS:
        to_insert[key] = current_proposal[key]
    proposal_archive_table.insert(to_insert)

    # Archive any investments which are past their end_date
    investor_rows = investor_table.find(account=args["<account>"])
    for investor_row in investor_rows:
        if investor_row["end_date"] <= date.today():
            to_insert = {}
            for cluster in CLUSTERS:
                to_insert[cluster] = investor_row[cluster]
                to_insert[f"current_{cluster}"] = investor_row[f"current_{cluster}"]
            to_insert["start_date"] = investor_row["start_date"]
            to_insert["end_date"] = investor_row["end_date"]
            to_insert["exhaustion_date"] = date.today()
            to_insert["account"] = args["<account>"]
            to_insert["proposal_id"] = current_proposal["id"]
            to_insert["investment_id"] = investor_row["id"]
            investor_archive_table.insert(to_insert)
            investor_table.delete(id=investor_row["id"])

    current_investments = utils.sum_investments(
        utils.get_current_investor_sus(args["<account>"])
    )

    # If there are relevant investments,
    #     check if there is any rollover
    if sum(current_investments.values()):
        need_to_rollover = {}
        for cluster in CLUSTERS:
            # If current usage exceeds proposal, rollover some SUs, else rollover all SUs
            if current_usage[cluster] > current_proposal[cluster]:
                need_to_rollover[cluster] = (
                    current_proposal[cluster]
                    + current_investments[cluster]
                    - current_usage[cluster]
                )
            else:
                need_to_rollover[cluster] = current_investments[cluster]
            # Only half should rollover
            need_to_rollover[cluster] /= 2

            # If the current usage exceeds proposal + investments or there is no investment, no need to rollover
            if need_to_rollover[cluster] < 0 or current_investments[cluster] == 0:
                need_to_rollover[cluster] = 0

        # TODO: Explore ramifications of having rollover SUs in other functions
        # - check_sus_limit is probably broken
        # - withdraw might be broken
        if sum(need_to_rollover.values()):
            # Go through investments and roll them over
            investor_rows = investor_table.find(account=args["<account>"])
            for investor_row in investor_rows:
                for cluster in CLUSTERS:
                    if need_to_rollover[cluster] > 0:
                        to_withdraw = (
                            investor_row[f"{cluster}"]
                            - investor_row[f"withdrawn_{cluster}"]
                        ) // utils.years_left(investor_row["end_date"])
                        to_rollover = (
                            investor_row[f"current_{cluster}"]
                            if investor_row[f"current_{cluster}"]
                            < need_to_rollover[cluster]
                            else need_to_rollover[cluster]
                        )
                        investor_row[f"current_{cluster}"] = to_withdraw
                        investor_row[f"rollover_{cluster}"] = to_rollover
                        investor_row[f"withdrawn_{cluster}"] = (
                            investor_row[f"withdrawn_{cluster}"] + to_withdraw
                        )
                        investor_table.update(investor_row, ["id"])
                        need_to_rollover[cluster] -= to_rollover

    # Insert new proposal
    proposal_type = utils.ProposalType(current_proposal["proposal_type"])
    proposal_duration = utils.get_proposal_duration(proposal_type)
    start_date = date.today()
    end_date = start_date + proposal_duration
    update_with = {
        "percent_notified": utils.PercentNotified.Zero.value,
        "start_date": start_date,
        "end_date": end_date,
    }
    for c in CLUSTERS:
        update_with[c] = sus[c]
    proposal_table.update(to_insert, ["id"])

    # Unlock the account
    utils.unlock_account(args["<account>"])

    # TODO: Should we notify the PI there proposal has been renewed?

else:
    raise NotImplementedError("The requested command isn't implemented yet.")

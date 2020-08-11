#!/usr/bin/env bats

load functions

@test "renewal with rollover" {
    # Check raw_usage
    raw_usage=$(get_raw_usage sam)
    [ $raw_usage -lt 100 ]

    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    # insert investment should work
    run python crc_bank.py investor sam 10000
    [ "$status" -eq 0 ]

    # modify the proposal date to 1 year
    run python crc_bank.py date_investment sam $(date -d "-365 days" +%m/%d/%y) 1
    [ "$status" -eq 0 ]

    # proposal renewal should work
    run python crc_bank.py renewal sam --smp=10000
    [ "$status" -eq 0 ]

    # dump the tables to JSON should work
    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    # proposal table should have 1 entry with 10000 SUs
    [ $(grep -c '"count": 1' proposal.json) -eq 1 ]
    [ $(grep -c '"smp": 10000' proposal.json) -eq 1 ]

    # proposal archive should have 1 entry with 10000 SUs
    [ $(grep -c '"count": 1' proposal_archive.json) -eq 1 ]
    [ $(grep -c '"smp": 10000' proposal_archive.json) -eq 1 ]

    # investor table should have rollover SUs
    [ $(grep -c '"count": 1' investor.json) -eq 1 ]
    [ $(grep -c '"service_units": 10000' investor.json) -eq 1 ]
    [ $(grep -c '"current_sus": 2000' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_sus": 4000' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_sus": 1000' investor.json) -eq 1 ]

    # clean up database and JSON files
    clean
}

@test "double renewal with rollover" {
    # Check raw_usage
    raw_usage=$(get_raw_usage sam)
    [ $raw_usage -lt 100 ]

    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    # insert investment should work
    run python crc_bank.py investor sam 10000
    [ "$status" -eq 0 ]

    # modify the proposal date to 1 year
    run python crc_bank.py date_investment sam $(date -d "-365 days" +%m/%d/%y) 1
    [ "$status" -eq 0 ]

    # proposal renewal should work
    run python crc_bank.py renewal sam --smp=10000
    [ "$status" -eq 0 ]

    # modify the proposal date to 2 years (might fail on leap years?)
    run python crc_bank.py date_investment sam $(date -d "-730 days" +%m/%d/%y) 1
    [ "$status" -eq 0 ]

    # proposal renewal should work
    run python crc_bank.py renewal sam --smp=10000
    [ "$status" -eq 0 ]

    # dump the tables to JSON should work
    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    # proposal table should have 1 entry with 10000 SUs
    [ $(grep -c '"count": 1' proposal.json) -eq 1 ]
    [ $(grep -c '"smp": 10000' proposal.json) -eq 1 ]

    # proposal archive should have 2 entry with 10000 SUs
    [ $(grep -c '"count": 2' proposal_archive.json) -eq 1 ]
    [ $(grep -c '"smp": 10000' proposal_archive.json) -eq 2 ]

    # investor table should have rollover SUs
    [ $(grep -c '"count": 1' investor.json) -eq 1 ]
    [ $(grep -c '"service_units": 10000' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_sus": 1000' investor.json) -eq 1 ]
    [ $(grep -c '"current_sus": 2000' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_sus": 6000' investor.json) -eq 1 ]

    # clean up database and JSON files
    clean
}

@test "after withdraw renew twice should archive investment" {
    # Check raw_usage
    raw_usage=$(get_raw_usage sam)
    [ $raw_usage -lt 100 ]

    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    # insert investment should work
    run python crc_bank.py investor sam 10000
    [ "$status" -eq 0 ]

    # withdraw all investor SUs
    run python crc_bank.py withdraw sam 8000
    [ "$status" -eq 0 ]

    # proposal renewal should work
    run python crc_bank.py renewal sam --smp=10000
    [ "$status" -eq 0 ]

    # dump the tables to JSON should work
    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    # proposal table should have 1 entry with 10000 SUs
    [ $(grep -c '"count": 1' proposal.json) -eq 1 ]
    [ $(grep -c '"smp": 10000' proposal.json) -eq 1 ]

    # proposal archive should have 2 entry with 10000 SUs
    [ $(grep -c '"count": 1' proposal_archive.json) -eq 1 ]
    [ $(grep -c '"smp": 10000' proposal_archive.json) -eq 1 ]

    # investor table should have rollover SUs
    [ $(grep -c '"count": 1' investor.json) -eq 1 ]
    [ $(grep -c '"service_units": 10000' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_sus": 5000' investor.json) -eq 1 ]
    [ $(grep -c '"current_sus": 0' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_sus": 10000' investor.json) -eq 1 ]

    run rm proposal.json investor.json proposal_archive.json investor_archive.json

    # proposal renewal should work
    run python crc_bank.py renewal sam --smp=10000
    [ "$status" -eq 0 ]

    # dump the tables to JSON should work
    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    # proposal table should have 1 entry with 10000 SUs
    [ $(grep -c '"count": 1' proposal.json) -eq 1 ]
    [ $(grep -c '"smp": 10000' proposal.json) -eq 1 ]

    # proposal archive should have 2 entry with 10000 SUs
    [ $(grep -c '"count": 2' proposal_archive.json) -eq 1 ]
    [ $(grep -c '"smp": 10000' proposal_archive.json) -eq 2 ]

    # investor table should be empty
    [ $(wc -l investor.json | awk '{print $1}') -eq 1 ]
    [ $(grep -c '{}' investor.json) -eq 1 ]

    # investor archive should have one investment
    [ $(grep -c '"count": 1' investor_archive.json) -eq 1 ]

    clean
}

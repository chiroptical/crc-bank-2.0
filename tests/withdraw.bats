#!/usr/bin/env bats

load functions

@test "withdraw works" {
    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    # insert investment should work
    run python crc_bank.py investor sam 10000
    [ "$status" -eq 0 ]

    # withdraw from investment
    run python crc_bank.py withdraw sam 8000
    [ "$status" -eq 0 ]

    # dump the tables to JSON should work
    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    # investor table should have rollover SUs
    [ $(grep -c '"count": 1' investor.json) -eq 1 ]
    [ $(grep -c '"service_units": 10000' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_sus": 0' investor.json) -eq 1 ]
    [ $(grep -c '"current_sus": 10000' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_sus": 10000' investor.json) -eq 1 ]

    # clean up database and JSON files
    clean
}

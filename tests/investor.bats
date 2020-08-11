#!/usr/bin/env bats

load functions

@test "investor fails with no proposal" {
    # insert investment should not work
    run python crc_bank.py investor sam 10000
    [ "$status" -eq 1 ]

    clean
}

@test "investor works" {
    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    # insert investment should work
    run python crc_bank.py investor sam 10000
    [ "$status" -eq 0 ]

    # dump the tables to JSON should work
    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    # proposal table should have 1 entry with 10000 SUs
    [ $(grep -c '"count": 1' proposal.json) -eq 1 ]
    [ $(grep -c '"smp": 10000' proposal.json) -eq 1 ]
    [ $(grep -c '"gpu": 0' proposal.json) -eq 1 ]
    [ $(grep -c '"htc": 0' proposal.json) -eq 1 ]
    [ $(grep -c '"mpi": 0' proposal.json) -eq 1 ]

    # investor table should not have rollover SUs
    [ $(grep -c '"count": 1' investor.json) -eq 1 ]
    [ $(grep -c '"service_units": 10000' investor.json) -eq 1 ]
    [ $(grep -c '"current_sus": 2000' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_sus": 2000' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_sus": 0' investor.json) -eq 1 ]

    # clean up database and JSON files
    clean
}

#!/usr/bin/env bats

load functions

@test "insert works" {
    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    # info should work and print something
    run python crc_bank.py info sam
    [ "$status" -eq 0 ]
    [ "$output" != "" ]

    # dump the tables to JSON should work
    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    # proposal should have 1 smp entry with 10000 SUs
    [ $(grep -c '"count": 1' proposal.json) -eq 1 ]
    [ $(grep -c '"smp": 10000' proposal.json) -eq 1 ]
    [ $(grep -c '"gpu": 0' proposal.json) -eq 1 ]
    [ $(grep -c '"htc": 0' proposal.json) -eq 1 ]
    [ $(grep -c '"mpi": 0' proposal.json) -eq 1 ]
    [ $(grep -c "\"start_date\": \"$(date +%F)\"" proposal.json) -eq 1 ]

    # all other tables should be empty
    [ $(grep -c '{}' proposal_archive.json) -eq 1 ]
    [ $(grep -c '{}' investor.json) -eq 1 ]
    [ $(grep -c '{}' investor_archive.json) -eq 1 ]

    # clean up database and JSON files
    clean
}

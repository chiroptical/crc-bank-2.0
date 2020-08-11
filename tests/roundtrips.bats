#!/usr/bin/env bats

load functions

@test "roundtrip proposal.json" {
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    run python crc_bank.py insert proposal root --mpi=10000
    [ "$status" -eq 0 ]

    run python crc_bank.py insert proposal kjordan --gpu=10000
    [ "$status" -eq 0 ]

    # dump the tables to JSON should work
    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    # make a copy of the proposal.json and investor.json to compare with
    run cp proposal.json proposal.json.init
    [ "$status" -eq 0 ]

    # import the copied proposal.json table
    run python crc_bank.py import_proposal proposal.json.init -y
    [ "$status" -eq 0 ]

    # clean up old dumps
    run rm proposal.json investor.json proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    # dump the tables to JSON should work
    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    run cmp -s proposal.json proposal.json.init
    [ "$status" -eq 0 ]

    # clean up database and JSON files
    clean
    run rm proposal.json.init
}

@test "roundtrip investor.json" {
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]
    
    run python crc_bank.py investor sam 10000
    [ "$status" -eq 0 ]

    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    run cp investor.json investor.json.init
    [ "$status" -eq 0 ]

    run python crc_bank.py import_investor investor.json.init -y
    [ "$status" -eq 0 ]

    run rm proposal.json investor.json proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    run cmp -s investor.json investor.json.init
    [ "$status" -eq 0 ]

    clean
    run rm investor.json.init
}

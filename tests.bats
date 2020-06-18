#!/usr/bin/env bats

load functions

@test "run with no args, exit 1" {
    run python crc_bank.py
    [ "$status" -eq 1 ]
}

@test "run with --help, exit 0" {
    run python crc_bank.py --help
    [ "$status" -eq 0 ]
}

@test "basic insert works" {
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    run python crc_bank.py info sam
    [ "$status" -eq 0 ]
    [ "$output" != "" ]
    clean
}

@test "renewal with rollover" {
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    run python crc_bank.py investor sam --smp=10000
    [ "$status" -eq 0 ]

    run python crc_bank.py renewal sam --smp=10000
    [ "$status" -eq 0 ]

    run python crc_bank.py dump proposal.json investor.json proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    [ $(grep -c '"count": 1' proposal.json) -eq 1 ]
    [ $(grep -c '"smp": 10000' proposal.json) -eq 1 ]

    [ $(grep -c '"count": 1' proposal_archive.json) -eq 1 ]
    [ $(grep -c '"smp": 10000' proposal_archive.json) -eq 1 ]

    [ $(grep -c '"count": 1' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_smp": 1000' investor.json) -eq 1 ]
    [ $(grep -c '"current_smp": 1600' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_smp": 3600' investor.json) -eq 1 ]

    clean
}

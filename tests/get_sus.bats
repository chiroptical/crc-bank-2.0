#!/usr/bin/env bats

load functions

@test "get_sus works" {
    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    # insert investment should work
    run python crc_bank.py investor sam 10000
    [ "$status" -eq 0 ]

    # get_sus should work and produce output
    run python crc_bank.py get_sus sam
    [ "$status" -eq 0 ]
    [ $(echo $output | grep -c "proposal,10000,0,0,0") -eq 1 ]
    [ $(echo $output | grep -c "investment,2000") -eq 1 ]

    # clean up database and JSON files
    clean
}

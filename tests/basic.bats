#!/usr/bin/env bats

load functions

@test "run with no args, exit 1" {
    run python crc_bank.py
    [ "$status" -eq 1 ]

    clean
}

@test "run with --help, exit 0, print something" {
    run python crc_bank.py --help
    [ "$status" -eq 0 ]
    [ "$output" != "" ]

    clean
}

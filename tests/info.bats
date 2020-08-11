#!/usr/bin/env bats

load functions

@test "info fails with no proposal" {
    run python crc_bank.py info sam
    [ "$status" -eq 1 ]

    clean
}

@test "info works with proposal" {
    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    run python crc_bank.py info sam
    [ "$status" -eq 0 ]

    clean
}

#!/usr/bin/env bats

load functions

@test "usage fails with no proposal" {
    run python crc_bank.py usage sam
    [ "$status" -eq 1 ]

    clean
}

@test "usage works" {
    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    run python crc_bank.py usage sam
    [ "$status" -eq 0 ]
    [ $(echo $output | grep -c "Aggregate") -gt 0 ]
    [ $(echo $output | grep -c "Investment") -eq 0 ]

    clean
}

@test "usage with investment works" {
    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    # insert investment should work
    run python crc_bank.py investor sam 10000
    [ "$status" -eq 0 ]

    run python crc_bank.py usage sam
    [ "$status" -eq 0 ]
    [ $(echo $output | grep -c "Aggregate") -gt 0 ]
    [ $(echo $output | grep -c "Investment") -gt 0 ]

    clean
}

#!/usr/bin/env bats

load functions

@test "add updates SUs" {
    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    # add proposal should work
    run python crc_bank.py add sam --mpi=10000
    [ "$status" -eq 0 ]

    # dump the tables to JSON should work
    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    # proposal should have 1 entry with 10000 SUs
    [ $(grep -c '"count": 1' proposal.json) -eq 1 ]
    [ $(grep -c '"smp": 10000' proposal.json) -eq 1 ]
    [ $(grep -c '"gpu": 0' proposal.json) -eq 1 ]
    [ $(grep -c '"htc": 0' proposal.json) -eq 1 ]
    [ $(grep -c '"mpi": 10000' proposal.json) -eq 1 ]
    
    clean
}

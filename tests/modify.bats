#!/usr/bin/env bats

load functions

@test "modify updates SUs" {
    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    # modify the proposal date to 7 days prior
    run python crc_bank.py date sam $(date -d "-7 days" +%m/%d/%y)

    # dump the tables to JSON should work
    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    # proposal should have 1 mpi entry with 10000 SUs
    [ $(grep -c '"count": 1' proposal.json) -eq 1 ]
    [ $(grep -c '"smp": 10000' proposal.json) -eq 1 ]
    [ $(grep -c '"gpu": 0' proposal.json) -eq 1 ]
    [ $(grep -c '"htc": 0' proposal.json) -eq 1 ]
    [ $(grep -c '"mpi": 0' proposal.json) -eq 1 ]
    [ $(grep -c "\"start_date\": \"$(date -d '-7 days' +%F)\"" proposal.json) -eq 1 ]

    # modify proposal should work
    run python crc_bank.py modify sam --mpi=10000
    [ "$status" -eq 0 ]

    # dump the tables to JSON should work
    run rm proposal.json investor.json proposal_archive.json \
        investor_archive.json
    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    # proposal should have 1 mpi entry with 10000 SUs
    [ $(grep -c '"count": 1' proposal.json) -eq 1 ]
    [ $(grep -c '"smp": 0' proposal.json) -eq 1 ]
    [ $(grep -c '"gpu": 0' proposal.json) -eq 1 ]
    [ $(grep -c '"htc": 0' proposal.json) -eq 1 ]
    [ $(grep -c '"mpi": 10000' proposal.json) -eq 1 ]
    [ $(grep -c "\"start_date\": \"$(date +%F)\"" proposal.json) -eq 1 ]
    
    clean
}

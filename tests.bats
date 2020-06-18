#!/usr/bin/env bats

load functions

@test "run with no args, exit 1" {
    run python crc_bank.py
    [ "$status" -eq 1 ]
}

@test "run with --help, exit 0, print something" {
    run python crc_bank.py --help
    [ "$status" -eq 0 ]
    [ "$output" != "" ]
}

@test "info fails with no proposal" {
    run python crc_bank.py info sam
    [ "$status" -eq 1 ]
}

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

    # all other tables should be empty
    [ $(grep -c '{}' proposal_archive.json) -eq 1 ]
    [ $(grep -c '{}' investor.json) -eq 1 ]
    [ $(grep -c '{}' investor_archive.json) -eq 1 ]

    # clean up database and JSON files
    clean
}

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

@test "change updates SUs" {
    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    # modify the proposal date to 7 days prior
    run python crc_bank.py date sam $(date -d "-7 days" +%m/%d/%y)

    # modify proposal should work
    run python crc_bank.py change sam --mpi=10000
    [ "$status" -eq 0 ]

    # dump the tables to JSON should work
    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    # proposal should have 1 mpi entry with 10000 SUs
    [ $(grep -c '"count": 1' proposal.json) -eq 1 ]
    [ $(grep -c '"smp": 0' proposal.json) -eq 1 ]
    [ $(grep -c '"gpu": 0' proposal.json) -eq 1 ]
    [ $(grep -c '"htc": 0' proposal.json) -eq 1 ]
    [ $(grep -c '"mpi": 10000' proposal.json) -eq 1 ]
    [ $(grep -c "\"start_date\": \"$(date -d '-7 days' +%F)\"" proposal.json) -eq 1 ]
    
    clean
}

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

@test "investor fails with no proposal" {
    # insert investment should not work
    run python crc_bank.py investor sam --smp=10000
    [ "$status" -eq 1 ]
}

@test "investor works" {
    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    # insert investment should work
    run python crc_bank.py investor sam --smp=10000
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
    [ $(grep -c '"rollover_smp": 0' investor.json) -eq 1 ]
    [ $(grep -c '"current_smp": 2000' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_smp": 2000' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_gpu": 0' investor.json) -eq 1 ]
    [ $(grep -c '"current_gpu": 0' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_gpu": 0' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_htc": 0' investor.json) -eq 1 ]
    [ $(grep -c '"current_htc": 0' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_htc": 0' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_mpi": 0' investor.json) -eq 1 ]
    [ $(grep -c '"current_mpi": 0' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_mpi": 0' investor.json) -eq 1 ]

    # clean up database and JSON files
    clean
}

@test "renewal with rollover" {
    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    # insert investment should work
    run python crc_bank.py investor sam --smp=10000
    [ "$status" -eq 0 ]

    # proposal renewal should work
    run python crc_bank.py renewal sam --smp=10000
    [ "$status" -eq 0 ]

    # dump the tables to JSON should work
    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    # proposal table should have 1 entry with 10000 SUs
    [ $(grep -c '"count": 1' proposal.json) -eq 1 ]
    [ $(grep -c '"smp": 10000' proposal.json) -eq 1 ]

    # proposal archive should have 1 entry with 10000 SUs
    [ $(grep -c '"count": 1' proposal_archive.json) -eq 1 ]
    [ $(grep -c '"smp": 10000' proposal_archive.json) -eq 1 ]

    # investor table should have rollover SUs
    [ $(grep -c '"count": 1' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_smp": 1000' investor.json) -eq 1 ]
    [ $(grep -c '"current_smp": 1600' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_smp": 3600' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_gpu": 0' investor.json) -eq 1 ]
    [ $(grep -c '"current_gpu": 0' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_gpu": 0' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_htc": 0' investor.json) -eq 1 ]
    [ $(grep -c '"current_htc": 0' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_htc": 0' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_mpi": 0' investor.json) -eq 1 ]
    [ $(grep -c '"current_mpi": 0' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_mpi": 0' investor.json) -eq 1 ]

    # clean up database and JSON files
    clean
}

@test "withdraw works" {
    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    # insert investment should work
    run python crc_bank.py investor sam --smp=10000
    [ "$status" -eq 0 ]

    # withdraw from investment
    run python crc_bank.py withdraw sam --smp=8000
    [ "$status" -eq 0 ]

    # dump the tables to JSON should work
    run python crc_bank.py dump proposal.json investor.json \
        proposal_archive.json investor_archive.json
    [ "$status" -eq 0 ]

    # investor table should have rollover SUs
    [ $(grep -c '"count": 1' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_smp": 0' investor.json) -eq 1 ]
    [ $(grep -c '"current_smp": 10000' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_smp": 10000' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_gpu": 0' investor.json) -eq 1 ]
    [ $(grep -c '"current_gpu": 0' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_gpu": 0' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_htc": 0' investor.json) -eq 1 ]
    [ $(grep -c '"current_htc": 0' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_htc": 0' investor.json) -eq 1 ]
    [ $(grep -c '"rollover_mpi": 0' investor.json) -eq 1 ]
    [ $(grep -c '"current_mpi": 0' investor.json) -eq 1 ]
    [ $(grep -c '"withdrawn_mpi": 0' investor.json) -eq 1 ]

    # clean up database and JSON files
    clean
}

@test "get_sus works" {
    # insert proposal should work
    run python crc_bank.py insert proposal sam --smp=10000
    [ "$status" -eq 0 ]

    # insert investment should work
    run python crc_bank.py investor sam --smp=10000
    [ "$status" -eq 0 ]

    # get_sus should work and produce output
    run python crc_bank.py get_sus sam
    [ "$status" -eq 0 ]
    [ $(echo $output | grep -c "proposal,10000,0,0,0") -eq 1 ]
    [ $(echo $output | grep -c "investment,2000,0,0,0") -eq 1 ]

    # clean up database and JSON files
    clean
}

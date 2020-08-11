#!/usr/bin/env bash

clean () {
    if [ -f "test.db" ]; then
        rm test.db
    fi
    if [ -f "logs/crc_bank.log" ]; then
        rm logs/crc_bank.log
    fi
    if [ -f "proposal.json" ]; then
        rm proposal.json
    fi
    if [ -f "investor.json" ]; then
        rm investor.json
    fi
    if [ -f "proposal_archive.json" ]; then
        rm proposal_archive.json
    fi
    if [ -f "investor_archive.json" ]; then
        rm investor_archive.json
    fi
}

get_raw_usage () {
    echo $(sshare -A $1 -o rawusage -p | sed -n 2p | cut -d'|' -f1)
}

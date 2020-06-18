#!/usr/bin/env bash

clean () {
    if [ -f "crc_bank.db" ]; then
        rm crc_bank.db
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

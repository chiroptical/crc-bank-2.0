#!/usr/bin/env bash

home_dir=/ihome/crc/bank
email='noreply@pitt.edu'
crc_bank=$home_dir/crc_bank.py
cron_logs=$home_dir/logs/cron.log

# generate a list of all of the accounts
accounts=($(sacctmgr list accounts -n -P format=account))

for acc in ${accounts[@]}; do
    $crc_bank info $acc &> /dev/null
    if [ $? -ne 0 ]; then
        mail -s "crc_bank.py error: no account for $acc" $email <<< "Unable to find an account for $acc"
    else
        $crc_bank check_sus_limit $acc >> $cron_logs 2>&1
        $crc_bank check_proposal_end_date $acc >> $cron_logs 2>&1
    fi
done

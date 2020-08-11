#!/usr/bin/env bash

rm test.db proposal.json investor.json proposal_archive.json investor_archive.json

if [ $(grep -c "^db = dataset.connect(\"sqlite:///crc_bank.db\")" constants.py) -eq 0 ]; then
    sudo sacctmgr -i modify account where account=sam cluster=smp,gpu,mpi,htc set rawusage=0
    for bat in $(ls tests/*.bats); do
        echo "====== BEGIN $bat ======"
        bats $bat
        if [ $? -ne 0 ]; then
            exit
        fi
        echo "======  END $bat  ======"
    done
else
    echo "ERROR: please modify \`db = ...\` in \`constants.py\` to work on a test database!"
fi

#!/data/data/com.termux/files/usr/bin/bash

cd "$HOME/cryptoFirstX1" || exit 1

while true; do
    clear
    echo "=================================================="
    echo " cryptoFirstX1 BLOCKCHAIN MONITOR"
    echo "=================================================="
    date
    echo

    python blockchain_monitor.py status

    echo
    echo "Press CTRL+C to stop."
    sleep 30
done

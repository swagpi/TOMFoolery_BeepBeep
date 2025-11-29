#!/bin/bash

set -e
env -i

export DB_DIR="$HOME/gits/TOMFoolery_BeepBeep/rust" 

PORT=8000
# cd "$HOME/TOMFoolery_BeepBeep/backend"
cd "$HOME/gits/TOMFoolery_BeepBeep/backend" # TODO: Remove this line!

python3 -m venv .venv
source .venv/bin/activate

pip3 install -r requirements.txt

function update_live_data() {
    while [ true ]; do
        python3 update_live_data.py
        sleep 10
    done
}

function fetch_other_vehicle_data() {
    while [ true ]; do
        python3 fetch_other_vehicle_data.py
        sleep 600
    done
}

update_live_data &
fetch_other_vehicle_data &

uvicorn backend:app --port "$PORT" --host "0.0.0.0"

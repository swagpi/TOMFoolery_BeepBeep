#!/bin/bash

# cd $HOME/TOMFoolery_BeepBeep/backend
cd $HOME/gits/TOMFoolery_BeepBeep/backend // TODO: Remove this line!
echo $PWD

python3 -m venv .venv
source .venv/bin/activate

pip3 install -r requirements.txt

while [[ true ]]; do
    python3 backend.py
    sleep 5
done

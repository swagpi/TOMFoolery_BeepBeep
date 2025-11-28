#!/bin/bash

set -e
env -i

PORT=6666
cd $HOME/TOMFoolery_BeepBeep/backend
# cd $HOME/gits/TOMFoolery_BeepBeep/backend # TODO: Remove this line!
echo $PWD

python3 -m venv .venv
source .venv/bin/activate

pip3 install -r requirements.txt

uvicorn backend:app --port "$PORT" --host "0.0.0.0"

#!/bin/bash

env -i
set -e

CURRENT_DIR=$HOME/TOMFoolery_BeepBeep
SERVICE_DIR=$CURRENT_DIR/services
USER_SERVICE_DIR=$HOME/.config/systemd/user
SERVICES=$(find "$SERVICE_DIR" -maxdepth 1 -mindepth 1)

RUST_DIR=rust

if ! [[ -d $DB_DIR ]]; then
    mkdir -p $DB_DIR
fi

pushd "$RUST_DIR"
    cargo build --release 
    cp target/release/tomfoolery $DB_DIR/tomfoolery
popd


if ! [[ -d $USER_SERVICE_DIR ]]; then
    echo "creating user service dir"
    mkdir -p "$USER_SERVICE_DIR"
fi

for SERVICE in $SERVICES; do
    if ! [[ -f "$USER_SERVICE_DIR/$(basename $SERVICE)" ]]; then
        echo "copying service $SERVICE"
        cp "$SERVICE" "$USER_SERVICE_DIR/$(basename $SERVICE)"
    fi
done

sudo loginctl enable-linger $USER

sudo systemctl daemon-reload
sudo systemctl daemon-reexec

systemctl --user import-environment DB_DIR

systemctl --user enable backend.service
systemctl --user start backend.service

systemctl --user enable pull_data.timer
systemctl --user start pull_data.timer

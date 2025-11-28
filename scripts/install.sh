#!/bin/bash

env -i
set -e

CURRENT_DIR=$HOME/TOMFoolery_BeepBeep
SERVICE_DIR=$CURRENT_DIR/services
NGINX_SYSD_DIR=/etc/systemd/system/nginx.service.d
NGINX_SYSD_CONF="$NGINX_SYSD_DIR/override.conf"
NGINX_SYSD_LOCAL="config/override.conf"
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
    echo "copying service $SERVICE"
    cp -f "$SERVICE" "$USER_SERVICE_DIR/$(basename $SERVICE)"
done

if ! [[ -f "$NGINX_SYSD_CONF" ]]; then
    echo "copying nginx-config-path override"
    mkdir -p "$NGINX_SYSD_DIR"
    cp -f "$NGINX_SYSD_LOCAL" "$NGINX_SYSD_CONF" 
fi


sudo loginctl enable-linger $USER

sudo systemctl daemon-reload
sudo systemctl daemon-reexec

systemctl --user import-environment DB_DIR

systemctl --user enable backend.service
systemctl --user start backend.service

systemctl --user enable pull_data.timer
systemctl --user start pull_data.timer

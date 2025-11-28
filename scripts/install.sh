#!/bin/bash

set -e

CURRENT_DIR=$PWD
SERVICE_DIR=$PWD/services
USER_SERVICE_DIR=$HOME/.config/systemd/user
SERVICES=$(find $SERVICE_DIR -name "*.service")

SYSTEMD_CONF="$HOME/.config/systemd/user/system.conf"
BACKUP_CONF="/etc/systemd/system.conf.bak"

SYSTEMD_CONF_FILE="
[Manager]
UnitPath=/etc/systemd/system:/lib/systemd/system:$SERVICE_DIR
"

if ! [[ -d $USER_SERVICE_DIR ]]; then
    echo "creating user service dir"
    mkdir -p $USER_SERVICE_DIR
fi

echo "Reloading systemd daemon..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

for SERVICE in $SERVICES do
    if ! [[ -f $USER_SERVICE_DIR/$(basename $SERVICE) ]]; then
        cp $SERVICE $USER_SERVICE_DIR/$(basename $SERVICE)
    fi
done

for SERVICE in $SERVICES do
    echo "Enabling: $(basename $SERVICE)"
    systemctl --user enable $(basename $SERVICE)
    systemctl --user start $(basename $SERVICE)
    echo "Enabled: $(basename $SERVICE)"
done

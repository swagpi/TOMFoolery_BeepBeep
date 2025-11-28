#!/bin/bash

set -e

CURRENT_DIR=$PWD
SERVICE_DIR=$PWD/services
USER_SERVICE_DIR=$HOME/.config/systemd/user
SERVICES=$(find $SERVICE_DIR -name "*.service")

SYSTEMD_CONF="$HOME/.config/systemd/user/system.conf"
BACKUP_CONF="/etc/systemd/system.conf.bak"

# echo "Backing up systemd config to $BACKUP_CONF..."
# sudo cp "$SYSTEMD_CONF" "$BACKUP_CONF"

# Append custom UnitPath if not already present
# if ! grep -q "$SERVICE_DIR" "$SYSTEMD_CONF"; then
#     echo "Adding custom service path to systemd..."
#     sudo sed -i "/^\[Manager\]/a UnitPath=/etc/systemd/system:/lib/systemd/system:$SERVICE_DIR" "$SYSTEMD_CONF"
# fi

SYSTEMD_CONF_FILE="
[Manager]
UnitPath=/etc/systemd/system:/lib/systemd/system:$SERVICE_DIR
"

if ! [[ -d $USER_SERVICE_DIR ]]; then
    echo "creating user service dir"
    sudo mkdir $USER_SERVICE_DIR
fi

echo "Reloading systemd daemon..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

for SERVICE in $SERVICES do
    if ! [[ -f $USER_SERVICE_DIR/$(basename $SERVICE) ]]; then
        cp $SERVICE $USER_SERVICE_DIR/$(basename $SERVICE)
    fi

    systemctl --user enable $(basename $SERVICE)
    systemctl --user start $(basename $SERVICE)
done

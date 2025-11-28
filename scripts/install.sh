#!/bin/bash

set -e

CURRENT_DIR=$PWD
SERVICE_DIR=$PWD/services
SERVICES=$(find $SERVICE_DIR -name "*.service")

SYSTEMD_CONF="/etc/systemd/system.conf"
BACKUP_CONF="/etc/systemd/system.conf.bak"

echo "Backing up systemd config to $BACKUP_CONF..."
sudo cp "$SYSTEMD_CONF" "$BACKUP_CONF"

# Append custom UnitPath if not already present
# if ! grep -q "$SERVICE_DIR" "$SYSTEMD_CONF"; then
#     echo "Adding custom service path to systemd..."
#     sudo sed -i "/^\[Manager\]/a UnitPath=/etc/systemd/system:/lib/systemd/system:$SERVICE_DIR" "$SYSTEMD_CONF"
# fi

if ! [[ -d /etc/systemd/system.conf.d ]]; then
    echo "Creating system.conf.d folder"
    sudo mkdir /etc/systemd/system.conf.d
fi

if ! [[ -f /etc/systemd/system.conf.d/tomfoolery.conf ]]; then 
    echo "creating file in /etc/systemd/system.conf.d/tomfoolery.conf"
    cat << EOF
    [Manager]
    UnitPath=/etc/systemd/system:/lib/systemd/system:$SERVICE_DIR
    EOF > /etc/systemd/system.conf.d/tomfoolery.conf
fi

echo "Reloading systemd daemon..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

for SERVICE in $SERVICES do
    sudo systemctl enable $SERVICE
done

#!/bin/bash

set -e

CURRENT_DIR=$PWD
SERVICE_DIR=$CURRENT_DIR/services
USER_SERVICE_DIR=$HOME/.config/systemd/user
SERVICES=$(find "$SERVICE_DIR" -name "*.service")

if ! [[ -d $USER_SERVICE_DIR ]]; then
    echo "creating user service dir"
    mkdir -p "$USER_SERVICE_DIR"
fi

# echo "Reloading systemd daemon..."
# sudo systemctl daemon-reexec
# sudo systemctl daemon-reload

for SERVICE in $SERVICES; do
    if ! [[ -f "$USER_SERVICE_DIR/$(basename $SERVICE)" ]]; then
        echo "copying service $SERVICE"
        cp "$SERVICE" "$USER_SERVICE_DIR/$(basename $SERVICE)"
    fi
done

for SERVICE in $SERVICES; do
    echo "Enabling: $(basename "$SERVICE")"
    systemctl --user enable "$(basename $SERVICE)"
    systemctl --user start "$(basename $SERVICE)"
    echo "Enabled: $(basename $SERVICE)"
done

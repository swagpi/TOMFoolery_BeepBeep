#!/bin/bash

OUT_DIR="$DB_DIR/data"
TMP_DATA=/tmp/data.zip

set -e

cd "$DB_DIR"

curl "https://download.gtfs.de/germany/free/latest.zip" -o "$TMP_DATA"
unzip "$TMP_DATA" -d "$OUT_DIR"

./tomfoolery

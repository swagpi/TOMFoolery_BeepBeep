#!/bin/bash

env -i
set -e

OUT_DIR="$DB_DIR/data"
TMP_DATA=/tmp/data.zip

cd "$DB_DIR"

curl "https://download.gtfs.de/germany/free/latest.zip" -o "$TMP_DATA"
unzip -of "$TMP_DATA" -d "$OUT_DIR"

./tomfoolery

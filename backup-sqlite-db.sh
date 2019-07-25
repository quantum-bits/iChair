#!/usr/bin/env bash

SRC="./ichair.db"
DST="./ichair-$(date +%Y%m%d).db"

echo Backing up $SRC to $DST
cp $SRC $DST

#!/usr/bin/env bash

echo 'Running test_setup.sh...'
. ./test_setup.sh

echo 'Starting unit test...'
python test/test_alias.py
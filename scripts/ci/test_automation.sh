#!/usr/bin/env bash

echo 'Running test_setup.sh...'
. $TRAVIS_BUILD_DIR/scripts/ci/test_setup.sh

echo 'Starting unit test...'
python test/test_alias.py
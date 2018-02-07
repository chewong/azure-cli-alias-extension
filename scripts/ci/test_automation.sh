#!/usr/bin/env bash

##############################################
# Define colored output func
function title {
    LGREEN='\033[1;32m'
    CLEAR='\033[0m'

    echo -e ${LGREEN}$1${CLEAR}
}

title 'Running test_setup.sh...'
. $TRAVIS_BUILD_DIR/scripts/ci/test_setup.sh

title 'Starting unit tests...'
python test/test_alias.py
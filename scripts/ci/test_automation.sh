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

title 'Executing unit tests...'
coverage run azext_alias/tests/test_alias.py
#!/usr/bin/env bash
##############################################
# Define colored output func
function title {
    LGREEN='\033[1;32m'
    CLEAR='\033[0m'

    echo -e ${LGREEN}$1${CLEAR}
}

title 'Executing tests...'
python -m unittest discover $TRAVIS_BUILD_DIR/azext_alias/tests/ -v

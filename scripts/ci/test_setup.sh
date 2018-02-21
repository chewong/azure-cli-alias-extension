#!/usr/bin/env bash

##############################################
# Define colored output func
function title {
    LGREEN='\033[1;32m'
    CLEAR='\033[0m'

    echo -e ${LGREEN}$1${CLEAR}
}

cd $TRAVIS_BUILD_DIR
cd ..
export HOME_DIR=$(pwd)

title 'Cloning Azure/azure-cli...'
git clone https://github.com/Azure/azure-cli.git $HOME_DIR/azure-cli

title 'Setting PYTHONPATH...'
# Point PYTHONPATH to azure-cli-core and azext_alias
export PYTHONPATH=$HOME_DIR/azure-cli/src/azure-cli-core:$TRAVIS_BUILD_DIR/azext_alias:${PYTHONPATH}
title $PYTHONPATH

title 'Installing dependencies...'
cd $TRAVIS_BUILD_DIR
pip install -r requirements.txt

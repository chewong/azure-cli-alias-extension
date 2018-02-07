#!/usr/bin/env bash

cd $TRAVIS_BUILD_DIR
cd ..
export HOME_DIR=$(pwd)

echo 'Cloning Azure/azure-cli...'
git clone https://github.com/Azure/azure-cli.git $HOME_DIR/azure-cli

echo 'Setting PYTHONPATH'
# Set PYTHONPATH to point to azure-cli-core and azext_alias
export PYTHONPATH=$HOME_DIR/azure-cli/src/azure-cli-core:$TRAVIS_BUILD_DIR/azext_alias:${PYTHONPATH}
echo $PYTHONPATH

echo 'Installing dependencies...'
cd $TRAVIS_BUILD_DIR
pip install -r requirements.txt

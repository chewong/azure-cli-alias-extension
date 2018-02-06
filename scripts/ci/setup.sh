#!/usr/bin/env bash

cd $TRAVIS_BUILD_DIR
git clone https://github.com/Azure/azure-cli.git

echo 'Setting PYTHONPATH'
# Set PYTHONPATH to point to azure-cli-core and azext_alias
export PYTHONPATH=$TRAVIS_BUILD_DIR/azure-cli/src/azure-cli-core:$TRAVIS_BUILD_DIR/azure-cli-alias-extension/azext_alias:${PYTHONPATH}
echo $PYTHONPATH

echo 'Installing dependencies...'
cd $TRAVIS_BUILD_DIR/azure-cli-alias-extension
pip install -r requirements.txt

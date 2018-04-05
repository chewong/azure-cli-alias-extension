#!/usr/bin/env bash
##############################################
# Define colored output func
function title {
    LGREEN='\033[1;32m'
    CLEAR='\033[0m'

    echo -e ${LGREEN}$1${CLEAR}
}

# https://github.com/Azure/azure-cli-extensions/blob/master/scripts/ci/test_source.sh#L8
title "Installing azure-cli-testsdk and azure-cli..."
pip install --pre azure-cli --extra-index-url https://azurecliprod.blob.core.windows.net/edge
pip install "git+https://github.com/Azure/azure-cli@dev#egg=azure-cli-testsdk&subdirectory=src/azure-cli-testsdk" -q

title 'Installing dependencies...'
pip install -r $TRAVIS_BUILD_DIR/requirements.txt -q

title "Generating alias extension wheel file..."
python setup.py bdist_wheel >/dev/null
WHL_FILE=$(find $TRAVIS_BUILD_DIR/dist -name "alias*.whl")
title "${WHL_FILE} generated."

title "Installing alias extension..."
az extension add --source $WHL_FILE --yes
az extension list --output table

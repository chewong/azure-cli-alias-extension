# azure-cli-alias-extension
[![Build Status](https://travis-ci.org/chewong/azure-cli-alias-extension.svg?branch=dev)](https://travis-ci.org/chewong/azure-cli-alias-extension)

An Azure CLI extension that provides command alias functionality. It aims to enhance Azure CLI usuability and improve developer productivity.

## Usage
2.0.28 is the minimum version of the Azure CLI that is compatible with the alias extension. To check the version of your CLI, simply run `az --version`. A detailed guide of updating your Azure CLI client can be found here.

After updating your Azure CLI client to the latest version, run the following command to install the extension:

```bash
$ az extension add --name alias
```

Run the following to verify your installation:
```bash
$ az extension list -otable
ExtensionType    Name                       Version
---------------  -------------------------  ---------
whl              alias                      0.1.0
```

To author the alias configuration file on OSX/Ubuntu (bash):
```
$ vim ~/.azure/alias
```

To author the alias configuration file on Windows, change the directory to `%HOMEPATH%/.azure` in file explorer and edit it directly.

For the configuration file specification, please visit [az-alias-spec](https://gist.github.com/chewong/2afb67374d700b34015d146f63a79b15)

## Developing
1. Set up your Azure CLI development environment:
Configure your machine [as follow](https://github.com/Azure/azure-cli/blob/master/doc/configuring_your_machine.md#preparing-your-machine), and make sure your virtual environment is activated.

2. Set up the extension:
```bash
$ git clone https://github.com/chewong/azure-cli-alias-extension.git
$ cd azure-cli-alias-extension
$ export AZURE_EXTENSION_DIR=~/.azure/devcliextensions
$ pip install --upgrade --target $AZURE_EXTENSION_DIR/azure-cli-alias-extension $(pwd)
```
3. Continue to develop your extension.
4. Any time you make changes to your extension and want to see them reflected in the CLI, run `pip install --upgrade --target $AZURE_EXTENSION_DIR/azure-cli-alias-extension $(pwd)`.


## Building
Before building locally, make sure you have [azure-cli virtual environment](https://github.com/Azure/azure-cli/blob/master/doc/configuring_your_machine.md#preparing-your-machine) activated.
```bash
$ unset AZURE_EXTENSION_DIR
$ cd azure-cli-alias-extension
$ python setup.py bdist_wheel
$ az extension add --source dist/alias-0.1.0-py2.py3-none-any.whl --yes
$ az extension list -otable
ExtensionType    Name                       Version
---------------  -------------------------  ---------
whl              alias                      0.1.0
```

## Testing and Others
With [azure-cli virtual environment](https://github.com/Azure/azure-cli/blob/master/doc/configuring_your_machine.md#preparing-your-machine) still activated, you can run tests locally by:

```bash
$ cd azure-cli
$ export PYTHONPATH=$(pwd)/src:${PYTHONPATH}
$ cd azure-cli-alias-extension
$ pip install -r requirements.txt
$ pip install .
$ python -m unittest discover azext_alias/tests/
```

To run pylint:
```bash
$ pylint azext_alias/
```

## References
[Extension Authoring](https://github.com/Azure/azure-cli/blob/dev/doc/extensions/authoring.md)

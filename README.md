# azure-cli-alias-extension
[![Build Status](https://travis-ci.org/chewong/azure-cli-alias-extension.svg?branch=dev)](https://travis-ci.org/chewong/azure-cli-alias-extension)

An Azure CLI extension that provides command alias functionality. It aims to enhance Azure CLI usuability and improve developer productivity.

## Usage
Configure your machine [as follow](https://github.com/Azure/azure-cli/blob/master/doc/configuring_your_machine.md#preparing-your-machine), and make sure your virtual environment is activated.

Run the following commands to install the extension:

```bash
$ cd azure-cli
$ git checkout dev
$ git pull
$ az extension add --source https://github.com/chewong/azure-cli-alias-extension/releases/download/0.0.1/azure_cli_alias_extension-0.0.1-py2.py3-none-any.whl -y
```

To author the alias configuration file on OSX/Ubuntu(bash):
```
$ vim ~/.azure/alias
```

To author the alias configuration file on Windows, go to  `%HOMEPATH%/.azure` in file explorer and edit it directly.

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
$ az extension add --source dist/azure_cli_alias_extension-0.0.1-py2.py3-none-any.whl --yes
$ az extension list -otable
ExtensionType    Name                       Version
---------------  -------------------------  ---------
whl              azure-cli-alias-extension  0.0.1
```

## Testing and Others
With [azure-cli virtual environment](https://github.com/Azure/azure-cli/blob/master/doc/configuring_your_machine.md#preparing-your-machine) still activated, you can run tests locally by:

```bash
$ cd azure-cli-alias-extension
$ export PYTHONPATH=$(pwd)/azext_alias:${PYTHONPATH}
$ pip install -r requirements.txt
$ python test/test_alias.py
```

To run pylint:
```bash
$ pylint azext_alias/
```

## References
[Extension Authoring](https://github.com/Azure/azure-cli/blob/dev/doc/extensions/authoring.md)
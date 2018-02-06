# azure-cli-alias-extension
An Azure CLI extension that provides command alias functionality. It aims to enhance Azure CLI usuability and improve developer productivity. For detailed specificaition of this feature, please visit [here](https://gist.github.com/chewong/2afb67374d700b34015d146f63a79b15).

## Developing
1. Set up your Azure CLI development environment:
```bash
$ git clone https://github.com/chewong/azure-cli
$ cd azure-cli
$ git checkout az-alias-prototype
```
Extra code in azure-cli-core are required to incorporate the alias extension, however, it is not available in [Azure/azure-cli](https://github.com/Azure/azure-cli) yet. Therefore, you need to check out the `az-alias-prototype` branch from chewong version of `azure-cli`, configure your machine [as follow](https://github.com/Azure/azure-cli/blob/master/doc/configuring_your_machine.md#preparing-your-machine), and make sure your virtual environment is activated.

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
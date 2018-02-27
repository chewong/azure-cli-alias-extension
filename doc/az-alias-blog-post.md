# Azure CLI Alias Extension

We are very excited to announce the public preview of Azure CLI alias extension. The extension allows users to define their own custom command alias in the Azure CLI based on existing commands. The motivation behind this is to introduce a fast, concise, and customizable way to interact with the Azure CLI, simplifying workflow, as well as boosting the productivity of our customers. This blog post will go over the installation guide, notable features and examples you can try out yourself.

Please note that since the extension is in public preview, the features and the configuration file format are subject to change.

## Installing the Alias Extension
**2.0.28** is the minimum version of the Azure CLI that is compatible with the alias extension. To check the version of your CLI, simply run `az --version`. A detailed guide to updating your Azure CLI can be found [here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest).

After updating your Azure CLI to the latest version, you can run the following command to install the extension:
```
az extension add --name alias
```

To verify your installation:
```
az extension list --output table
```

The command above will output a list of installed extensions in your CLI:
```
ExtensionType    Name                       Version
---------------  -------------------------  ---------
whl              alias                      0.1.0
```

## Working with the Alias Extension
To start creating your custom aliases, you will have to first create a configuration file named `alias` (without any file extension) under the `.azure` folder. `.azure` is a hidden folder under your home directory that stores CLI-related configurations and settings. To create an empty alias configuration file, you can run the following commands depending on your operating system:

- macOS / Ubuntu / Azure Cloud Shell / Bash on Windows
```
touch $HOME/.azure/alias
```
- Windows (Command Prompt)
```
type nul > %HOMEPATH%/.azure/alias
```

All your alias definitions will be stored in the alias configuration file. The configuration file is based on the INI configuration format and has the following additional rules when defining aliases:
- The alias is surrounded by a pair of square brackets
- Each alias has a section named "command", which contains the Azure CLI commands that the alias maps to
- Each alias can contain multiple commands in the command section
- Alias and its command can contain placeholders that accept positional arguments. Placeholders are delimited by braces `{}`. Each replacement field contains a zero-based numeric index of a positional argument
- With Python 3 installed on your system, duplicated aliases or duplicated commands in a single alias are not allowed
- With Python 2 installed on your system, in case of a duplicated alias/command, the latter alias/command will take precedence
- Error parsing the alias configuration will lead to inability to use the alias feature

## Features

![Demo 1](demo-1.gif)

![Demo 2](demo-2.gif)

### Simple Aliases
The first use case of the extension is to shorten existing commands. Below is an example of the alias configuration file containing three aliases, `c`, `ac`, and `ls`, each maps to a different command.
```
[c]
command = create

[ac]
command = account

[ls]
command = list
```
After setting up your alias configuration file, you can execute the following commands for verification.
```bash
# Equivalent to 'az group create --name TestRG1 --location "South Central US"'
az group c --name TestRG1 --location "South Central US"

# Equivalent to 'az account list --output table'
az ac ls --output table
```
The first command creates a resource group named `TestRG1` in `South Central US`, whereas the second command outputs a list of subscriptions for the logged in account.

### Complex Aliases
The second use case is to compress long, redundant, and verbose commands into a single alias.
```
[create-rgrp]
command = group create --name myResourceGroup --location eastus --tags owner=$USER

[create-vm]
command = vm create --resource-group myResourceGroup --name myVM --image UbuntuLTS --generate-ssh-keys

[get-vm-ip-addr]
command = vm list-ip-addresses --resource-group myResourceGroup --name myVM --query "[0].virtualMachine.network.publicIpAddresses[0].ipAddress"
```
You can use the aliases defined above to create a resource group named `myResourceGroup` in the eastus location, create a virtual machine in `myResourceGroup` named `myVM`, and obtain the public IP address of the virtual machine using `get-vm-ip-addr`.

Note that well-defined environment variables can be referenced in the configuration file, shown in the command section of the first alias.

```bash
# Equivalent to 'az group create --name myResourceGroup --location eastus --tags owners=alice'
az create-rgrp

# Equivalent to 'az vm create --resource-group myResourceGroup --name myVM --image UbuntuLTS --generate-ssh-keys'
az create-vm

# Equivalent to 'az vm list-ip-addresses --resource-group myResourceGroup --name myVM --query "[0].virtualMachine.network.publicIpAddresses[0].ipAddress"'
az get-vm-ip-addr
```

### Positional Arguments

Last but not least, positional arguments enable you to pass in custom arguments to your aliases. For example, in your alias configuration file:

```
[create-storage-ac {0} {1}]
command = storage account create --resource-group {0} --name {1}

[create-storage-container {0}]
command = storage container create --name {0}

[upload {0} {1}]
command = storage blob upload-batch --source {0} --destination {1}
```
You can execute the following commands to create a storage account and a storage container, as well as uploading local files to a given storage container. Note that the positional arguments are spaced-delimited, meaning for each positional argument, it cannot contain any spaces, or the command might behave abnormally.
```bash
# Equivalent to 'az storage account create --resource-group myResourceGroup --name mystoragesccount'
az create-storage-ac myResourceGroup mystoragesccount

# Save the storage account name as an environment variable
# macOS / Ubuntu / Azure Cloud Shell / Bash on Windows
export AZURE_STORAGE_ACCOUNT=mystoragesccount
# Windows (cmd.exe)
set AZURE_STORAGE_ACCOUNT=mystoragesccount

# Equivalent to 'storage container create --name mycontainer'
az create-storage-container mycontainer

# Equivalent to 'storage blob upload-batch --source mylocalfolder --destination mycontainer'
az upload mylocalfolder mycontainer
```

## Removing the Alias Extension
To remove the extension, you can execute the following commands:
```
az extension remove --name alias
```

## Feedback
If you encounter any issues or have feature suggestions, they can be filed in the [issue section](https://github.com/Azure/azure-cli-extensions/issues) of the GitHub repository. In the future, more features will be implemented to improve your productivity when using Azure CLI, so stay tuned!
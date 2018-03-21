# Goals
The az alias is an extension point allows user to define their own command alias based on existing commands. The alias will enable scenarios which improve the **usability** of azure cli.
# Commands
| Command | Description |
| ----------------- | ------------------------------------------------------- |
| `az alias create` | Create an alias. Overwrite if the alias already exists. |
| `az alias list`   | list all the active aliases. |
| `az alias remove` | Remove an alias. |
## `az alias create`
Create an alias.
### Required Parameters
`--name -n`: The alias of the command.

`--command -c`: The command that the alias represents. Use quotations to group complex commands. Environment variables are allowed in the command argument.

### Examples
```bash
# Simple alias
az alias create --name mn --command monitor

# Use quotations to group complex commands
az alias create \
--name diag \
--command "diagnostic-setting create"

# Equivalent to az monitor diagnostic-setting create -h
az mn diag -h
Command
az monitor diagnostic-settings create: Create diagnostic settings for the specified resource.
Arguments
....
```
### Using Placeholders to Enable Positional Arguments
The following scripts are equivalent:
```bash
az alias create \
--name "cp {{ source_uri }} {{ dest_container }}" \
--command "storage blob copy start-batch --source-uri {{ source_uri }} --destination-container {{ dest_container }}"
az cp http://account1.blob.windows.net/source http://account2.blob.windows.net/dest
```
```bash
az storage blob copy start-batch \
--source-uri http://account1.blob.windows.net/source \
--destination-container http://account2.blob.windows.net/dest
```
### Incorporating Environment Variables
``` bash
export USER=ernest
az alias create --name "mkrgrp {{ group_name }}" --command "group create -n {{ group_name }} --tags owner=\$USER"
az mkrgrp group-name
{
    "id": "/subscriptions/00977cdb-163f-435f-9c32-39ec8ae61f4d/resourceGroups/group-name",
    "location": "southcentralus",
    "managedBy": null,
    "name": "group-name",
    "properties": {
        "provisioningState": "Succeeded"
    },
    "tags": {
        "owner": "ernest"
    }
}
```
## `az alias list`
list all the active aliases, their respective commands and descriptions.
### Example
```bash
az alias list -o table

Alias Command Description
------------------ ------------------------------------------------------------ -----------
mn monitor
diag diagnostic-setting create Create a diagnostic setting.
```
## `az alias remove`
remove an alias.
### Required Parameters
`--name -n`: The alias to be removed
### Examples
```bash
az alias list -o table

Alias              Command
------------------ ------------------------------------------------------------
mn                 monitor
diag               diagnostic-setting create

az alias remove --name mn
az alias list -o table

Alias              Command
------------------ ------------------------------------------------------------
diag               diagnostic-setting create
```

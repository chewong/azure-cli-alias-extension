# Goals
The az alias is an extension point allows user to define their own command alias based on existing commands. The alias will enable scenarios which improve the **usability** of azure cli.

# Commands
| Command | Description |
| ----------------- | ------------------------------------------------------- |
| [`az alias create`](#az-alias-create)               | Create an alias. Overwrite if the alias already exists. |
| [`az alias create-script`](#az-alias-create-script) | Create an alias that triggers an external bash script. |
| [`az alias import`](#az-alias-load)                   | Import aliases from a file. |
| [`az alias list`](#az-alias-list)                   | list all the active aliases. |
| [`az alias remove`](#az-alias-remove)               | Remove an alias. |
| [`az alias remove-batch`](#az-alias-remove-batch)   | Remove multiple aliases at the same time. |

## `az alias create`
Create an alias.

### Required Parameters
`--name -n`: The alias of the command.

`--command -c`: The command that the alias represents. Use quotations to group complex commands. Environment variables are allowed in the command argument.

### Examples
```bash
# Simple alias
$ az alias create --name mn --command monitor

# Use quotations to group complex commands
$ az alias create \
    --name diag \
    --command "diagnostic-setting create"

# Equivalent to az monitor diagnostic-setting create -h
$ az mn diag -h
Command
az monitor diagnostic-settings create: Create diagnostic settings for the specified resource.
Arguments
....
```
### Using Placeholders to Enable Positional Arguments
The following scripts are equivalent:
```bash
$ az alias create \
    --name "cp {{ source_uri }} {{ dest_container }}" \
    --command "storage blob copy start-batch --source-uri {{ source_uri }} --destination-container {{ dest_container }}"
$ az cp http://account1.blob.windows.net/source http://account2.blob.windows.net/dest
```
```bash
$ az storage blob copy start-batch \
    --source-uri http://account1.blob.windows.net/source \
    --destination-container http://account2.blob.windows.net/dest
```
### Incorporating Environment Variables
``` bash
$ az alias create --name "mkrgrp {{ group_name }}" --command "group create -n {{ group_name }} --tags owner=\$USER"
$ az mkrgrp group-name
{
    "id": "/subscriptions/xxxxxxxxxxxxxxx/resourceGroups/group-name",
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

## `az alias create-script`
Create an alias that points to a bash script.

### Required Parameters
`--name -n`: The alias of the command.

`--source -s`: The path of the bash script.

### Example
```bash
# test.sh
name=$(az vm show -g {{ resourceGroup }} -n {{ vmName }} -otsv --query 'osProfile.adminUsername')
ip=$(az vm list-ip-addresses -n {{ vmName }} --query '[0].virtualMachine.network.publicIpAddresses[0].ipAddress' -otsv)
echo "ssh $name@$ip"
ssh $name@$ip
```
```bash
$ az alias create-script --name 'ssh {{ resourceGroup }} {{ vmName }}' --source ./test.sh
$ az ssh MyResourceGroup MyVm
```


## `az alias import`
Import aliases from a file.

### Required Parameters
`--file -f`: The path of the file to load as aliases. Can be in json or ini.

### Example
```bash
$ az alias import --source ~/alias

$ az alias list -otable
Alias                         Command
----------------------------  ---------------------------------------------
list-vm {{ resource_group }}  vm list --resource-group {{ resource_group }}
grp                           group
```


## `az alias list`
list all the active aliases, their respective commands and descriptions.


## `az alias remove`
Remove an alias.

### Required Parameters
`--name -n`: The alias to be removed

### Examples
```bash
$ az alias list --output table
Alias              Command
------------------ ------------------------------------------------------------
mn                 monitor
diag               diagnostic-setting create

$ az alias remove --name mn
$ az alias list --output table

Alias              Command
------------------ ------------------------------------------------------------
diag               diagnostic-setting create
```

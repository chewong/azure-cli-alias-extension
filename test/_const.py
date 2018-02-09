# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

DEFAULT_MOCK_ALIAS_STRING = '''
[mn]
command = monitor

[diag]
command = diagnostic-settings create

[ac]
command = account

[ls]
command = list -otable

[create-grp]
command = group create -n test --tags tag1=$tag1 tag2=$tag2 tag3=$non-existing-env-var

[create-vm]
command = vm create -g test-group -n test-vm

[pos-arg-1 {0} {1}]
command = iot {0}test {1}test

[pos-arg-2]
command = ad {0} {1}

[cp {0} {1}]
command = storage blob copy start-batch --source-uri {0} --destination-container {1}

[show-ext-1 {0}]
command = extension show -n {1}

[show-ext-2 {1}]
command = extension show -n {0}

[ac-ls]
command = ac ls

[-h]
command = account
'''

COLLISION_MOCK_ALIAS_STRING = '''
[account]
command = monitor

[list-locations]
command = diagnostic-settings create

[dns]
command = network dns
'''

DUP_SECTION_MOCK_ALIAS_STRING = '''
[mn]
command = monitor

[mn]
command = account
'''

TEST_RESERVED_COMMANDS = ['account list-locations',
                          'network dns',
                          'storage account']

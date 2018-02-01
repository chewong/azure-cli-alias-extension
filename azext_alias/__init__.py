# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack import events

from azure.cli.core import AzCommandsLoader

class AliasExtensionLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azext_alias.alias import alias_event_handler

        example_custom = CliCommandType(operations_tmpl='test')

        super(AliasExtensionLoader, self).__init__(cli_ctx=cli_ctx,
                                                   min_profile='2017-03-10-profile',
                                                   custom_command_type=example_custom)

        self.cli_ctx.register_event(events.EVENT_INVOKER_POST_CMD_TBL_CREATE, alias_event_handler)

    def load_command_table(self, args):
        return {}

    def load_arguments(self, command):
        pass

COMMAND_LOADER_CLS = AliasExtensionLoader

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack import events
from knack.log import get_logger


from azure.cli.core import AzCommandsLoader

DEBUG_MSG = 'Alias Transfromer: Transformed args to %s in %.3fs'

logger = get_logger(__name__)


class AliasExtensionLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType

        example_custom = CliCommandType(operations_tmpl='test')

        super(AliasExtensionLoader, self).__init__(cli_ctx=cli_ctx,
                                                   min_profile='2017-03-10-profile',
                                                   custom_command_type=example_custom)

        self.cli_ctx.register_event(events.EVENT_INVOKER_PRE_TRUNCATE_CMD_TBL, alias_event_handler)

    def load_command_table(self, args):
        return {}

    def load_arguments(self, command):
        pass

def alias_event_handler(_, **kwargs):
    """ An event handler for alias transformation when EVENT_INVOKER_PRE_TRUNCATE_CMD_TBL event is invoked """
    import timeit
    from azext_alias.alias import AliasManager

    start_time = timeit.default_timer()
    args = kwargs.get('args')
    alias_manager = AliasManager(**kwargs)
    # [:] will keep the reference of the original args
    args[:] = alias_manager.transform(args)

    elapsed_time = timeit.default_timer() - start_time
    logger.debug(DEBUG_MSG, args, elapsed_time)


COMMAND_LOADER_CLS = AliasExtensionLoader

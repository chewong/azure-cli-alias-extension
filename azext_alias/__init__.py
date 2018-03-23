# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import timeit

from knack.log import get_logger

from azure.cli.core import AzCommandsLoader
from azure.cli.core.decorators import Completer
from azure.cli.core.commands.events import EVENT_INVOKER_PRE_CMD_TBL_TRUNCATE
from azext_alias.alias import (
    GLOBAL_ALIAS_PATH,
    AliasManager,
    get_config_parser
)
from azext_alias._const import DEBUG_MSG_WITH_TIMING
from azext_alias import telemetry
from azext_alias import _help  # pylint: disable=unused-import

logger = get_logger(__name__)
cached_reserved_commands = []


class AliasCommandLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        custom_command_type = CliCommandType(operations_tmpl='azext_alias.custom#{}')
        super(AliasCommandLoader, self).__init__(cli_ctx=cli_ctx,
                                                 custom_command_type=custom_command_type)
        self.cli_ctx.register_event(EVENT_INVOKER_PRE_CMD_TBL_TRUNCATE, alias_event_handler)

    def load_command_table(self, _):
        with self.command_group('alias') as g:
            g.custom_command('create', 'create_alias')
            g.custom_command('list', 'list_alias')
            g.custom_command('remove', 'remove_alias')

        return self.command_table

    def load_arguments(self, _):
        with self.argument_context('alias') as c:
            c.argument('alias_name', options_list=['--name', '-n'], help='The name of the alias.',
                       completer=get_alias_completer)
            c.argument('alias_command', options_list=['--command', '-c'], help='The command that the alias points to.')


@Completer
def get_alias_completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    try:
        alias_table = get_config_parser()
        alias_table.read(GLOBAL_ALIAS_PATH)
        return alias_table.sections()
    except Exception:  # pylint: disable=broad-except
        return []


def alias_event_handler(_, **kwargs):
    """
    An event handler for alias transformation when EVENT_INVOKER_PRE_TRUNCATE_CMD_TBL event is invoked
    """
    try:
        telemetry.start()

        start_time = timeit.default_timer()
        args = kwargs.get('args')
        alias_manager = AliasManager(**kwargs)

        # [:] will keep the reference of the original args
        args[:] = alias_manager.transform(args)

        # Cache the reserved commands for validation later
        if args[:2] == ['alias', 'create']:
            load_cmd_tbl_func = kwargs.get('load_cmd_tbl_func', lambda _: {})
            global cached_reserved_commands  # pylint: disable=global-statement
            cached_reserved_commands = alias_manager.reserved_commands if alias_manager.reserved_commands \
                                                                       else load_cmd_tbl_func([]).keys()

        elapsed_time = (timeit.default_timer() - start_time) * 1000
        logger.debug(DEBUG_MSG_WITH_TIMING, args, elapsed_time)

        telemetry.set_execution_time(round(elapsed_time, 2))
    except Exception as client_exception:  # pylint: disable=broad-except
        telemetry.set_exception(client_exception)
        raise
    finally:
        telemetry.conclude()


COMMAND_LOADER_CLS = AliasCommandLoader

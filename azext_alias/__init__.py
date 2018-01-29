# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re

from knack.log import get_logger
from knack.util import CLIError

from azure.cli.core._environment import get_config_dir

GLOBAL_CONFIG_DIR = get_config_dir()
ALIAS_FILE_NAME = 'alias'
GLOBAL_ALIAS_PATH = os.path.join(GLOBAL_CONFIG_DIR, ALIAS_FILE_NAME)

PLACEHOLDER_REGEX = r'\s*{\d+}'
PLACEHOLDER_SPLIT_REGEX = r'\s*{\d+\.split\(((\'.*\')|(".*"))\)\[\d+\]}'
ENV_VAR_REGEX = r'\$[a-zA-Z][a-zA-Z0-9]*'
QUOTES_REGEX = r'^[\'|\"]|[\'|\"]$'

COLLISION_WARNING = '\'%s\' is currently mapped to \'%s\' in alias configuration.'
INCONSISTENT_INDEXING_ERROR = 'Inconsistent placeholder indexing in alias command.'
RECURSIVE_ALIAS_ERROR = 'Potentially recursive alias: \'{}\' is associated by another alias'
DEBUG_MSG = 'Alias Transfromer: Took %.3f seconds to transform %s to %s'

logger = get_logger(__name__)


class AliasManager:

    def __init__(self, **kwargs):
        from six.moves import configparser

        self.alias_table = configparser.ConfigParser()
        try:
            if not os.path.exists(GLOBAL_ALIAS_PATH):
                with open(GLOBAL_ALIAS_PATH, 'w') as alias_config_file:
                    self.alias_table.write(alias_config_file)

            self.alias_table.read(GLOBAL_ALIAS_PATH)
        except configparser.DuplicateSectionError:
            pass

        self.kwargs = kwargs
        self.reserved_commands = self.kwargs.get('reserved_commands', [])
        self.collision_regex = r'^'
        self.bypass_recursive_check_cmd = set()

    def transform(self, args):
        """ Transform any aliases in args to their respective commands """
        import timeit

        start_time = timeit.default_timer()
        transformed_commands = []
        alias_iter = enumerate(args, 1)

        for alias_index, alias in alias_iter:
            full_alias = self.get_full_alias(alias)
            num_pos_args = AliasManager.count_positional_args(full_alias)
            if full_alias in self.alias_table:
                cmd_derived_from_alias = self.alias_table[full_alias].get('command', alias)
            else:
                cmd_derived_from_alias = alias

            # If we have an alias collision, DO NOT transform it and simply append it to transformed_commands
            if alias[0] != '-' and self.is_collided(alias):
                transformed_commands.append(alias)
                if alias != cmd_derived_from_alias:
                    logger.warning(COLLISION_WARNING, alias, cmd_derived_from_alias)
                continue

            if not num_pos_args and alias != cmd_derived_from_alias:
                # Truncate the list of reserved commands based on the command derived from alias
                self.collision_regex = self.collision_regex.replace(alias.lower(), cmd_derived_from_alias.lower())
                self.reserved_commands = self.get_truncated_reserved_commands()
            elif num_pos_args:
                # Take arguments indexed from i to i + num_pos_args and inject
                # them as positional arguments into the command
                pos_args_iter = AliasManager.pos_args_iter(args, alias_index, num_pos_args)
                for placeholder, pos_arg in pos_args_iter:
                    if placeholder not in cmd_derived_from_alias:
                        raise CLIError(INCONSISTENT_INDEXING_ERROR)
                    cmd_derived_from_alias = cmd_derived_from_alias.replace(placeholder, pos_arg)
                    #
                    self.bypass_recursive_check_cmd.add(pos_arg)
                    # Skip the next arg because it has been already consumed as a positional argument above
                    next(alias_iter)
            else:  # alias == cmd_derived_from_alias
                # DO NOT perform anything if the alias is not registered in the alias config file
                pass

            # Invoke split() because the command derived from the alias might contain spaces
            transformed_commands += cmd_derived_from_alias.split()

        transformed_commands = AliasManager.post_transform(transformed_commands)

        if transformed_commands != args:
            self.check_recursive_alias(transformed_commands)

        elapsed_time = timeit.default_timer() - start_time
        logger.debug(DEBUG_MSG, elapsed_time, args, transformed_commands)

        return transformed_commands

    def is_collided(self, alias):
        """
        Check if a given alias collides with a reserved command.
        Return True if there is a collision.
        Collision in this context is defined as an alias containing the exact same characters as a
        reserved command in the same level. For example:
        level 0 | level 1 | level 2 | ...
            az       vm      create   ...
        If a user defined an alias [vm]->[account list], and typed 'az vm', there is a collision because 'vm' in
        'az vm' is in level 1 and 'vm' itself is a level-1-reserved word. However, if the alias is [vm]->[list],
        'az account vm' would translate to 'az account list' because vm is not a level-2-reserved word.
        However, we do not encourage customers to define alias that contains reserved words

        self.collision_regex is an regex that we keep building throughout transform(), which checks for
        collision. Simply append alias to self.collision_regex and check if there are commands in
        self.reserved_words that prefix with self.collision_regex. If the result set is empty, we can conclude
        that there is no collision occurred (for now).
        """
        self.collision_regex += r'{}($|\s)'.format(alias.lower())
        collided = self.get_truncated_reserved_commands()

        if collided:
            self.bypass_recursive_check_cmd.add(alias)
            self.reserved_commands = collided
            return True
        return False

    def get_full_alias(self, query):
        """ Return the full alias (with the placeholders, if any) given a search query """
        if query in self.alias_table:
            return query
        return next((section for section in self.alias_table.sections() if section.split()[0] == query), '')

    def check_recursive_alias(self, commands):
        """ Check for any recursive alias """
        for subcommand in commands:
            if subcommand not in self.bypass_recursive_check_cmd and self.get_full_alias(subcommand):
                raise CLIError(RECURSIVE_ALIAS_ERROR.format(subcommand))

    def get_truncated_reserved_commands(self):
        """ List all the reserved commands where their prefix is the same as the current collision regex """
        return list(filter(re.compile(self.collision_regex).match, self.reserved_commands))

    @staticmethod
    def count_positional_args(arg):
        """ Count how many positional arguments ({0}, {1} ...) there are. """
        return len(re.findall(PLACEHOLDER_REGEX, arg))

    @staticmethod
    def pos_args_iter(args, start_index, num_pos_args):
        """
        Generate an tuple iterator ([0], [1]) where the [0] is the positional argument
        placeholder and [1] is the argument value. e.g. ('{0}', pos_arg_1) -> ('{1}', pos_arg_2) -> ...
        """
        pos_args = args[start_index: start_index + num_pos_args]
        if len(pos_args) != num_pos_args:
            raise CLIError(INCONSISTENT_INDEXING_ERROR)

        for i, pos_arg in enumerate(pos_args):
            yield ('{{{}}}'.format(i), pos_arg)

    @staticmethod
    def post_transform(args):
        """
        Inject environment variables and remove leading and trailing quotes
        after transforming alias to commands
        """
        def inject_env_vars(arg):
            """ Inject environment variables into the commands """
            env_vars = re.findall(ENV_VAR_REGEX, arg)
            for env_var in env_vars:
                arg = arg.replace(env_var, os.path.expandvars(env_var))
            return arg

        post_transform_commands = []
        for arg in args:
            # JMESPath queries are surrounded by a pair of quotes,
            # need to get rid of them before passing args to argparse
            arg = re.sub(QUOTES_REGEX, '', arg)
            post_transform_commands.append(inject_env_vars(arg))

        return post_transform_commands

ARG_EXT_CLS = AliasManager

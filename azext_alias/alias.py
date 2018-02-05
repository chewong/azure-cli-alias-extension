# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re
import hashlib

from knack.log import get_logger
from knack.util import CLIError
from configparser import ConfigParser

from azure.cli.core._environment import get_config_dir
from azext_alias._const import (
    GLOBAL_CONFIG_DIR,
    ALIAS_FILE_NAME,
    ALIAS_HASH_FILE_NAME,
    PLACEHOLDER_REGEX,
    ENV_VAR_REGEX,
    QUOTES_REGEX,
    COLLISION_WARNING,
    INCONSISTENT_INDEXING_ERROR,
    RECURSIVE_ALIAS_ERROR,
    PARSE_ERROR,
    IGNORE_CONFIG_MSG)

GLOBAL_ALIAS_PATH = os.path.join(GLOBAL_CONFIG_DIR, ALIAS_FILE_NAME)
GLOBAL_ALIAS_HASH_PATH = os.path.join(GLOBAL_CONFIG_DIR, ALIAS_HASH_FILE_NAME)

logger = get_logger(__name__)


class AliasManager(object):

    def __init__(self, **kwargs):
        self.alias_table = ConfigParser()
        self.kwargs = kwargs
        self.bypass_recursive_check_cmd = set()
        self.collided_alias = set()
        self.reserved_commands = []
        self.alias_config_str = ''
        self.alias_config_hash = ''

        self.load_alias_table()
        self.load_alias_hash()

    def load_alias_table(self):
        """ Load (create, if not exist) the alias config file """
        try:
            # w+ creates the alias config file if it does not exist
            open_mode = 'r+' if os.path.exists(GLOBAL_ALIAS_PATH) else 'w+'
            with open(GLOBAL_ALIAS_PATH, open_mode) as alias_config_file:
                self.alias_config_str = alias_config_file.read()
            self.alias_table.read(GLOBAL_ALIAS_PATH)
        except Exception:  # pylint: disable=broad-except
            self.alias_table = ConfigParser()

    def load_alias_hash(self):
        """ Load (create, if not exist) the alias hash file """
        # w+ creates the alias hash file if it does not exist
        open_mode = 'r+' if os.path.exists(GLOBAL_ALIAS_HASH_PATH) else 'w+'
        with open(GLOBAL_ALIAS_HASH_PATH, open_mode) as alias_config_hash_file:
            self.alias_config_hash = alias_config_hash_file.read()

    def detect_alias_config_change(self):
        """
        Return False if the alias configuration file has not been changed since the last run.
        Otherwise, return True.
        """
        # Do not load the entire command table if there is a parse error
        if self.parse_error():
            return False

        alias_config_sha1 = hashlib.sha1(self.alias_config_str.encode('utf-8')).hexdigest()
        # Overwrite the old hash with the new one
        if alias_config_sha1 != self.alias_config_hash:
            self.alias_config_hash = alias_config_sha1
            return True
        return False

    def transform(self, args):
        # Only load the entire command table if it detects changes in the alias config
        if self.detect_alias_config_change():
            self.load_full_command_table()
            self.build_collision_table()

        """ Transform any aliases in args to their respective commands """
        # If we have an alias collision or parse error,
        # do not perform anything and simply return the original input args
        if self.collided_alias or self.parse_error():
            logger.warning(COLLISION_WARNING.format(self.collided_alias) if self.collided_alias else PARSE_ERROR)
            logger.warning(IGNORE_CONFIG_MSG)

            # Write an empty hash so next run will check the config file against the entire command table again
            self.write_alias_config_hash(True)
            return args

        transformed_commands = []
        alias_iter = enumerate(args, 1)

        for alias_index, alias in alias_iter:
            full_alias = self.get_full_alias(alias)
            num_pos_args = AliasManager.count_positional_args(full_alias)

            if self.alias_table.has_option(full_alias, 'command'):
                cmd_derived_from_alias = self.alias_table.get(full_alias, 'command')
            else:
                cmd_derived_from_alias = alias

            if num_pos_args:
                # Take arguments indexed from i to i + num_pos_args and inject
                # them as positional arguments into the command
                pos_args_iter = AliasManager.pos_args_iter(args, alias_index, num_pos_args)
                for placeholder, pos_arg in pos_args_iter:
                    if placeholder not in cmd_derived_from_alias or placeholder not in full_alias:
                        raise CLIError(INCONSISTENT_INDEXING_ERROR)
                    cmd_derived_from_alias = cmd_derived_from_alias.replace(placeholder, pos_arg)

                    self.bypass_recursive_check_cmd.add(pos_arg)
                    # Skip the next arg because it has been already consumed as a positional argument above
                    next(alias_iter)
            else:  # alias == cmd_derived_from_alias
                # DO NOT perform anything if the alias is not registered in the alias config file
                pass

            # Invoke split() because the command derived from the alias might contain spaces
            transformed_commands += cmd_derived_from_alias.split()

        transformed_commands = self.post_transform(transformed_commands)

        if transformed_commands != args:
            self.check_recursive_alias(transformed_commands)

        return transformed_commands

    def build_collision_table(self):
        """
        Check every word in each alias, check, and build if the word collided with a reserved command.
        If there is a collision, the word will be appended to self.collided_alias
        """
        for alias in self.alias_table.sections():
            self.check_collision(alias.split()[0])

    def check_collision(self, word):
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
        collision_regex = r'.*(^|\s){}($|\s).*'.format(word.lower())
        collided = self.get_truncated_reserved_commands(collision_regex)

        if collided:
            self.collided_alias.add(word)

    def get_full_alias(self, query):
        """ Return the full alias (with the placeholders, if any) given a search query """
        if query in self.alias_table.sections():
            return query
        return next((section for section in self.alias_table.sections() if section.split()[0] == query), '')

    def check_recursive_alias(self, commands):
        """ Check for any recursive alias """
        for subcommand in commands:
            if subcommand not in self.bypass_recursive_check_cmd and self.get_full_alias(subcommand):
                raise CLIError(RECURSIVE_ALIAS_ERROR.format(subcommand))

    def get_truncated_reserved_commands(self, collision_regex):
        """ List all the reserved commands where their prefix is the same as the current collision regex """
        return list(filter(re.compile(collision_regex).match, self.reserved_commands))

    def load_full_command_table(self):
        """ Perform a full load of the command table to get all the reserved command words """
        load_cmd_tbl_func = self.kwargs.get('load_cmd_tbl_func', None)
        if load_cmd_tbl_func:
            self.reserved_commands = list(load_cmd_tbl_func([]).keys())

    def post_transform(self, args):
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

        self.write_alias_config_hash()

        return post_transform_commands

    def write_alias_config_hash(self, empty_hash=False):
        """
        Write self.alias_config_hash to the alias hash file.
        An empty hash means that we need to validate the hash file in the next run
        """
        with open(GLOBAL_ALIAS_HASH_PATH, 'w') as alias_config_hash_file:
            alias_config_hash_file.write('' if empty_hash else self.alias_config_hash)

    def parse_error(self):
        """
        There is a parse error if there are strings inside the alias
        config file but there is no alias loaded in self.alias_table
        """
        return not self.alias_table.sections() and self.alias_config_str

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
    def count_positional_args(arg):
        """ Count how many positional arguments ({0}, {1} ...) there are. """
        return len(re.findall(PLACEHOLDER_REGEX, arg))

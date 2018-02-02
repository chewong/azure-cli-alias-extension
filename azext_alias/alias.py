# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re

from knack.log import get_logger
from knack.util import CLIError
from six.moves.configparser import ConfigParser, DuplicateSectionError, NoSectionError, NoOptionError, DuplicateOptionError
import hashlib

from azure.cli.core._environment import get_config_dir

GLOBAL_CONFIG_DIR = get_config_dir()
ALIAS_FILE_NAME = 'alias'
ALIAS_HASH_FILE_NAME = 'alias.sha1'
GLOBAL_ALIAS_PATH = os.path.join(GLOBAL_CONFIG_DIR, ALIAS_FILE_NAME)
GLOBAL_ALIAS_HASH_PATH = os.path.join(GLOBAL_CONFIG_DIR, ALIAS_HASH_FILE_NAME)

PLACEHOLDER_REGEX = r'\s*{\d+}'
PLACEHOLDER_SPLIT_REGEX = r'\s*{\d+\.split\(((\'.*\')|(".*"))\)\[\d+\]}'
ENV_VAR_REGEX = r'\$[a-zA-Z][a-zA-Z0-9_]*'
QUOTES_REGEX = r'^[\'|\"]|[\'|\"]$'

COLLISION_WARNING = '\'%s\' is a reserved command in the CLI, but is currently mapped to \'%s\' in alias configuration'
INCONSISTENT_INDEXING_ERROR = 'Inconsistent placeholder indexing in alias command'
RECURSIVE_ALIAS_ERROR = 'Potentially recursive alias: \'{}\' is associated by another alias'
READ_ERROR_MSG = 'Unable to read section %s, and/or its command'
DUP_SECTION_ERROR = 'Ignoring alias config file because it seems like there are duplicated alias in your configuration file'

# Config Status Enum
CONFIG_VALID = '0'
# Inability to read the config file, not errors such as recursive alias and inconsistent placeholder
CONFIG_INVALID = '1'
CONFIG_NEED_VALIDATION = '2'
CONFIG_COLLIDED = '3'

logger = get_logger(__name__)


class AliasManager(object):

    def __init__(self, **kwargs):
        self.alias_table = ConfigParser()
        self.kwargs = kwargs
        self.collision_regex = r'^'
        self.bypass_recursive_check_cmd = set()
        self.collided_alias = set()
        self.reserved_commands = []
        self.load_alias_table()

        # Only load the entire command table if it detects changes in the alias config
        # (CONFIG_NEED_VALIDATION) or it previously had collided aliases (CONFIG_COLLIDED)
        alias_config_status = self.detect_alias_config_change()
        if alias_config_status == CONFIG_NEED_VALIDATION:
            self.load_full_command_table()
            self.build_collision_table()

    def load_alias_table(self):
        try:
            if not os.path.exists(GLOBAL_ALIAS_PATH):
                open(GLOBAL_ALIAS_PATH, 'w').close()
            if not os.path.exists(GLOBAL_ALIAS_HASH_PATH):
                self.create_alias_sha1()
            self.alias_table.read(GLOBAL_ALIAS_PATH)
        except (DuplicateSectionError, DuplicateOptionError):
            logger.warning(DUP_SECTION_ERROR)
            self.append_config_status_to_hash(CONFIG_INVALID)
            self.alias_table.read_string('')

    def create_alias_sha1(self):
        with open(GLOBAL_ALIAS_PATH, 'r') as alias_config_file, open(GLOBAL_ALIAS_HASH_PATH, 'w+') as alias_hash_file:
            alias_config_str = alias_config_file.read().encode('utf-8')
            alias_config_sha1 = hashlib.sha1(alias_config_str).hexdigest()
            alias_hash_file.write(alias_config_sha1)
            self.append_config_status_to_hash(CONFIG_NEED_VALIDATION)

    def detect_alias_config_change(self):
        """
        Return False if the alias configuration file has not been changed since the last run.
        Otherwise, return True.
        alias.sha1 format: <40 digits long hash in hex><1 digit config status>
        """
        with open(GLOBAL_ALIAS_PATH, 'r') as alias_config_file, open(GLOBAL_ALIAS_HASH_PATH, 'r+') as alias_hash_file:
            alias_config_str = alias_config_file.read().encode('utf-8')
            alias_config_sha1 = hashlib.sha1(alias_config_str).hexdigest()
            previous_hash = alias_hash_file.read()

            if previous_hash[40] == CONFIG_INVALID:
                return CONFIG_INVALID
            elif alias_config_sha1 == previous_hash[:40]:
                if previous_hash[40] == CONFIG_COLLIDED:
                     self.build_collision_table(previous_hash[42:])
                return previous_hash[40]
            else:
                alias_hash_file.seek(0)
                alias_hash_file.truncate()
                alias_hash_file.write(alias_config_sha1)
                return CONFIG_NEED_VALIDATION

    def transform(self, args):
        """ Transform any aliases in args to their respective commands """
        transformed_commands = []
        alias_iter = enumerate(args, 1)

        for alias_index, alias in alias_iter:
            full_alias = self.get_full_alias(alias)
            num_pos_args = AliasManager.count_positional_args(full_alias)

            if self.alias_table.has_option(full_alias, 'command'):
                cmd_derived_from_alias = self.alias_table.get(full_alias, 'command')
            else:
                cmd_derived_from_alias = alias

            # If we have an alias collision, DO NOT transform it and simply append it to transformed_commands
            if alias in self.collided_alias:
                transformed_commands.append(alias)
                logger.warning(COLLISION_WARNING, alias, cmd_derived_from_alias)
                continue

            if num_pos_args:
                # Take arguments indexed from i to i + num_pos_args and inject
                # them as positional arguments into the command
                pos_args_iter = self.pos_args_iter(args, alias_index, num_pos_args)
                for placeholder, pos_arg in pos_args_iter:
                    if placeholder not in cmd_derived_from_alias:
                        self.error(CONFIG_VALID, INCONSISTENT_INDEXING_ERROR)
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

    def build_collision_table(self, collision_str=''):
        if collision_str:
            for s in collision_str.split(','):
                self.collided_alias.add(s)
        else:
            for alias in self.alias_table.sections():
                self.collision_regex = r'^'
                for word in alias.split():
                    self.check_collision(word)

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
        self.collision_regex += r'{}($|\s)'.format(word.lower())
        collided = self.get_truncated_reserved_commands()

        if collided:
            self.collided_alias.add(word)
        return bool(collided)

    def get_full_alias(self, query):
        """ Return the full alias (with the placeholders, if any) given a search query """
        if query in self.alias_table.sections():
            return query
        return next((section for section in self.alias_table.sections() if section.split()[0] == query), '')

    def check_recursive_alias(self, commands):
        """ Check for any recursive alias """
        for subcommand in commands:
            if subcommand not in self.bypass_recursive_check_cmd and self.get_full_alias(subcommand):
                self.error(CONFIG_VALID, RECURSIVE_ALIAS_ERROR.format(subcommand))

    def get_truncated_reserved_commands(self):
        """ List all the reserved commands where their prefix is the same as the current collision regex """
        return list(filter(re.compile(self.collision_regex).match, self.reserved_commands))

    def load_full_command_table(self):
        """ Perform a full load of the command table to get all the reserved command words """
        load_cmd_tbl_func = self.kwargs.get('load_cmd_tbl_func', None)
        if load_cmd_tbl_func:
            self.reserved_commands = load_cmd_tbl_func([])

    def append_config_status_to_hash(self, config_status=None):
        with open(GLOBAL_ALIAS_HASH_PATH, 'r+') as alias_hash_file:
            # Start writing right after the 40-digit hash
            alias_hash_file.seek(40)
            alias_hash_file.truncate()

            if config_status:
                alias_hash_file.write(config_status)
            elif self.collided_alias:
                alias_hash_file.write(CONFIG_COLLIDED)
                alias_hash_file.write('\n{}'.format(','.join(self.collided_alias)))
            else:
                alias_hash_file.write(CONFIG_VALID)

    def error(self, config_status, error_str):
        self.append_config_status_to_hash(config_status)
        raise CLIError(error_str)

    def pos_args_iter(self, args, start_index, num_pos_args):
        """
        Generate an tuple iterator ([0], [1]) where the [0] is the positional argument
        placeholder and [1] is the argument value. e.g. ('{0}', pos_arg_1) -> ('{1}', pos_arg_2) -> ...
        """
        pos_args = args[start_index: start_index + num_pos_args]
        if len(pos_args) != num_pos_args:
            self.error(CONFIG_VALID, INCONSISTENT_INDEXING_ERROR)

        for i, pos_arg in enumerate(pos_args):
            yield ('{{{}}}'.format(i), pos_arg)

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

        self.append_config_status_to_hash()

        return post_transform_commands

    @staticmethod
    def count_positional_args(arg):
        """ Count how many positional arguments ({0}, {1} ...) there are. """
        return len(re.findall(PLACEHOLDER_REGEX, arg))
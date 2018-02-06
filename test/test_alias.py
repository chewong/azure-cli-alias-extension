# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from knack.util import CLIError
from ddt import ddt, data

from azext_alias import alias
from azext_alias._const import GLOBAL_CONFIG_DIR
from _const import (DEFAULT_MOCK_ALIAS_STRING,
                    COLLISION_MOCK_ALIAS_STRING,
                    TEST_RESERVED_COMMANDS,
                    DUP_SECTION_MOCK_ALIAS_STRING)

@ddt
class TestAlias(unittest.TestCase):

    @data(('ac', 'account'),
          ('ls', 'list -otable'),
          ('ac ls', 'account list -otable'),
          ('mn diag', 'monitor diagnostic-settings create'),
          ('create-vm', 'vm create -g test-group -n test-vm'))
    def test_transform_simple_alias(self, value):
        alias_args, expected_args = value
        self.assertAlias(expected_args, alias_args)

    @data(('ac set -s test', 'account set -s test'),
          ('vm ls -g test -otable', 'vm list -otable -g test -otable'))
    def test_transform_alias_with_extra_args(self, value):
        alias_args, expected_args = value
        self.assertAlias(expected_args, alias_args)

    @data(('cp test1 test2', 'storage blob copy start-batch --source-uri test1 --destination-container test2'))
    def test_transform_pos_arg(self, value):
        alias_args, expected_args = value
        self.assertAlias(expected_args, alias_args)

    @data(('cp test1 test2 -o tsv', 'storage blob copy start-batch --source-uri test1 --destination-container test2 -o tsv'),
          ('create-vm --image ubtuntults --generate-ssh-key --no-wait', 'vm create -g test-group -n test-vm --image ubtuntults --generate-ssh-key --no-wait'))
    def test_transform_pos_arg_with_extra_args(self, value):
        alias_args, expected_args = value
        self.assertAlias(expected_args, alias_args)

    @data(('cp mn diag', 'storage blob copy start-batch --source-uri mn --destination-container diag'))
    def test_transform_pos_arg_with_alias(self, value):
        # Placeholders are aliases in this case
        # Expected alias_manager not to transform mn and diag, even though they are alias,
        # because they are positional argument in this use case
        alias_args, expected_args = value
        self.assertAlias(expected_args, alias_args)

    @data(('group create -n test --tags tag1=$tag1 tag2=$tag2 tag3=$non-existing-env-var', 'group create -n test --tags tag1=test-env-var-1 tag2=test-env-var-2 tag3=$non-existing-env-var'))
    def test_post_transform_env_var(self, value):
        os.environ['tag1'] = 'test-env-var-1'
        os.environ['tag2'] = 'test-env-var-2'
        alias_args, expected_args = value
        self.assertPostTransform(expected_args, alias_args)

    @data(('vm list -g MyResourceGroup --query "[].id" -o tsv', 'vm list -g MyResourceGroup --query [].id -o tsv'),
          ('vm list -g MyResourceGroup --query \'[].id\' -o tsv', 'vm list -g MyResourceGroup --query [].id -o tsv'))
    def test_post_transform_remove_quotes(self, value):
        alias_args, expected_args = value
        self.assertPostTransform(expected_args, alias_args)

    def test_recursive_alias(self):
        alias_manager = self.get_alias_manager()
        with self.assertRaises(CLIError):
            alias_manager.transform(['ac-ls'])

    @data(['cp'], ['show-ext-1', 'test-ext'], ['show-ext-2', 'test-ext'])
    def test_inconsistent_placeholder_index(self, value):
        alias_manager = self.get_alias_manager()
        # Raise error if there is not enough positional argument provided
        with self.assertRaises(CLIError):
            alias_manager.transform(value)

    def test_build_collision_table(self):
        alias_manager = self.get_alias_manager(DEFAULT_MOCK_ALIAS_STRING, TEST_RESERVED_COMMANDS)
        self.assertSetEqual(set(), alias_manager.collided_alias)

        alias_manager = self.get_alias_manager(COLLISION_MOCK_ALIAS_STRING, TEST_RESERVED_COMMANDS)
        alias_manager.build_collision_table()
        self.assertSetEqual(set(['account', 'list-locations', 'dns', 'storage']), alias_manager.collided_alias)

    def test_parse_error(self):
        alias_manager = self.get_alias_manager()
        self.assertFalse(alias_manager.parse_error())

        alias_manager = self.get_alias_manager(DUP_SECTION_MOCK_ALIAS_STRING)
        self.assertTrue(alias_manager.parse_error())

        alias_manager = self.get_alias_manager('Malformed alias config file string')
        self.assertTrue(alias_manager.parse_error())

    def test_detect_alias_config_change(self):
        alias_manager = self.get_alias_manager()
        alias.alias_config_str = DEFAULT_MOCK_ALIAS_STRING
        self.assertFalse(alias_manager.detect_alias_config_change())

        alias_manager = self.get_alias_manager()
        # Load a new alias file (an empty string in this case)
        alias_manager.alias_config_str = ''
        self.assertTrue(alias_manager.detect_alias_config_change())

    ##########################
    #### Helper functions ####
    ##########################
    def get_alias_manager(self, mock_alias_str=DEFAULT_MOCK_ALIAS_STRING, reserved_commands=None):
        alias_manager = MockAliasManager(mock_alias_str=mock_alias_str)
        alias_manager.reserved_commands = reserved_commands if reserved_commands else []
        return alias_manager

    def assertAlias(self, expected_args, alias_args):
        """ Assert the alias with the default alias config file """
        alias_manager = self.get_alias_manager()
        self.assertEqual(expected_args.split(), alias_manager.transform(alias_args.split()))

    def assertPostTransform(self, expected_args, alias_args, mock_alias_str=DEFAULT_MOCK_ALIAS_STRING):
        alias_manager = self.get_alias_manager(mock_alias_str=mock_alias_str)
        self.assertEqual(expected_args.split(), alias_manager.post_transform(alias_args.split()))


class MockAliasManager(alias.AliasManager):

    def load_alias_table(self):
        from configparser import ConfigParser

        self.alias_config_str = self.kwargs.get('mock_alias_str', '')
        try:
            try:
                # Python 2 implementation
                from StringIO import StringIO
                self.alias_table.readfp(StringIO(self.alias_config_str))
            except ModuleNotFoundError:
                # Python 3 implementation
                self.alias_table = ConfigParser()
                self.alias_table.read_string(self.alias_config_str)
        except Exception:  # pylint: disable=broad-except
            self.alias_table = ConfigParser()

    def load_alias_hash(self):
        import hashlib
        self.alias_config_hash = hashlib.sha1(self.alias_config_str.encode('utf-8')).hexdigest()

    def write_alias_config_hash(self, empty_hash=False):
        pass

if __name__ == '__main__':
    unittest.main()

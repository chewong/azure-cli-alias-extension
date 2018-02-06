# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from knack.util import CLIError

from azext_alias import alias
from azext_alias._const import GLOBAL_CONFIG_DIR
from _const import (DEFAULT_MOCK_ALIAS_STRING,
                    COLLISION_MOCK_ALIAS_STRING,
                    TEST_RESERVED_COMMANDS,
                    DUP_SECTION_MOCK_ALIAS_STRING)

class TestAlias(unittest.TestCase):

    def test_transform_simple_alias(self):
        alias_args = 'ac'
        expected_args = 'account'
        self.assertAlias(expected_args, alias_args)

        alias_args = 'ls'
        expected_args = 'list -otable'
        self.assertAlias(expected_args, alias_args)

        alias_args = 'ac ls'
        expected_args = 'account list -otable'
        self.assertAlias(expected_args, alias_args)

        alias_args = 'mn diag'
        expected_args = 'monitor diagnostic-settings create'
        self.assertAlias(expected_args, alias_args)

    def test_transform_alias_with_extra_args(self):
        alias_args = 'ac set -s test'
        expected_args = 'account set -s test'
        self.assertAlias(expected_args, alias_args)

    def test_transform_pos_arg(self):
        alias_args = 'cp test1 test2'
        expected_args = 'storage blob copy start-batch --source-uri test1 --destination-container test2'
        self.assertAlias(expected_args, alias_args)

    def test_transform_pos_arg_with_extra_args(self):
        alias_args = 'cp test1 test2 -o tsv'
        expected_args = 'storage blob copy start-batch --source-uri test1 --destination-container test2 -o tsv'
        self.assertAlias(expected_args, alias_args)

        alias_args = 'create-vm --image ubtuntults --generate-ssh-key --no-wait'
        expected_args = 'vm create -g test-group -n test-vm --image ubtuntults --generate-ssh-key --no-wait'
        self.assertAlias(expected_args, alias_args)

    def test_transform_pos_arg_with_alias(self):
        # Placeholders are aliases in this case
        alias_args = 'cp mn diag'
        # Expected alias_manager not to transform mn and diag, even though they are alias,
        # because they are positional argument in this use case
        expected_args = 'storage blob copy start-batch --source-uri mn --destination-container diag'
        self.assertAlias(expected_args, alias_args)

    def test_post_transform_env_var(self):
        os.environ['tag1'] = 'test-env-var-1'
        os.environ['tag2'] = 'test-env-var-2'
        alias_args = 'group create -n test --tags tag1=$tag1 tag2=$tag2 tag3=$non-existing-env-var'
        expected_args = 'group create -n test --tags tag1=test-env-var-1 tag2=test-env-var-2 tag3=$non-existing-env-var'
        self.assertPostTransform(expected_args, alias_args)

    def test_post_transform_remove_quotes(self):
        alias_args = 'vm list -g MyResourceGroup --query "[].id" -o tsv'
        expected_args = 'vm list -g MyResourceGroup --query [].id -o tsv'
        self.assertPostTransform(expected_args, alias_args)

        alias_args = 'vm list -g MyResourceGroup --query \'[].id\' -o tsv'
        expected_args = 'vm list -g MyResourceGroup --query [].id -o tsv'
        self.assertPostTransform(expected_args, alias_args)

    def test_recursive_alias(self):
        alias_manager = self.get_alias_manager()
        with self.assertRaises(CLIError):
            alias_manager.transform(['ac-ls'])

    def test_inconsistent_placeholder_index(self):
        alias_manager = self.get_alias_manager()
        # Raise error if there is not enough positional argument provided
        with self.assertRaises(CLIError):
            alias_manager.transform(['cp'])

        # Raise error if the placeholder indexing in the alias config file is inconsistent
        with self.assertRaises(CLIError):
            alias_manager.transform(['show-ext-1', 'test-ext'])
        with self.assertRaises(CLIError):
            alias_manager.transform(['show-ext-2', 'test-ext'])

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

        # Load a new alias file (an empty string in this case)
        alias_manager = self.get_alias_manager()
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

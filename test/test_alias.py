import os
import unittest

from knack.util import CLIError

from azext_alias import alias
from azext_alias._const import GLOBAL_CONFIG_DIR

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

[cp {0} {1}]
command = storage blob copy start-batch --source-uri {0} --destination-container {1}

[show-ext {0}]
command = extension show -n {1}

[dns]
command = network dns

[ac-ls]
command = ac ls
'''

class TestAlias(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        alias.GLOBAL_ALIAS_PATH = os.path.join(GLOBAL_CONFIG_DIR, 'test_alias')
        alias.GLOBAL_ALIAS_HASH_PATH = os.path.join(GLOBAL_CONFIG_DIR, 'test_alias.sha1')

    @classmethod
    def tearDownClass(self):
        # Remove test files
        os.remove(alias.GLOBAL_ALIAS_PATH)
        os.remove(alias.GLOBAL_ALIAS_HASH_PATH)

    def test_transform_simple_alias(self):
        alias_args = ['ac', 'ls']
        expected_args = ['account', 'list', '-otable']
        self.assertAlias(expected_args, alias_args)

        alias_args = ['mn', 'diag']
        expected_args = ['monitor', 'diagnostic-settings', 'create']
        self.assertAlias(expected_args, alias_args)

    def test_transform_simple_alias_with_extra_args(self):
        alias_args = ['ac', 'set', '-s', 'test']
        expected_args = ['account', 'set', '-s', 'test']
        self.assertAlias(expected_args, alias_args)

        alias_args = ['create-vm', '--image', 'ubtuntults', '--generate-ssh-key', '--no-wait']
        expected_args = ['vm', 'create', '-g', 'test-group', '-n',
                         'test-vm', '--image', 'ubtuntults', '--generate-ssh-key', '--no-wait']
        self.assertAlias(expected_args, alias_args)

    def test_transform_pos_arg(self):
        alias_args = ['cp', 'test1', 'test2']
        expected_args = ['storage', 'blob', 'copy', 'start-batch', '--source-uri',
                         'test1', '--destination-container', 'test2']
        self.assertAlias(expected_args, alias_args)

    def test_transform_pos_arg_with_extra_args(self):
        alias_args = ['cp', 'test1', 'test2', '-o', 'tsv']
        expected_args = ['storage', 'blob', 'copy', 'start-batch', '--source-uri',
                         'test1', '--destination-container', 'test2', '-o', 'tsv']
        self.assertAlias(expected_args, alias_args)

    def test_transform_pos_arg_with_alias(self):
        # Placeholders are aliases in this case
        alias_args = ['cp', 'mn', 'diag']
        # Expected alias_manager not to transform mn and diag, even though they are alias,
        # because they are positional argument in this use case
        expected_args = ['storage', 'blob', 'copy', 'start-batch', '--source-uri',
                         'mn', '--destination-container', 'diag']
        self.assertAlias(expected_args, alias_args)

    def test_post_transform_env_var(self):
        os.environ['tag1'] = 'test-env-var-1'
        os.environ['tag2'] = 'test-env-var-2'
        alias_args = ['group', 'create', '-n', 'test', '--tags',
                      'tag1=$tag1',
                      'tag2=$tag2',
                      'tag3=$non-existing-env-var']
        expected_args = ['group', 'create', '-n', 'test', '--tags',
                         'tag1=test-env-var-1',
                         'tag2=test-env-var-2',
                         'tag3=$non-existing-env-var']
        self.assertPostTransform(expected_args, alias_args)

    def test_post_transform_remove_quotes(self):
        alias_args = ['vm', 'list', '-g', 'MyResourceGroup', '--query', '"[].id"', '-o', 'tsv']
        expected_args = ['vm', 'list', '-g', 'MyResourceGroup', '--query', '[].id', '-o', 'tsv']
        self.assertPostTransform(expected_args, alias_args)

        alias_args = ['vm', 'list', '-g', 'MyResourceGroup', '--query', '\'[].id\'', '-o', 'tsv']
        expected_args = ['vm', 'list', '-g', 'MyResourceGroup', '--query', '[].id', '-o', 'tsv']
        self.assertPostTransform(expected_args, alias_args)

    def test_recursive_alias(self):
        alias_manager = MockAliasManager(mock_alias_str=DEFAULT_MOCK_ALIAS_STRING,
                                         load_cmd_tbl_func=self.load_cmd_tbl_func)
        with self.assertRaises(CLIError):
            alias_manager.transform(['ac-ls'])

        with self.assertRaises(CLIError):
            alias_manager.transform(['dns'])

    def test_inconsistent_placeholder_index(self):
        alias_manager = MockAliasManager(mock_alias_str=DEFAULT_MOCK_ALIAS_STRING,
                                         load_cmd_tbl_func=self.load_cmd_tbl_func)
        # Raise error if there is not enough positional argument provided
        with self.assertRaises(CLIError):
            alias_manager.transform(['cp'])

        # Raise error if the placeholder indexing in the alias config file is inconsistent
        with self.assertRaises(CLIError):
            alias_manager.transform(['show-ext', 'test-ext'])

    ##########################
    #### Helper functions ####
    ##########################
    def assertAlias(self, expected_args, alias_args, mock_alias_str=DEFAULT_MOCK_ALIAS_STRING):
        alias_manager = MockAliasManager(mock_alias_str=mock_alias_str,
                                         load_cmd_tbl_func=self.load_cmd_tbl_func)
        self.assertEqual(expected_args, alias_manager.transform(alias_args))

    def assertPostTransform(self, expected_args, alias_args, mock_alias_str=DEFAULT_MOCK_ALIAS_STRING):
        alias_manager = MockAliasManager(mock_alias_str=mock_alias_str,
                                         load_cmd_tbl_func=self.load_cmd_tbl_func)
        self.assertEqual(expected_args, alias_manager.post_transform(alias_args))

    def load_cmd_tbl_func(self, _):
        return []

class MockAliasManager(alias.AliasManager):

    def __init__(self, **kwargs):
        super(MockAliasManager, self).__init__(**kwargs)

    def load_alias_table(self):
        with open(alias.GLOBAL_ALIAS_PATH, 'w+') as alias_config_file:
            alias_config_file.write(self.kwargs.get('mock_alias_str', ''))
        self.alias_table.read(alias.GLOBAL_ALIAS_PATH)

if __name__ == '__main__':
    unittest.main()

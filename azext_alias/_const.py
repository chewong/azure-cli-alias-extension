import os

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

COLLISION_WARNING = 'The following alias collided with a reserved command in the CLI: {}'
INCONSISTENT_INDEXING_ERROR = 'Inconsistent placeholder indexing in alias command'
RECURSIVE_ALIAS_ERROR = 'Potentially recursive alias: \'{}\' is associated by another alias'
PARSE_ERROR = 'Error parsing the configuration file'
IGNORE_CONFIG_MSG = 'Ignoring the alias configuration file...'